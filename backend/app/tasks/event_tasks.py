"""
Event task handlers for different types of events.
"""

import asyncio
from datetime import datetime, timezone
from typing import List, Union
from uuid import uuid4

from app.config.loggers import general_logger as logger
from app.langchain.core.agent import call_workflow_agent
from app.langchain.llm.client import init_gemini_llm
from app.models.arq_event_models import EventModel
from app.models.chat_models import (
    MessageModel,
    SystemConversationPurpose,
    UpdateMessagesRequest,
)
from app.models.reminder_models import ReminderModel
from app.models.workflow_models import WorkflowModel
from app.services.conversation_service import (
    create_system_conversation,
    get_conversation,
    update_messages,
)
from app.services.notification_service import notification_service
from app.services.user_service import get_user_by_id
from app.services.workflow_service import update_workflow
from app.utils.notification.sources import AIProactiveNotificationSource
from app.utils.oauth_utils import get_tokens_by_user_id
from langchain_core.messages import AIMessage, HumanMessage

gemini_model = init_gemini_llm()


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


async def _create_conversation_for_workflow(
    workflow: WorkflowModel, notification_title: str, user_dict: dict
) -> str:
    """
    Create a new system conversation for a workflow and update the workflow with conversation_id.

    Args:
        workflow: The workflow
        notification_title: Title from the AI agent response to use as conversation title
        user_dict: User context dictionary

    Returns:
        The new conversation_id
    """
    if not workflow.id:
        raise ValueError("Workflow must have an ID")

    # Create system conversation for workflow processing
    conversation = await create_system_conversation(
        user_id=workflow.user_id,
        description=notification_title,
        system_purpose=SystemConversationPurpose.WORKFLOW_PROCESSING,
    )

    # Update the workflow with the new conversation_id
    await update_workflow(
        workflow_id=workflow.id,
        update_data={"conversation_id": conversation["conversation_id"]},
        user_id=workflow.user_id,
    )

    logger.info(
        f"Created system conversation {conversation['conversation_id']} for workflow {workflow.id}"
    )
    return conversation["conversation_id"]


async def _store_workflow_execution(
    conversation_id: str,
    instructions: str,
    ai_response: str,
    user_dict: dict,
    notification_request,
) -> None:
    """
    Log the workflow execution as messages in the conversation and create notification.

    Args:
        conversation_id: ID of the conversation to log to
        instructions: The original workflow instructions
        ai_response: The AI agent's response
        user_dict: User context dictionary
        notification_request: Prepared notification request object
    """
    user_message = MessageModel(
        type="user",
        response=f"Execute workflow: {instructions}",
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


async def _execute_workflow(workflow: WorkflowModel) -> None:
    """
    Execute an agentic workflow with conversation tracking and history context.

    This function:
    1. Retrieves authentication tokens
    2. Gets conversation history (last 10 messages) if conversation exists
    3. Calls AI agent with context-aware instructions
    4. Creates conversation on first execution
    5. Logs execution as conversation messages
    6. Creates notification

    Args:
        workflow: The agentic workflow to execute
    """
    if not workflow.id:
        raise ValueError("Workflow must have an ID")

    # Get authentication tokens
    access_token, refresh_token, success = await get_tokens_by_user_id(
        user_id=workflow.user_id
    )

    if not success:
        logger.error(
            f"Failed to get valid tokens for user {workflow.user_id} while executing workflow {workflow.id}"
        )
        raise ValueError(
            f"Failed to get valid tokens for user {workflow.user_id} while executing workflow {workflow.id}"
        )

    user_dict = await get_user_by_id(workflow.user_id)

    if not user_dict:
        raise ValueError(f"User with user_id {workflow.user_id} not found")

    # Get conversation history for context if conversation exists
    conversation_history = []
    if workflow.conversation_id:
        conversation_history = await _get_conversation_history(
            workflow.conversation_id, user_dict, limit=10
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
    notification_data = await call_workflow_agent(
        instruction=workflow.payload.instructions,
        user_id=workflow.user_id,
        workflow_id=workflow.id,
        access_token=access_token,
        refresh_token=refresh_token,
        old_messages=formatted_conversation_history,
    )

    if not notification_data:
        logger.error(
            f"AI agent reminder {workflow.id} returned no notification data for user {workflow.user_id}"
        )
        raise ValueError(
            f"AI agent reminder {workflow.id} returned no notification data"
        )

    # Create conversation if this is the first execution
    conversation_id = workflow.conversation_id
    if not conversation_id:
        conversation_id = await _create_conversation_for_workflow(
            workflow, notification_data.title, user_dict
        )

    # Prepare notification
    notification = await AIProactiveNotificationSource.create_reminder_notification(
        title=notification_data.title,
        body=notification_data.body,
        reminder_id=workflow.id,
        user_id=workflow.user_id,
        actions=[],
        send=True,  # Send notification immediately
    )

    # Log execution and send notification
    await _store_workflow_execution(
        conversation_id=conversation_id,
        instructions=workflow.payload.instructions,  # Use original instructions for logging
        ai_response=notification_data.message,
        user_dict=user_dict,
        notification_request=notification,
    )


async def _execute_reminder(reminder: ReminderModel) -> None:
    """
    Execute a reminder by sending a simple notification.

    Args:
        reminder: The reminder to execute
    """
    if not reminder.id:
        logger.error("Reminder has no ID, skipping execution")
        raise ValueError("Reminder has no ID, skipping execution")

    await AIProactiveNotificationSource.create_reminder_notification(
        title=reminder.payload.title,
        body=reminder.payload.body,
        reminder_id=reminder.id,
        user_id=reminder.user_id,
        actions=[],
        send=True,  # Send notification immediately
    )


async def execute_event(
    event: EventModel,
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
    logger.info(f"Executing event: {event.id}")

    if not event.id:
        logger.error(f"Reminder {event.id} has no ID, skipping execution.")
        raise ValueError(f"Reminder {event.id} has no ID, skipping execution.")

    try:
        if isinstance(event, WorkflowModel):
            await _execute_workflow(event)
        elif isinstance(event, ReminderModel):
            await _execute_reminder(event)
        else:
            raise ValueError(f"Unknown event type for {event.id}: {type(event)}")

        logger.info(f"Event {event.id} executed successfully")
    except Exception as e:
        logger.error(f"Failed to execute reminder {event.id}: {str(e)}")
        raise
