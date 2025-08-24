"""
Reminder task handlers for different types of reminders.
"""

import asyncio
from datetime import datetime, timezone
from typing import List, Union
from uuid import uuid4

from app.config.loggers import general_logger as logger
from app.langchain.core.agent import call_reminder_agent
from app.models.chat_models import (
    MessageModel,
    SystemPurpose,
    UpdateMessagesRequest,
)
from app.models.reminder_models import (
    AgentType,
    AIAgentReminderPayload,
    ReminderModel,
    StaticReminderPayload,
)
from app.services.conversation_service import (
    create_system_conversation,
    get_conversation,
    update_messages,
)
from app.services.notification_service import notification_service
from app.services.reminder_service import reminder_scheduler
from app.utils.notification.sources import AIProactiveNotificationSource
from app.utils.oauth_utils import get_tokens_by_user_id
from langchain_core.messages import AIMessage, HumanMessage


async def _get_conversation_history(
    conversation_id: str, user_dict: dict, limit: int = 10
) -> List[MessageModel]:
    """
    Retrieve the last N messages from a conversation for context.

    Args:
        conversation_id: The conversation to retrieve messages from
        user_dict: User context dictionary
        limit: Number of recent messages to retrieve (default: 10)

    Returns:
        List of MessageModel objects, empty list if conversation not found
    """
    try:
        conversation = await get_conversation(conversation_id, user_dict)
        messages = conversation.get("messages", [])

        # Get the last 'limit' messages
        recent_messages = messages[-limit:] if len(messages) > limit else messages

        # Convert to MessageModel objects
        return [MessageModel(**msg) for msg in recent_messages]
    except Exception as e:
        logger.warning(
            f"Could not retrieve conversation history for {conversation_id}: {e}"
        )
        return []


async def _create_conversation_for_reminder(
    reminder: ReminderModel, notification_title: str, user_dict: dict
) -> str:
    """
    Create a new system conversation for a reminder and update the reminder with conversation_id.

    Args:
        reminder: The reminder model
        notification_title: Title from the AI agent response to use as conversation title
        user_dict: User context dictionary

    Returns:
        The new conversation_id
    """
    if not reminder.id:
        raise ValueError("Reminder must have an ID")

    # Create system conversation for reminder processing
    conversation = await create_system_conversation(
        user_id=reminder.user_id,
        description=notification_title,
        system_purpose=SystemPurpose.REMINDER_PROCESSING,
    )

    # Update the reminder with the new conversation_id
    await reminder_scheduler.update_reminder(
        reminder_id=reminder.id,
        update_data={"conversation_id": conversation["conversation_id"]},
        user_id=reminder.user_id,
    )

    logger.info(
        f"Created system conversation {conversation['conversation_id']} for reminder {reminder.id}"
    )
    return conversation["conversation_id"]


async def _log_reminder_execution(
    conversation_id: str,
    instructions: str,
    ai_response: str,
    user_dict: dict,
    notification_request,
) -> None:
    """
    Log the reminder execution as messages in the conversation and create notification.

    Args:
        conversation_id: ID of the conversation to log to
        instructions: The original reminder instructions
        ai_response: The AI agent's response
        user_dict: User context dictionary
        notification_request: Prepared notification request object
    """
    user_message = MessageModel(
        type="user",
        response=f"Execute reminder: {instructions}",
        date=datetime.now(timezone.utc).isoformat(),
        message_id=str(uuid4()),
    )

    bot_message = MessageModel(
        type="bot",
        response=ai_response,
        date=datetime.now(timezone.utc).isoformat(),
        message_id=str(uuid4()),
    )

    messages_request = UpdateMessagesRequest(
        conversation_id=conversation_id, messages=[user_message, bot_message]
    )

    await asyncio.gather(
        update_messages(messages_request, user_dict),
        notification_service.create_notification(notification_request),
    )


