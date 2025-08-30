"""
Workflow conversation service for managing single conversations per workflow.
"""

from datetime import datetime, timezone
from typing import List

from app.db.mongodb.collections import conversations_collection
from app.models.chat_models import MessageModel, SystemPurpose, UpdateMessagesRequest
from app.services.conversation_service import (
    create_system_conversation,
    update_messages,
)
from app.config.loggers import general_logger as logger


async def get_or_create_workflow_conversation(
    workflow_id: str, user_id: str, workflow_title: str
) -> dict:
    """
    Get existing workflow conversation or create a new one.
    Uses workflow_id in metadata to identify the conversation.

    Args:
        workflow_id: The workflow ID
        user_id: The user ID
        workflow_title: Title of the workflow for conversation description

    Returns:
        dict: Existing or newly created workflow conversation
    """
    # Try to find existing workflow conversation
    existing_conversation = await conversations_collection.find_one(
        {
            "user_id": user_id,
            "is_system_generated": True,
            "system_purpose": SystemPurpose.WORKFLOW_EXECUTION,
            "metadata.workflow_id": workflow_id,
        }
    )

    if existing_conversation:
        existing_conversation["_id"] = str(existing_conversation["_id"])
        logger.info(
            f"Found existing workflow conversation {existing_conversation['conversation_id']} for workflow {workflow_id}"
        )
        return existing_conversation

    conversation = await create_system_conversation(
        user_id=user_id,
        description=workflow_title,
        system_purpose=SystemPurpose.WORKFLOW_EXECUTION,
    )

    # Add workflow metadata to conversation
    await conversations_collection.update_one(
        {"conversation_id": conversation["conversation_id"]},
        {
            "$set": {
                "metadata": {
                    "workflow_id": workflow_id,
                    "workflow_title": workflow_title,
                    "created_by": "workflow_system",
                }
            }
        },
    )

    logger.info(
        f"Created new workflow conversation {conversation['conversation_id']} for workflow {workflow_id}"
    )
    return conversation


async def add_workflow_execution_messages(
    conversation_id: str,
    workflow_execution_messages: List[MessageModel],
    user_id: str,
) -> None:
    """
    Add new execution messages to existing workflow conversation.

    Args:
        conversation_id: ID of the workflow conversation
        workflow_execution_messages: List of messages from workflow execution
        user_id: User ID for authorization
    """
    try:
        # Create update request
        messages_request = UpdateMessagesRequest(
            conversation_id=conversation_id, messages=workflow_execution_messages
        )

        # Use existing update_messages service
        user_dict = {"user_id": user_id}
        await update_messages(messages_request, user_dict)

        logger.info(
            f"Added {len(workflow_execution_messages)} execution messages to workflow conversation {conversation_id}"
        )

    except Exception as e:
        logger.error(
            f"Failed to add workflow execution messages to conversation {conversation_id}: {str(e)}"
        )
        raise


async def create_workflow_execution_summary_message(
    workflow_title: str,
    workflow_description: str,
    execution_start_time: datetime,
    execution_results: List[dict],
    success: bool = True,
) -> MessageModel:
    """
    Create a summary message for workflow execution.

    Args:
        workflow_title: Title of the workflow
        workflow_description: Description of the workflow
        execution_start_time: When the execution started
        execution_results: Results from workflow execution
        success: Whether the execution was successful

    Returns:
        MessageModel: Summary message for the execution
    """
    from uuid import uuid4

    execution_time = datetime.now(timezone.utc)
    duration = (execution_time - execution_start_time).total_seconds()

    if success:
        summary = f"""🚀 **Scheduled Workflow Execution**

**Workflow**: {workflow_title}
**Description**: {workflow_description}
**Executed**: {execution_time.strftime("%Y-%m-%d %H:%M:%S UTC")}
**Duration**: {duration:.1f}s
**Status**: ✅ Completed Successfully

**Steps Executed**: {len(execution_results)}"""

        for i, result in enumerate(execution_results, 1):
            step_status = "✅" if not result.get("error") else "❌"
            summary += f"\n{i}. {step_status} {result.get('step_id', f'Step {i}')}"

    else:
        summary = f"""🚀 **Scheduled Workflow Execution**

**Workflow**: {workflow_title}
**Executed**: {execution_time.strftime("%Y-%m-%d %H:%M:%S UTC")}
**Duration**: {duration:.1f}s
**Status**: ❌ Failed

**Error**: Workflow execution encountered an error."""

    return MessageModel(
        type="bot",
        response=summary,
        date=execution_time.isoformat(),
        message_id=str(uuid4()),
    )
