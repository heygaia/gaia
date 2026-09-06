"""Every stop rule and every direction, one fact at a time."""

from dataclasses import replace

import pytest

from app.services.activation.policy import (
    CLAIM_KEY_PREFIX,
    MAX_ACCOUNT_AGE_DAYS,
    SEQUENCE_LENGTH,
    Direction,
    Facts,
    SkipReason,
    claim_key,
    direction,
    skip_reason,
)

SENDABLE = Facts(
    opted_out=False,
    days_sent=0,
    account_age_days=1,
    subscription_active=True,
    has_channel=True,
    user_messaged_last_24h=False,
    replied_to_sequence_last_24h=False,
    connected_integrations=0,
    handovers=0,
)


class TestSkipReason:
    def test_a_fresh_paying_user_with_a_channel_is_sent_to(self) -> None:
        assert skip_reason(SENDABLE) is None

    @pytest.mark.parametrize(
        ("change", "reason"),
        [
            ({"opted_out": True}, SkipReason.OPTED_OUT),
            ({"days_sent": SEQUENCE_LENGTH}, SkipReason.SEQUENCE_COMPLETE),
            ({"days_sent": SEQUENCE_LENGTH + 3}, SkipReason.SEQUENCE_COMPLETE),
            ({"account_age_days": MAX_ACCOUNT_AGE_DAYS + 1}, SkipReason.ACCOUNT_TOO_OLD),
            ({"subscription_active": False}, SkipReason.NOT_SUBSCRIBED),
            ({"has_channel": False}, SkipReason.NO_CHANNEL),
            ({"user_messaged_last_24h": True}, SkipReason.USER_ACTIVE_TODAY),
        ],
    )
    def test_each_rule_stops_the_send_on_its_own(self, change: dict, reason: SkipReason) -> None:
        assert skip_reason(replace(SENDABLE, **change)) is reason

    def test_boundaries_send(self) -> None:
        assert skip_reason(replace(SENDABLE, days_sent=SEQUENCE_LENGTH - 1)) is None
        assert skip_reason(replace(SENDABLE, account_age_days=MAX_ACCOUNT_AGE_DAYS)) is None

    def test_a_reply_to_the_sequence_is_not_the_user_being_busy_elsewhere(self) -> None:
        """Answering yesterday's message is engagement with the sequence, so today
        continues it rather than standing down."""
        facts = replace(SENDABLE, user_messaged_last_24h=True, replied_to_sequence_last_24h=True)
        assert skip_reason(facts) is None

    def test_terminal_reasons_win_over_the_daily_one(self) -> None:
        facts = replace(SENDABLE, user_messaged_last_24h=True, days_sent=SEQUENCE_LENGTH)
        assert skip_reason(facts) is SkipReason.SEQUENCE_COMPLETE

    def test_the_rule_order_is_fixed(self) -> None:
        everything = Facts(
            opted_out=True,
            days_sent=SEQUENCE_LENGTH,
            account_age_days=MAX_ACCOUNT_AGE_DAYS + 1,
            subscription_active=False,
            has_channel=False,
            user_messaged_last_24h=True,
            replied_to_sequence_last_24h=False,
            connected_integrations=0,
            handovers=0,
        )
        assert skip_reason(everything) is SkipReason.OPTED_OUT
        assert skip_reason(replace(everything, opted_out=False)) is SkipReason.SEQUENCE_COMPLETE
        assert (
            skip_reason(replace(everything, opted_out=False, days_sent=0))
            is SkipReason.ACCOUNT_TOO_OLD
        )

    def test_the_constants(self) -> None:
        assert SEQUENCE_LENGTH == 5
        assert MAX_ACCOUNT_AGE_DAYS == 14


class TestDirection:
    def test_nothing_connected_points_at_a_connection(self) -> None:
        assert direction(SENDABLE) is Direction.CONNECT

    def test_connected_but_nothing_handed_over_points_at_a_job(self) -> None:
        assert direction(replace(SENDABLE, connected_integrations=1)) is Direction.HANDOVER

    def test_a_handover_gets_its_follow_through(self) -> None:
        assert (
            direction(replace(SENDABLE, connected_integrations=1, handovers=2))
            is Direction.FOLLOW_THROUGH
        )

    def test_a_handover_without_a_connection_still_follows_through(self) -> None:
        assert direction(replace(SENDABLE, handovers=1)) is Direction.FOLLOW_THROUGH

    def test_a_reply_yesterday_beats_everything(self) -> None:
        facts = replace(
            SENDABLE, replied_to_sequence_last_24h=True, connected_integrations=3, handovers=3
        )
        assert direction(facts) is Direction.CONTINUE_THREAD


class TestClaimKey:
    def test_is_scoped_to_user_and_day(self) -> None:
        assert claim_key("u1", 3) == f"{CLAIM_KEY_PREFIX}u1:3"
        assert claim_key("u1", 3) != claim_key("u1", 4)
        assert claim_key("u1", 3) != claim_key("u2", 3)
        assert CLAIM_KEY_PREFIX == "activation:sent:"
