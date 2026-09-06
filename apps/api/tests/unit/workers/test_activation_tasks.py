"""The order a run does things in: stop, claim, write, deliver, record.

The seams substituted here are the ones that leave the process (Redis, Mongo,
the model, RabbitMQ). Everything the sequence actually decides — which stop
reason wins, whether the day is claimed, whether a failed publish leaves it
claimable, whether the next day is scheduled — runs for real.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from app.models.activation_models import ActivationDraft
from app.models.user_models import UserDocument
from app.services.activation.context import RunContext
from app.services.activation.copy import ActivationCopyError
from app.services.activation.policy import Direction, Facts, SkipReason
from app.services.outbound_delivery import OutboundResult
from app.workers.tasks import activation_tasks

USER_ID = "6acc0dac0cc0a00000000001"
NOW = datetime(2026, 5, 4, 6, 0, tzinfo=UTC)


def _facts(**overrides: object) -> Facts:
    base = {
        "opted_out": False,
        "days_sent": 1,
        "account_age_days": 2,
        "subscription_active": True,
        "has_channel": True,
        "user_messaged_last_24h": False,
        "replied_to_sequence_last_24h": False,
        "connected_integrations": 1,
        "handovers": 0,
    }
    base.update(overrides)
    return Facts(**base)  # type: ignore[arg-type] -- a dict of the dataclass's own fields


def _context(**overrides: object) -> RunContext:
    from app.models.activation_models import ActivationSequenceState

    return RunContext(
        facts=_facts(**overrides),
        state=ActivationSequenceState(),
        platform="telegram",
        who_block="Role: founder",
        integrations_block="Connected: Gmail",
        yesterday_block="Nothing.",
        already_sent_block="Nothing yet.",
    )


@pytest.fixture
def user() -> UserDocument:
    return UserDocument(_id=USER_ID, timezone="UTC", created_at=NOW - timedelta(days=2))


@pytest.fixture
def seams(user: UserDocument):
    """Every out-of-process seam, defaulted to the happy path."""
    with (
        patch.object(activation_tasks.user_repository, "get", AsyncMock(return_value=user)),
        patch.object(
            activation_tasks.user_repository, "record_activation_message", AsyncMock()
        ) as record,
        patch.object(activation_tasks.context, "gather", AsyncMock(return_value=_context())),
        patch.object(
            activation_tasks,
            "draft_message",
            AsyncMock(
                return_value=ActivationDraft(bubbles=["morning"], suggestion="connect gmail")
            ),
        ) as draft,
        patch.object(
            activation_tasks,
            "publish_outbound_message",
            AsyncMock(return_value=OutboundResult.PUBLISHED),
        ) as publish,
        patch.object(activation_tasks.chat_sync, "persist_bot_message", AsyncMock()) as sync,
        patch.object(activation_tasks, "enqueue_next_day", AsyncMock()) as enqueue,
        patch.object(activation_tasks, "capture_event") as capture,
        patch.object(activation_tasks, "_claim", AsyncMock(return_value=True)) as claim,
        patch.object(activation_tasks, "_release", AsyncMock()) as release,
    ):
        yield {
            "record": record,
            "draft": draft,
            "publish": publish,
            "sync": sync,
            "enqueue": enqueue,
            "capture": capture,
            "claim": claim,
            "release": release,
        }


class TestHappyPath:
    async def test_sends_persists_records_and_schedules_tomorrow(self, seams) -> None:
        result = await activation_tasks.send_activation_message({}, USER_ID, 1)

        assert "sent activation day 1" in result
        seams["publish"].assert_awaited_once()
        assert seams["publish"].await_args.args[2] == ["morning"]
        seams["sync"].assert_awaited_once()
        recorded = seams["record"].await_args.args[1]
        assert (recorded.day, recorded.platform, recorded.suggestion) == (
            1,
            "telegram",
            "connect gmail",
        )
        seams["enqueue"].assert_awaited_once()
        assert seams["enqueue"].await_args.args[1] == 2

    async def test_the_direction_reaches_both_the_prompt_and_the_event(self, seams) -> None:
        await activation_tasks.send_activation_message({}, USER_ID, 1)
        assert seams["draft"].await_args.kwargs["direction"] is Direction.HANDOVER
        assert seams["capture"].call_args.args[2]["direction"] is Direction.HANDOVER


class TestStopConditions:
    @pytest.mark.parametrize(
        ("override", "reason"),
        [
            ({"opted_out": True}, SkipReason.OPTED_OUT),
            ({"days_sent": 5}, SkipReason.SEQUENCE_COMPLETE),
            ({"account_age_days": 15}, SkipReason.ACCOUNT_TOO_OLD),
            ({"subscription_active": False}, SkipReason.NOT_SUBSCRIBED),
            ({"has_channel": False}, SkipReason.NO_CHANNEL),
            ({"user_messaged_last_24h": True}, SkipReason.USER_ACTIVE_TODAY),
        ],
    )
    async def test_every_stop_reason_skips_before_the_model_call(
        self, seams, override, reason
    ) -> None:
        activation_tasks.context.gather = AsyncMock(return_value=_context(**override))

        result = await activation_tasks.send_activation_message({}, USER_ID, 1)

        assert reason in result
        seams["draft"].assert_not_awaited()
        seams["publish"].assert_not_awaited()
        seams["claim"].assert_not_awaited()
        assert seams["capture"].call_args.args[2]["reason"] is reason

    async def test_being_active_today_does_not_burn_the_day(self, seams) -> None:
        # Terminal reasons end the sequence; this one is only about today, so
        # the SAME day is rescheduled rather than the next one.
        activation_tasks.context.gather = AsyncMock(
            return_value=_context(user_messaged_last_24h=True)
        )

        await activation_tasks.send_activation_message({}, USER_ID, 1)

        assert seams["enqueue"].await_args.args[1] == 1

    async def test_a_terminal_reason_schedules_nothing(self, seams) -> None:
        activation_tasks.context.gather = AsyncMock(return_value=_context(opted_out=True))
        await activation_tasks.send_activation_message({}, USER_ID, 1)
        seams["enqueue"].assert_not_awaited()

    async def test_an_unknown_user_is_a_skip_not_a_crash(self, seams) -> None:
        activation_tasks.user_repository.get = AsyncMock(return_value=None)
        assert "unknown_user" in await activation_tasks.send_activation_message({}, USER_ID, 1)


class TestClaim:
    async def test_a_lost_claim_sends_nothing(self, seams) -> None:
        seams["claim"].return_value = False

        result = await activation_tasks.send_activation_message({}, USER_ID, 1)

        assert "already_claimed" in result
        seams["draft"].assert_not_awaited()
        seams["publish"].assert_not_awaited()
        seams["record"].assert_not_awaited()

    async def test_the_claim_is_taken_before_the_model_is_paid_for(self, seams) -> None:
        await activation_tasks.send_activation_message({}, USER_ID, 1)
        assert seams["claim"].await_args.args == (USER_ID, 1)


class TestDeliveryFailure:
    async def test_a_broker_failure_releases_the_day_and_raises(self, seams) -> None:
        # ARQ retries on the raise, and the released claim is what lets the
        # retry actually send instead of no-opping.
        seams["publish"].return_value = OutboundResult.FAILED

        with pytest.raises(activation_tasks.ActivationDeliveryError):
            await activation_tasks.send_activation_message({}, USER_ID, 1)

        seams["release"].assert_awaited_once_with(USER_ID, 1)
        seams["record"].assert_not_awaited()

    async def test_an_unsupported_platform_skips_without_raising(self, seams) -> None:
        seams["publish"].return_value = OutboundResult.SKIPPED

        result = await activation_tasks.send_activation_message({}, USER_ID, 1)

        assert "publish_skipped" in result
        seams["release"].assert_awaited_once_with(USER_ID, 1)
        seams["record"].assert_not_awaited()

    async def test_nothing_is_recorded_before_the_message_lands(self, seams) -> None:
        seams["publish"].return_value = OutboundResult.FAILED
        with pytest.raises(activation_tasks.ActivationDeliveryError):
            await activation_tasks.send_activation_message({}, USER_ID, 1)
        seams["sync"].assert_not_awaited()


class TestCopyFailure:
    async def test_a_failed_draft_sends_nothing_and_moves_on(self, seams) -> None:
        # The one thing that must never happen is a generic message going out
        # because the specific one could not be written.
        seams["draft"].side_effect = ActivationCopyError("no unique draft")

        result = await activation_tasks.send_activation_message({}, USER_ID, 1)

        assert "copy_failed" in result
        seams["publish"].assert_not_awaited()
        seams["record"].assert_not_awaited()
        assert seams["enqueue"].await_args.args[1] == 2
