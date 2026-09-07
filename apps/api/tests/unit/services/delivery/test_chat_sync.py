"""The outbound message GAIA sent is written into the bot's own conversation.

Found live on 2026-09-07: the first real activation send was delivered but the
sync failed with "403: Not authenticated", because the user dict handed to the
session and conversation services carried the Mongo ``_id`` and no ``user_id``.
"""

from unittest.mock import AsyncMock, patch

import pytest

from app.models.user_models import UserDocument
from app.services.delivery import chat_sync

USER_ID = "6acc0dac0cc0a00000000001"
LINK = {"telegram": {"platform": "telegram", "platformUserId": "622", "username": None}}


@pytest.fixture
def seams():
    with (
        patch.object(
            chat_sync.PlatformLinkService, "get_linked_platforms", AsyncMock(return_value=LINK)
        ),
        patch.object(
            chat_sync.BotService, "get_or_create_session", AsyncMock(return_value="conv-1")
        ) as session,
        patch.object(chat_sync, "update_messages", AsyncMock()) as update,
    ):
        yield {"session": session, "update": update}


@pytest.mark.unit
class TestPersistBotMessage:
    async def test_the_session_and_the_write_are_made_as_the_authenticated_user(
        self, seams
    ) -> None:
        user = UserDocument.model_validate({"id": USER_ID, "email": "a@b.c", "timezone": "UTC"})

        await chat_sync.persist_bot_message(user, "telegram", ["Morning.", "Gmail?"])

        session_user = seams["session"].await_args.args[3]
        assert seams["session"].await_args.args[:3] == ("telegram", "622", None)
        assert session_user["user_id"] == USER_ID
        assert session_user["_id"] == USER_ID
        request, write_user = seams["update"].await_args.args
        assert request.conversation_id == "conv-1"
        assert request.messages[0].response == "Morning.\n\nGmail?"
        assert write_user["user_id"] == USER_ID

    async def test_a_platform_the_user_never_linked_writes_nothing(self, seams) -> None:
        user = UserDocument.model_validate({"id": USER_ID, "email": "a@b.c"})

        await chat_sync.persist_bot_message(user, "whatsapp", ["Morning."])

        seams["session"].assert_not_awaited()
        seams["update"].assert_not_awaited()

    async def test_nothing_to_say_writes_nothing(self, seams) -> None:
        await chat_sync.persist_bot_message(
            UserDocument.model_validate({"id": USER_ID}), "telegram", []
        )

        seams["session"].assert_not_awaited()

    async def test_a_failed_write_is_a_warning_with_the_cause_not_a_raise(self, seams) -> None:
        seams["update"].side_effect = RuntimeError("mongo gone")
        with patch.object(chat_sync, "log") as log:
            await chat_sync.persist_bot_message(
                UserDocument.model_validate({"id": USER_ID}), "telegram", ["hi"]
            )

        log.warning.assert_called_once_with(
            "delivery.chat_sync_failed", user_id=USER_ID, platform="telegram", error="mongo gone"
        )
