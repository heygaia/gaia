"""Picking the ONE chat platform a proactive message lands on."""

from app.constants.notifications import (
    CHANNEL_TYPE_DISCORD,
    CHANNEL_TYPE_SLACK,
    CHANNEL_TYPE_TELEGRAM,
    CHANNEL_TYPE_WHATSAPP,
    DEFAULT_CHAT_CHANNEL_PRIORITY,
)
from app.services.delivery.chat_channel import (
    pick_chat_channel,
    resolve_channel_priority,
)


class TestResolveChannelPriority:
    def test_unset_falls_back_to_the_default_order(self) -> None:
        assert resolve_channel_priority(None) == list(DEFAULT_CHAT_CHANNEL_PRIORITY)

    def test_a_stored_order_is_honoured(self) -> None:
        assert resolve_channel_priority([CHANNEL_TYPE_SLACK, CHANNEL_TYPE_TELEGRAM]) == [
            CHANNEL_TYPE_SLACK,
            CHANNEL_TYPE_TELEGRAM,
        ]

    def test_unknown_platforms_are_dropped(self) -> None:
        # A hand-edited or legacy document must never route a message to a
        # channel the outbound queues do not have.
        assert resolve_channel_priority(["carrier_pigeon", CHANNEL_TYPE_SLACK]) == [
            CHANNEL_TYPE_SLACK
        ]

    def test_an_all_unknown_list_falls_back_rather_than_silencing_the_user(self) -> None:
        assert resolve_channel_priority(["carrier_pigeon"]) == list(DEFAULT_CHAT_CHANNEL_PRIORITY)

    def test_a_non_list_falls_back(self) -> None:
        assert resolve_channel_priority("telegram") == list(  # type: ignore[arg-type] -- a legacy doc really can hold a bare string, and it must not crash a send
            DEFAULT_CHAT_CHANNEL_PRIORITY
        )


class TestPickChatChannel:
    def test_the_first_linked_and_enabled_platform_wins(self) -> None:
        picked = pick_chat_channel(
            [CHANNEL_TYPE_TELEGRAM, CHANNEL_TYPE_SLACK],
            {CHANNEL_TYPE_TELEGRAM: {}, CHANNEL_TYPE_SLACK: {}},
            {},
        )
        assert picked == CHANNEL_TYPE_TELEGRAM

    def test_priority_order_beats_link_order(self) -> None:
        picked = pick_chat_channel(
            [CHANNEL_TYPE_SLACK, CHANNEL_TYPE_TELEGRAM],
            {CHANNEL_TYPE_TELEGRAM: {}, CHANNEL_TYPE_SLACK: {}},
            {},
        )
        assert picked == CHANNEL_TYPE_SLACK

    def test_an_unlinked_first_choice_is_skipped(self) -> None:
        picked = pick_chat_channel(
            [CHANNEL_TYPE_TELEGRAM, CHANNEL_TYPE_SLACK], {CHANNEL_TYPE_SLACK: {}}, {}
        )
        assert picked == CHANNEL_TYPE_SLACK

    def test_a_disabled_first_choice_is_skipped(self) -> None:
        picked = pick_chat_channel(
            [CHANNEL_TYPE_TELEGRAM, CHANNEL_TYPE_SLACK],
            {CHANNEL_TYPE_TELEGRAM: {}, CHANNEL_TYPE_SLACK: {}},
            {CHANNEL_TYPE_TELEGRAM: False},
        )
        assert picked == CHANNEL_TYPE_SLACK

    def test_no_linked_platform_is_no_channel(self) -> None:
        # The activation sequence stops here; it never falls back to the web.
        assert pick_chat_channel(list(DEFAULT_CHAT_CHANNEL_PRIORITY), {}, {}) is None

    def test_every_linked_platform_disabled_is_no_channel(self) -> None:
        assert (
            pick_chat_channel(
                [CHANNEL_TYPE_WHATSAPP, CHANNEL_TYPE_DISCORD],
                {CHANNEL_TYPE_WHATSAPP: {}, CHANNEL_TYPE_DISCORD: {}},
                {CHANNEL_TYPE_WHATSAPP: False, CHANNEL_TYPE_DISCORD: False},
            )
            is None
        )

    def test_a_missing_preference_means_enabled(self) -> None:
        assert (
            pick_chat_channel([CHANNEL_TYPE_DISCORD], {CHANNEL_TYPE_DISCORD: {}}, {})
            == CHANNEL_TYPE_DISCORD
        )
