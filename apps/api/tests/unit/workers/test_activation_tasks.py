"""The order a run does things in: stop, claim, write, deliver, record.

The seams substituted here are the ones that leave the process (Redis, Mongo,
the model, RabbitMQ). Everything the sequence actually decides — which stop
reason wins, whether the day is claimed, whether a failed publish leaves it
claimable, whether the next day is scheduled — runs for real.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from app.models.activation_models import ActivationDraft, ActivationMessage
from app.models.chat_models import ConversationSource
from app.models.user_models import UserDocument
from app.services.activation.context import RunContext
from app.services.activation.copy import ActivationCopyError
from app.services.activation.policy import (
    ActivationBrief,
    Direction,
    Facts,
    PromptBlocks,
    SkipReason,
)
from app.services.analytics_service import AnalyticsEvents
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


def _context(platform: str | None = "telegram", **overrides: object) -> RunContext:
    from app.models.activation_models import ActivationSequenceState

    return RunContext(
        facts=_facts(**overrides),
        state=ActivationSequenceState(),
        platform=platform,
        blocks=PromptBlocks(
            who="Role: founder",
            integrations="Connected: Gmail",
            yesterday="Nothing.",
            already_sent="Nothing yet.",
        ),
    )


class _Clock:
    """``datetime`` as the task sees it, pinned so every timestamp it passes on is NOW."""

    @staticmethod
    def now(tz: object = None) -> datetime:
        assert tz is UTC
        return NOW


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
                return_value=ActivationDraft(
                    bubbles=["morning"], suggestion="connect gmail", connect_target="gmail"
                )
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
        patch.object(activation_tasks, "datetime", _Clock),
        patch.object(activation_tasks, "log") as log,
    ):
        yield {
            "log": log,
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
        assert seams["draft"].await_args.args[0].direction is Direction.HANDOVER
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


class TestWhatTheTaskPassesOn:
    """Every argument the task hands to a seam, exactly: a dropped or swapped one
    sends the wrong day, to the wrong user, at the wrong time."""

    async def test_the_run_is_stamped_on_the_wide_event(self, seams) -> None:
        await activation_tasks.send_activation_message({}, USER_ID, 1)

        seams["log"].set.assert_any_call(user_id=USER_ID, user={"id": USER_ID}, activation_day=1)
        seams["log"].set.assert_any_call(direction=Direction.HANDOVER, platform="telegram")

    async def test_the_user_is_read_and_gathered_at_the_pinned_now(self, seams, user) -> None:
        await activation_tasks.send_activation_message({}, USER_ID, 1)

        activation_tasks.user_repository.get.assert_awaited_once_with(USER_ID)
        activation_tasks.context.gather.assert_awaited_once_with(user, NOW)

    async def test_tomorrow_is_scheduled_for_this_user_in_their_timezone_from_now(
        self, seams
    ) -> None:
        await activation_tasks.send_activation_message({}, USER_ID, 1)

        seams["enqueue"].assert_awaited_once_with(USER_ID, 2, "UTC", NOW)

    async def test_an_active_day_reschedules_the_same_day_with_the_same_arguments(
        self, seams
    ) -> None:
        activation_tasks.context.gather = AsyncMock(
            return_value=_context(user_messaged_last_24h=True)
        )

        await activation_tasks.send_activation_message({}, USER_ID, 1)

        seams["enqueue"].assert_awaited_once_with(USER_ID, 1, "UTC", NOW)

    async def test_the_sent_event_carries_day_platform_and_direction(self, seams) -> None:
        await activation_tasks.send_activation_message({}, USER_ID, 1)

        seams["capture"].assert_called_once_with(
            USER_ID,
            AnalyticsEvents.ACTIVATION_DAY_SENT,
            {"day": 1, "platform": "telegram", "direction": Direction.HANDOVER},
        )

    async def test_an_unknown_user_is_skipped_under_their_own_id_and_day(self, seams) -> None:
        activation_tasks.user_repository.get = AsyncMock(return_value=None)

        result = await activation_tasks.send_activation_message({}, USER_ID, 3)

        assert result == f"skip {USER_ID} day 3: unknown_user"
        seams["capture"].assert_called_once_with(
            USER_ID, AnalyticsEvents.ACTIVATION_DAY_SKIPPED, {"day": 3, "reason": "unknown_user"}
        )

    async def test_a_stop_reason_is_skipped_under_the_users_id_and_day(self, seams) -> None:
        activation_tasks.context.gather = AsyncMock(return_value=_context(opted_out=True))

        result = await activation_tasks.send_activation_message({}, USER_ID, 2)

        assert result == f"skip {USER_ID} day 2: {SkipReason.OPTED_OUT}"
        seams["capture"].assert_called_once_with(
            USER_ID,
            AnalyticsEvents.ACTIVATION_DAY_SKIPPED,
            {"day": 2, "reason": SkipReason.OPTED_OUT},
        )

    async def test_a_platform_gaia_cannot_message_is_a_named_skip(self, seams) -> None:
        activation_tasks.context.gather = AsyncMock(return_value=_context(platform="pager"))

        result = await activation_tasks.send_activation_message({}, USER_ID, 1)

        assert result == f"skip {USER_ID} day 1: unsupported_platform"
        seams["capture"].assert_called_once_with(
            USER_ID,
            AnalyticsEvents.ACTIVATION_DAY_SKIPPED,
            {"day": 1, "reason": "unsupported_platform"},
        )
        seams["claim"].assert_not_awaited()


class TestSkip:
    def test_the_reason_lands_on_the_event_the_analytics_and_the_return(self) -> None:
        with (
            patch.object(activation_tasks, "log") as log,
            patch.object(activation_tasks, "capture_event") as capture,
        ):
            result = activation_tasks._skip("u1", 4, "copy_failed")

        assert result == "skip u1 day 4: copy_failed"
        log.set.assert_called_once_with(skipped="copy_failed")
        capture.assert_called_once_with(
            "u1", AnalyticsEvents.ACTIVATION_DAY_SKIPPED, {"day": 4, "reason": "copy_failed"}
        )


class TestWhatTheTaskPassesOnAfterTheClaim:
    async def test_the_brief_is_todays_day_direction_and_gathered_blocks(self, seams) -> None:
        await activation_tasks.send_activation_message({}, USER_ID, 1)

        assert seams["draft"].await_args.args == (
            ActivationBrief(day=1, direction=Direction.HANDOVER, blocks=_context().blocks),
        )
        assert seams["draft"].await_args.kwargs == {"earlier": [], "user_id": USER_ID}

    async def test_a_lost_claim_is_skipped_under_the_users_id_and_day(self, seams) -> None:
        seams["claim"].return_value = False

        result = await activation_tasks.send_activation_message({}, USER_ID, 4)

        assert result == f"skip {USER_ID} day 4: already_claimed"
        seams["capture"].assert_called_once_with(
            USER_ID, AnalyticsEvents.ACTIVATION_DAY_SKIPPED, {"day": 4, "reason": "already_claimed"}
        )

    async def test_a_failed_draft_is_recorded_skipped_and_tomorrow_still_scheduled(
        self, seams
    ) -> None:
        seams["draft"].side_effect = ActivationCopyError("no unique draft")

        result = await activation_tasks.send_activation_message({}, USER_ID, 1)

        assert result == f"skip {USER_ID} day 1: copy_failed"
        seams["log"].set.assert_any_call(copy_error="no unique draft")
        seams["capture"].assert_called_once_with(
            USER_ID, AnalyticsEvents.ACTIVATION_DAY_SKIPPED, {"day": 1, "reason": "copy_failed"}
        )
        seams["enqueue"].assert_awaited_once_with(USER_ID, 2, "UTC", NOW)

    async def test_the_message_is_published_to_this_user_on_their_platform(self, seams) -> None:
        await activation_tasks.send_activation_message({}, USER_ID, 1)

        seams["publish"].assert_awaited_once_with(ConversationSource.TELEGRAM, USER_ID, ["morning"])

    async def test_a_broker_failure_names_the_user_and_platform(self, seams) -> None:
        seams["publish"].return_value = OutboundResult.FAILED

        with pytest.raises(
            activation_tasks.ActivationDeliveryError,
            match=f"^activation publish failed for {USER_ID} on telegram$",
        ):
            await activation_tasks.send_activation_message({}, USER_ID, 1)

    async def test_a_skipped_publish_is_skipped_under_the_users_id_and_day(self, seams) -> None:
        seams["publish"].return_value = OutboundResult.SKIPPED

        result = await activation_tasks.send_activation_message({}, USER_ID, 2)

        assert result == f"skip {USER_ID} day 2: publish_skipped"
        seams["capture"].assert_called_once_with(
            USER_ID, AnalyticsEvents.ACTIVATION_DAY_SKIPPED, {"day": 2, "reason": "publish_skipped"}
        )

    async def test_the_recorded_message_is_the_whole_delivered_day(self, seams, user) -> None:
        await activation_tasks.send_activation_message({}, USER_ID, 1)

        seams["record"].assert_awaited_once_with(
            USER_ID,
            ActivationMessage(
                day=1,
                direction=Direction.HANDOVER,
                platform="telegram",
                sent_at=NOW,
                bubbles=["morning"],
                suggestion="connect gmail",
                connect_target="gmail",
            ),
        )
        seams["sync"].assert_awaited_once_with(user, "telegram", ["morning"])
        seams["log"].set.assert_any_call(bubbles=1)
