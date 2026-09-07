"""Writing GAIA's outbound back into the bot conversation it was sent to.

Platform delivery is fire-and-forget (RabbitMQ to bot), so the bot's own history
never contains what GAIA sent. Without this, a user replying "yeah do it" is
answering a message the next agent turn cannot see, and GAIA asks them what they
mean. This closes that loop for every proactive send.
"""

from datetime import UTC, datetime
from typing import cast

from app.models.chat_models import MessageModel, UpdateMessagesRequest
from app.models.user_models import AuthenticatedUser, UserDocument, user_to_legacy_dict
from app.services.bot_service import BotService
from app.services.conversation_service import update_messages
from app.services.platform_link_service import PlatformLinkService
from shared.py.wide_events import log


async def persist_bot_message(user: UserDocument, platform: str, parts: list[str]) -> None:
    """Append one assistant turn (``parts``, joined) to a platform's bot conversation.

    Best-effort: the message is already delivered by the time this runs, so a
    history-sync failure must not fail the caller's flow and make it re-send.
    It is logged rather than swallowed, so a silently context-free bot shows up
    in the wide events instead of only in a confused user's screenshot.
    """
    if not parts:
        return
    user_id = user.id
    linked = await PlatformLinkService.get_linked_platforms(user_id)
    entry = linked.get(platform)
    if not entry:
        return
    # The session and conversation services read ``user_id`` off the caller,
    # which a stored document does not carry; the bot path also wants ``_id``.
    actor = cast(AuthenticatedUser, {**user_to_legacy_dict(user), "user_id": user_id})
    try:
        # Resolved through bot_sessions every time, never cached: /new re-mints
        # the conversation id, and a stale one writes into a dead thread.
        conversation_id = await BotService.get_or_create_session(
            platform, str(entry["platformUserId"]), None, actor
        )
        await update_messages(
            UpdateMessagesRequest(
                conversation_id=conversation_id,
                messages=[
                    MessageModel(
                        type="bot",
                        response="\n\n".join(parts),
                        date=datetime.now(UTC).isoformat(),
                    )
                ],
            ),
            actor,
        )
    except Exception as e:
        log.warning("delivery.chat_sync_failed", user_id=user_id, platform=platform, error=str(e))
