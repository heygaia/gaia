"""Unit tests for app.workers.tasks.signup_email_tasks.

The two ESP round-trips a signup owes the new user, moved onto the worker queue
so a restart mid-send cannot drop them. Both failure paths are swallowed so
neither delivery can fail the other, which makes the wide event the only place a
lost email is visible — a blank or misattributed entry there is a signup
silently missing its welcome email.
"""

import asyncio
from unittest.mock import AsyncMock, patch

from bson import ObjectId
import pytest

from app.constants.log_tags import LogTag
from app.workers.tasks.signup_email_tasks import deliver_signup_emails
from tests.helpers import captured_wide_event

MODULE = "app.workers.tasks.signup_email_tasks"


@pytest.fixture
def mock_send_welcome_email():
    with patch(f"{MODULE}.send_welcome_email", new_callable=AsyncMock) as mock_fn:
        yield mock_fn


@pytest.fixture
def mock_add_marketing_contact():
    with patch(f"{MODULE}.add_marketing_contact", new_callable=AsyncMock) as mock_fn:
        yield mock_fn


@pytest.fixture
def hung_esp_call():
    """An ESP stub that accepts the call and never answers."""

    async def _hang(*_args: str, **_kwargs: str) -> None:
        await asyncio.Event().wait()

    return _hang


class TestDeliverSignupEmails:
    async def test_both_deliveries_go_out_for_the_new_user(
        self, mock_send_welcome_email, mock_add_marketing_contact
    ):
        user_id = str(ObjectId())

        result = await deliver_signup_emails({}, user_id, "bob@test.com", "Bob")

        mock_send_welcome_email.assert_awaited_once_with("bob@test.com", "Bob", user_id=user_id)
        mock_add_marketing_contact.assert_awaited_once_with("bob@test.com", "Bob", user_id=user_id)
        assert user_id in result

    async def test_the_two_esp_calls_run_concurrently(
        self, mock_send_welcome_email, mock_add_marketing_contact
    ):
        """Both round-trips are in flight at once — neither waits on the other."""
        # A two-party barrier only opens if both calls are running at the same
        # time; awaited one after the other, the first waits for a partner that
        # has not started and the rendezvous times out.
        barrier = asyncio.Barrier(2)
        rendezvous: set[str] = set()

        async def _welcome(*_args: str, **_kwargs: str) -> None:
            await asyncio.wait_for(barrier.wait(), timeout=1)
            rendezvous.add("welcome_email")

        async def _contact(*_args: str, **_kwargs: str) -> None:
            await asyncio.wait_for(barrier.wait(), timeout=1)
            rendezvous.add("marketing_contact")

        mock_send_welcome_email.side_effect = _welcome
        mock_add_marketing_contact.side_effect = _contact

        await deliver_signup_emails({}, str(ObjectId()), "bob@test.com", "Bob")

        assert rendezvous == {"welcome_email", "marketing_contact"}

    async def test_a_hung_welcome_email_is_abandoned_after_the_timeout(
        self, mock_send_welcome_email, mock_add_marketing_contact, hung_esp_call
    ):
        """An ESP that accepts the call and never answers is the failure the
        bound exists for. Unbounded, the job waits on it for the worker's whole
        30-minute timeout and the lost email is recorded nowhere at all."""
        user_id = str(ObjectId())
        mock_send_welcome_email.side_effect = hung_esp_call

        with patch(f"{MODULE}.SIGNUP_EMAIL_TIMEOUT_SECONDS", 0.01):
            async with captured_wide_event() as event:
                # Two orders of magnitude above the bound: the job returns here
                # only because the timeout abandoned the call, so an unbounded
                # wait fails this line instead of hanging the suite.
                async with asyncio.timeout(2):
                    await deliver_signup_emails({}, user_id, "bob@test.com", "Bob")

        assert event["errors"] == [
            {
                "msg": f"{LogTag.OAUTH} Failed to send welcome email to",
                "user": {"id": user_id},
                "error": "",
                "error_type": "TimeoutError",
            }
        ]
        mock_add_marketing_contact.assert_awaited_once_with("bob@test.com", "Bob", user_id=user_id)

    async def test_a_hung_marketing_contact_is_abandoned_after_the_timeout(
        self, mock_send_welcome_email, mock_add_marketing_contact, hung_esp_call
    ):
        """The audience call carries its own bound — sharing the welcome email's
        would leave one of the two round-trips able to hang forever."""
        user_id = str(ObjectId())
        mock_add_marketing_contact.side_effect = hung_esp_call

        with patch(f"{MODULE}.SIGNUP_EMAIL_TIMEOUT_SECONDS", 0.01):
            async with captured_wide_event() as event:
                async with asyncio.timeout(2):
                    await deliver_signup_emails({}, user_id, "bob@test.com", "Bob")

        assert event["errors"] == [
            {
                "msg": f"{LogTag.OAUTH} Failed to add marketing contact for",
                "user": {"id": user_id},
                "error": "",
                "error_type": "TimeoutError",
            }
        ]
        mock_send_welcome_email.assert_awaited_once_with("bob@test.com", "Bob", user_id=user_id)

    async def test_a_welcome_email_failure_is_recorded_and_the_contact_still_runs(
        self, mock_send_welcome_email, mock_add_marketing_contact
    ):
        user_id = str(ObjectId())
        mock_send_welcome_email.side_effect = RuntimeError("SMTP error")

        async with captured_wide_event() as event:
            await deliver_signup_emails({}, user_id, "bob@test.com", "Bob")

        assert event["errors"] == [
            {
                "msg": f"{LogTag.OAUTH} Failed to send welcome email to",
                "user": {"id": user_id},
                "error": "SMTP error",
                "error_type": "RuntimeError",
            }
        ]
        mock_add_marketing_contact.assert_awaited_once_with("bob@test.com", "Bob", user_id=user_id)

    async def test_a_marketing_contact_failure_is_recorded_on_its_own(
        self, mock_send_welcome_email, mock_add_marketing_contact
    ):
        user_id = str(ObjectId())
        mock_add_marketing_contact.side_effect = RuntimeError("Resend API error")

        async with captured_wide_event() as event:
            await deliver_signup_emails({}, user_id, "bob@test.com", "Bob")

        assert event["errors"] == [
            {
                "msg": f"{LogTag.OAUTH} Failed to add marketing contact for",
                "user": {"id": user_id},
                "error": "Resend API error",
                "error_type": "RuntimeError",
            }
        ]
        mock_send_welcome_email.assert_awaited_once_with("bob@test.com", "Bob", user_id=user_id)

    async def test_a_cancelled_delivery_does_not_strand_the_other_one(
        self, mock_send_welcome_email, mock_add_marketing_contact
    ):
        """Cancellation is the one failure a delivery's own ``except Exception``
        cannot catch, so it reaches the gather. Propagated, it ends the job on
        the spot and the second round-trip is dropped mid-flight; collected,
        both still finish and the job is not recorded as a casualty."""
        delivered: list[str] = []

        async def _cancelled(*_args: str, **_kwargs: str) -> None:
            raise asyncio.CancelledError

        async def _slow_contact(*_args: str, **_kwargs: str) -> None:
            await asyncio.sleep(0)
            await asyncio.sleep(0)
            delivered.append("marketing_contact")

        mock_send_welcome_email.side_effect = _cancelled
        mock_add_marketing_contact.side_effect = _slow_contact

        await deliver_signup_emails({}, str(ObjectId()), "bob@test.com", "Bob")

        assert delivered == ["marketing_contact"]
