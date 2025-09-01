from typing import Annotated

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.config import get_stream_writer

from app.config.loggers import chat_logger as logger
from app.decorators import with_doc, with_rate_limiting
from app.docstrings.langchain.tools.notification_tool_docs import (
    EXECUTE_NOTIFICATION_ACTION,
    GET_UNREAD_NOTIFICATIONS,
    MARK_NOTIFICATION_READ,
)
from app.models.notification.notification_models import (
    NotificationStatus,
)
from app.services.notification_service import notification_service


def get_user_id_from_config(config: RunnableConfig) -> str:
    """Extract user ID from the config."""
    if not config:
        logger.error("Notification tool called without config")
        return ""

    metadata = config.get("metadata", {})
    user_id = metadata.get("user_id", "")

    if not user_id:
        logger.error("No user_id found in config metadata")
        return ""

    return user_id


@tool
@with_rate_limiting("get_unread_notifications")
@with_doc(GET_UNREAD_NOTIFICATIONS)
async def get_unread_notifications_tool(
    config: RunnableConfig,
    limit: Annotated[
        int,
        "Maximum number of unread notifications to return. Default is 20, maximum is 50.",
    ] = 20,
    offset: Annotated[
        int,
        "Number of notifications to skip for pagination. Default is 0.",
    ] = 0,
) -> str:
    """Get user's unread notifications."""
    try:
        user_id = get_user_id_from_config(config)
        writer = get_stream_writer()

        # Validate limit
        if limit > 50:
            limit = 50
        elif limit < 1:
            limit = 20

        writer({"progress": "Fetching unread notifications..."})

        # Get unread notifications from service (status = pending, delivered)
        notifications = await notification_service.get_user_notifications(
            user_id=user_id,
            status=NotificationStatus.PENDING,  # Only unread notifications
            limit=limit,
            offset=offset,
        )

        # Also get delivered notifications (which are unread)
        delivered_notifications = await notification_service.get_user_notifications(
            user_id=user_id,
            status=NotificationStatus.DELIVERED,
            limit=limit,
            offset=offset,
        )

        # Combine notifications and limit results
        all_notifications = notifications + delivered_notifications
        notifications = all_notifications[:limit]

        if not notifications:
            return "No unread notifications found."

        logger.info(
            f"Retrieved {len(notifications)} unread notifications for user {user_id}"
        )
        return f"Found {len(notifications)} unread notifications. Displaying in notification panel."

    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        return f"Failed to retrieve notifications: {str(e)}"


@tool
@with_rate_limiting("mark_notification_read")
@with_doc(MARK_NOTIFICATION_READ)
async def mark_notification_read_tool(
    config: RunnableConfig,
    notification_id: Annotated[
        str,
        "The unique identifier of the notification to mark as read.",
    ],
) -> str:
    """Mark a specific notification as read."""
    try:
        user_id = get_user_id_from_config(config)
        writer = get_stream_writer()

        writer({"progress": "Marking notification as read..."})

        # Mark notification as read
        updated_notification = await notification_service.mark_as_read(
            notification_id=notification_id, user_id=user_id
        )

        if not updated_notification:
            return f"Notification {notification_id} not found or could not be marked as read."

        logger.info(f"Marked notification {notification_id} as read for user {user_id}")
        return "Notification marked as read successfully."

    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        return f"Failed to mark notification as read: {str(e)}"


@tool
@with_rate_limiting("execute_notification_action")
@with_doc(EXECUTE_NOTIFICATION_ACTION)
async def execute_notification_action_tool(
    config: RunnableConfig,
    notification_id: Annotated[
        str,
        "The unique identifier of the notification containing the action.",
    ],
    action_id: Annotated[
        str,
        "The unique identifier of the action to execute.",
    ],
) -> str:
    """Execute a specific action from a notification."""
    try:
        user_id = get_user_id_from_config(config)
        writer = get_stream_writer()

        writer({"progress": "Executing notification action..."})

        # Execute the action
        result = await notification_service.execute_action(
            notification_id=notification_id,
            action_id=action_id,
            user_id=user_id,
            request=None,  # Will be populated in actual implementation
        )

        if not result.success:
            return f"Failed to execute action: {result.message or 'Unknown error'}"

        logger.info(
            f"Executed action {action_id} for notification {notification_id} for user {user_id}"
        )
        return f"Action executed successfully: {result.message or 'Action completed'}"

    except Exception as e:
        logger.error(f"Error executing notification action: {e}")
        return f"Failed to execute action: {str(e)}"


tools = [
    get_unread_notifications_tool,
    mark_notification_read_tool,
    execute_notification_action_tool,
]
