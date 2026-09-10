"""``WorkflowsRepository.claim_limit_notice`` — the limit-notice dedup gate.

The gate exists because one production thread ended on six identical daily-limit
notifications. It fails open on purpose: a user who hits a budget wall must be
told, even if Redis cannot answer. What it must never do is fail open *quietly* —
that turns a Redis degradation into the original incident with nothing in the
logs to connect the two.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.db.repositories.workflows import workflow_repository

pytestmark = pytest.mark.unit

MODULE = "app.db.repositories.workflows"


def _redis(set_result: object = None, set_error: Exception | None = None) -> MagicMock:
    client = MagicMock()
    client.set = AsyncMock(return_value=set_result, side_effect=set_error)
    return client


async def test_the_first_notice_in_the_window_is_claimed() -> None:
    client = _redis(set_result=True)
    with patch(f"{MODULE}.redis_cache") as cache:
        cache.redis = client
        assert await workflow_repository.claim_limit_notice("u1", "wf1") is True


async def test_a_second_notice_in_the_same_window_is_refused() -> None:
    """SET NX returns None when the key is already there — that is the dedup."""
    client = _redis(set_result=None)
    with patch(f"{MODULE}.redis_cache") as cache:
        cache.redis = client
        assert await workflow_repository.claim_limit_notice("u1", "wf1") is False


async def test_a_redis_failure_sends_the_notice_and_says_so() -> None:
    """Failing open is correct; failing open silently is the bug.

    The log line is the only thing that will tell the next person why six
    identical notices went out, so the fields it carries are asserted exactly:
    without ``workflow_id``/``user_id`` the event cannot be joined to the
    notifications the user actually received.
    """
    client = _redis(set_error=ConnectionError("redis down"))
    with (
        patch(f"{MODULE}.redis_cache") as cache,
        patch(f"{MODULE}.log") as mock_log,
    ):
        cache.redis = client
        assert await workflow_repository.claim_limit_notice("u1", "wf1") is True

    mock_log.warning.assert_called_once_with(
        "Limit-notice dedup unavailable, sending the notice anyway",
        workflow_id="wf1",
        user_id="u1",
        error="redis down",
        error_type="ConnectionError",
    )


async def test_no_redis_at_all_sends_the_notice_without_a_warning() -> None:
    """Redis not being wired up is a configuration state, not a degradation.

    Logging here would fire on every notice in any deployment without Redis and
    drown the line above, which is the one that matters.
    """
    with (
        patch(f"{MODULE}.redis_cache") as cache,
        patch(f"{MODULE}.log") as mock_log,
    ):
        cache.redis = None
        assert await workflow_repository.claim_limit_notice("u1", "wf1") is True

    mock_log.warning.assert_not_called()