async def _execute_ai_agent_reminder(reminder: ReminderModel) -> None:
    """
    Execute an AI agent reminder with conversation tracking and history context.

    This function:
    1. Retrieves authentication tokens
    2. Gets conversation history (last 10 messages) if conversation exists
    3. Calls AI agent with context-aware instructions
    4. Creates conversation on first execution
    5. Logs execution as conversation messages
    6. Creates notification

    Args:
        reminder: The AI agent reminder to execute
    """
    if not isinstance(reminder.payload, AIAgentReminderPayload):
        raise ValueError("Invalid payload type for AI agent reminder")

    if not reminder.id:
        raise ValueError("Reminder must have an ID")

    # Get authentication tokens
    access_token, refresh_token, success = await get_tokens_by_user_id(
        user_id=reminder.user_id
    )

    if not success:
        logger.error(
            f"Failed to get valid tokens for user {reminder.user_id} while executing reminder {reminder.id}"
        )
        raise ValueError(
            f"Failed to get valid tokens for user {reminder.user_id} while executing reminder {reminder.id}"
        )

    user_dict = {"user_id": reminder.user_id}

    # Get conversation history for context if conversation exists
    conversation_history = []
    if reminder.conversation_id:
        conversation_history = await _get_conversation_history(
            reminder.conversation_id, user_dict, limit=10
        )

    # Convert message history to LangChain message format
    formatted_conversation_history: List[Union[HumanMessage, AIMessage]] = []
    for msg in conversation_history:
        if msg.type == "user":
            user_message = HumanMessage(content=msg.response)
            formatted_conversation_history.append(user_message)
        elif msg.type == "bot":
            ai_message = AIMessage(content=msg.response)
            formatted_conversation_history.append(ai_message)

    # Call AI agent with enhanced instructions
    notification_data = await call_reminder_agent(
        instruction=reminder.payload.instructions,
        user_id=reminder.user_id,
        reminder_id=reminder.id,
        access_token=access_token,
        refresh_token=refresh_token,
        old_messages=formatted_conversation_history,
    )

    if not notification_data:
        logger.error(
            f"AI agent reminder {reminder.id} returned no notification data for user {reminder.user_id}"
        )
        raise ValueError(
            f"AI agent reminder {reminder.id} returned no notification data"
        )

    # Create conversation if this is the first execution
    conversation_id = reminder.conversation_id
    if not conversation_id:
        conversation_id = await _create_conversation_for_reminder(
            reminder, notification_data.title, user_dict
        )

    # Prepare notification
    notification = AIProactiveNotificationSource.create_reminder_notification(
        title=notification_data.title,
        body=notification_data.body,
        reminder_id=reminder.id,
        user_id=reminder.user_id,
        actions=[],
    )

    # Log execution and send notification
    await _log_reminder_execution(
        conversation_id=conversation_id,
        instructions=reminder.payload.instructions,  # Use original instructions for logging
        ai_response=notification_data.message,
        user_dict=user_dict,
        notification_request=notification,
    )


async def _execute_static_reminder(reminder: ReminderModel) -> None:
    """
    Execute a static reminder by sending a simple notification.

    Args:
        reminder: The static reminder to execute
    """
    if not isinstance(reminder.payload, StaticReminderPayload):
        raise ValueError("Invalid payload type for static reminder")

    if not reminder.id:
        raise ValueError("Reminder must have an ID")

    notification = AIProactiveNotificationSource.create_reminder_notification(
        title=reminder.payload.title,
        body=reminder.payload.body,
        reminder_id=reminder.id,
        user_id=reminder.user_id,
        actions=[],
    )

    await notification_service.create_notification(notification)

    logger.info(
        f"Static reminder {reminder.id} sent notification to user {reminder.user_id}"
    )


async def execute_reminder_by_agent(
    reminder: ReminderModel,
):
    """
    Execute a reminder task based on its type.

    This is the main entry point for reminder execution. It routes to the appropriate
    handler based on the reminder's agent type:
    - AI_AGENT: Executes with conversation tracking and history context
    - STATIC: Sends simple notification

    Args:
        reminder: The reminder to execute
        access_token: OAuth access token (for compatibility, retrieved automatically)
        refresh_token: OAuth refresh token (for compatibility, retrieved automatically)
    """
    logger.info(f"Executing reminder: {reminder.id} for agent: {reminder.agent}")

    if not reminder.id:
        logger.error(f"Reminder {reminder.id} has no ID, skipping execution.")
        raise ValueError(f"Reminder {reminder.id} has no ID, skipping execution.")

    try:
        if reminder.agent == AgentType.AI_AGENT:
            await _execute_ai_agent_reminder(reminder)
        elif reminder.agent == AgentType.STATIC:
            await _execute_static_reminder(reminder)
        else:
            raise ValueError(f"Unknown agent type: {reminder.agent}")

        logger.info(
            f"Reminder {reminder.id} executed successfully for agent: {reminder.agent}"
        )
    except Exception as e:
        logger.error(f"Failed to execute reminder {reminder.id}: {str(e)}")
        raise
