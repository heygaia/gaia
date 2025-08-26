"""
Workflow worker functions for ARQ task processing.
Contains all workflow-related background tasks and execution logic.
"""

from datetime import datetime, timezone
from typing import Optional

from app.config.loggers import arq_worker_logger as logger


async def _update_workflow_step_field(
    workflow_id: str, user_id: str, step_index: int, field_name: str, field_value
) -> bool:
    """
    Update a specific field of a workflow step using MongoDB field-specific operations.
    This avoids updating the entire workflow document.

    Args:
        workflow_id: ID of the workflow
        user_id: ID of the user who owns the workflow
        step_index: Index of the step to update (0-based)
        field_name: Name of the field to update (e.g., 'executed_at', 'result')
        field_value: New value for the field

    Returns:
        bool: True if update was successful, False otherwise
    """
    try:
        from app.db.mongodb.collections import workflows_collection
        from datetime import datetime, timezone

        # Use MongoDB positional operator to update specific array element
        update_data = {
            f"steps.{step_index}.{field_name}": field_value,
            "updated_at": datetime.now(timezone.utc),
        }

        result = await workflows_collection.update_one(
            {"_id": workflow_id, "user_id": user_id}, {"$set": update_data}
        )

        return result.modified_count > 0

    except Exception as e:
        logger.error(f"Failed to update workflow step field {field_name}: {str(e)}")
        return False


async def _update_workflow_execution_metrics(
    workflow_id: str,
    user_id: str,
    total_executions: int,
    successful_executions: Optional[int] = None,
) -> bool:
    """
    Update workflow execution metrics efficiently using MongoDB increment operations.

    Args:
        workflow_id: ID of the workflow
        user_id: ID of the user who owns the workflow
        total_executions: Total number of executions to increment
        successful_executions: Successful executions to increment (optional)

    Returns:
        bool: True if update was successful, False otherwise
    """
    try:
        from app.db.mongodb.collections import workflows_collection
        from datetime import datetime, timezone

        # Use MongoDB increment operations for atomic updates
        update_operations = {
            "$inc": {"total_executions": total_executions},
            "$set": {
                "last_executed_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            },
        }

        if successful_executions is not None:
            update_operations["$inc"]["successful_executions"] = successful_executions

        result = await workflows_collection.update_one(
            {"_id": workflow_id, "user_id": user_id}, update_operations
        )

        return result.modified_count > 0

    except Exception as e:
        logger.error(f"Failed to update workflow execution metrics: {str(e)}")
        return False


async def _batch_update_workflow_steps(
    workflow_id: str, user_id: str, step_updates: dict
) -> bool:
    """
    Batch update multiple workflow step fields in a single MongoDB operation.

    Args:
        workflow_id: ID of the workflow
        user_id: ID of the user who owns the workflow
        step_updates: Dictionary mapping step indices to field updates
                     e.g., {0: {'executed_at': datetime, 'result': {...}}}

    Returns:
        bool: True if update was successful, False otherwise
    """
    try:
        from app.db.mongodb.collections import workflows_collection
        from datetime import datetime, timezone

        # Build update document for multiple step fields
        update_data = {"updated_at": datetime.now(timezone.utc)}

        for step_index, fields in step_updates.items():
            for field_name, field_value in fields.items():
                update_data[f"steps.{step_index}.{field_name}"] = field_value

        result = await workflows_collection.update_one(
            {"_id": workflow_id, "user_id": user_id}, {"$set": update_data}
        )

        return result.modified_count > 0

    except Exception as e:
        logger.error(f"Failed to batch update workflow steps: {str(e)}")
        return False


async def process_workflow(
    ctx: dict, workflow_id: str, context: Optional[dict] = None
) -> str:
    """
    Process a workflow execution task using BaseSchedulerService.
    This leverages the robust scheduling infrastructure for recurring workflows,
    occurrence counting, and status management.

    Args:
        ctx: ARQ context
        workflow_id: ID of the workflow to execute
        context: Optional execution context

    Returns:
        Processing result message
    """
    logger.info(f"Processing workflow execution: {workflow_id}")

    try:
        # Use the robust WorkflowScheduler for execution and lifecycle management
        from app.services.workflow.scheduler import WorkflowScheduler

        scheduler = WorkflowScheduler()
        await scheduler.initialize()

        try:
            # This handles the complete execution lifecycle:
            # 1. Gets and validates the workflow
            # 2. Executes the workflow steps
            # 3. Handles recurring logic automatically
            # 4. Updates occurrence count and status
            # 5. Schedules next execution if recurring
            result = await scheduler.process_task_execution(workflow_id)

            if result.success:
                logger.info(
                    f"Workflow {workflow_id} executed successfully: {result.message}"
                )
                return f"Workflow executed successfully: {result.message}"
            else:
                logger.error(
                    f"Workflow {workflow_id} execution failed: {result.message}"
                )
                return f"Workflow execution failed: {result.message}"

        finally:
            await scheduler.close()

    except Exception as e:
        error_msg = f"Error processing workflow {workflow_id}: {str(e)}"
        logger.error(error_msg)

        # Update workflow status to failed
        try:
            from app.services.workflow.scheduler import WorkflowScheduler
            from app.models.scheduler_models import ScheduledTaskStatus

            scheduler = WorkflowScheduler()
            await scheduler.initialize()
            await scheduler.update_task_status(
                workflow_id, ScheduledTaskStatus.CANCELLED, {"error_message": str(e)}
            )
            await scheduler.close()
        except Exception as status_error:
            logger.error(f"Failed to update workflow status: {status_error}")

        return error_msg


async def execute_workflow_as_chat(workflow, user_id: str, context: dict) -> list:
    """
    Execute workflow as a single chat session, just like normal user chat.
    This creates proper tool calls and messages identical to normal chat flow.

    Args:
        workflow: The workflow object to execute
        user_id: User ID for context
        context: Optional execution context

    Returns:
        List of MessageModel objects from the execution
    """
    from uuid import uuid4
    from app.models.chat_models import MessageModel
    from app.langchain.core.graph_manager import GraphManager
    from app.services.workflow_conversation_service import (
        get_or_create_workflow_conversation,
    )

    try:
        logger.info(
            f"Executing workflow {workflow.id} as chat session for user {user_id}"
        )

        # Get or create the workflow conversation for thread context
        conversation = await get_or_create_workflow_conversation(
            workflow_id=workflow.id,
            user_id=user_id,
            workflow_title=workflow.title,
        )

        # Get the workflow processing graph (same as normal chat)
        graph = await GraphManager.get_graph("workflow_processing")
        if not graph:
            raise ValueError("Workflow processing graph not available")

        # Format workflow steps into a natural language prompt
        workflow_prompt = format_workflow_steps_as_prompt(workflow)

        # Create user message for workflow trigger
        user_message = MessageModel(
            type="user",
            response=f"🚀 **Scheduled Execution**: {workflow.title}\n\n{workflow_prompt}",
            date=datetime.now(timezone.utc).isoformat(),
            message_id=str(uuid4()),
        )

        # Execute via the normal chat graph (same as user chat)
        graph_config = {
            "configurable": {
                "user_id": user_id,
                "conversation_id": conversation["conversation_id"],
                "thread_id": f"workflow_{workflow.id}_{int(datetime.now(timezone.utc).timestamp())}",
            }
        }

        # Execute the workflow prompt through the graph
        initial_state = {
            "messages": [{"role": "user", "content": user_message.response}],
            "current_datetime": datetime.now(timezone.utc).isoformat(),
            "mem0_user_id": user_id,
            "conversation_id": conversation["conversation_id"],
        }

        # Invoke the graph (non-streaming for background execution)
        result = await graph.ainvoke(initial_state, config=graph_config)

        # Extract all messages from the result
        execution_messages = [user_message]

        # Convert LangChain messages to MessageModel objects
        for msg in result.get("messages", []):
            if hasattr(msg, "type") and msg.type == "ai":
                # This is the bot response with tool calls
                bot_message = MessageModel(
                    type="bot",
                    response=getattr(msg, "content", ""),
                    date=datetime.now(timezone.utc).isoformat(),
                    message_id=str(uuid4()),
                )
                execution_messages.append(bot_message)
            elif hasattr(msg, "type") and msg.type == "tool":
                # This is a tool call result - include it as well
                tool_message = MessageModel(
                    type="bot",
                    response=f"**Tool Used**: {getattr(msg, 'name', 'Unknown Tool')}\n**Result**: {getattr(msg, 'content', '')}",
                    date=datetime.now(timezone.utc).isoformat(),
                    message_id=str(uuid4()),
                )
                execution_messages.append(tool_message)

        logger.info(
            f"Workflow {workflow.id} executed successfully with {len(execution_messages)} messages"
        )
        return execution_messages

    except Exception as e:
        logger.error(f"Failed to execute workflow {workflow.id} as chat: {str(e)}")
        # Return error message
        error_message = MessageModel(
            type="bot",
            response=f"❌ **Workflow Execution Failed**\n\nWorkflow: {workflow.title}\nError: {str(e)}",
            date=datetime.now(timezone.utc).isoformat(),
            message_id=str(uuid4()),
        )
        return [error_message]


def format_workflow_steps_as_prompt(workflow) -> str:
    """Convert workflow steps into a natural language prompt for LLM execution."""
    prompt = f"""Please execute the following workflow steps in sequence:

**Workflow Goal**: {getattr(workflow, "description", "Complete the defined workflow tasks")}

**Steps to execute**:
"""

    for i, step in enumerate(workflow.steps, 1):
        prompt += f"\n{i}. **{step.title}**"
        prompt += f"\n   - Description: {step.description}"
        prompt += f"\n   - Tool: {step.tool_name}"
        if hasattr(step, "tool_inputs") and step.tool_inputs:
            prompt += f"\n   - Inputs: {step.tool_inputs}"
        prompt += "\n"

    prompt += "\nExecute each step using the appropriate tools and provide the results."
    return prompt


async def regenerate_workflow_steps(
    ctx: dict,
    workflow_id: str,
    user_id: str,
    regeneration_reason: str,
    force_different_tools: bool = True,
) -> str:
    """
    Regenerate workflow steps for an existing workflow.

    Args:
        ctx: ARQ context
        workflow_id: ID of the workflow to regenerate steps for
        user_id: ID of the user who owns the workflow
        regeneration_reason: Reason for regeneration
        force_different_tools: Whether to force different tools

    Returns:
        Processing result message
    """
    logger.info(
        f"Regenerating workflow steps: {workflow_id} for user {user_id}, reason: {regeneration_reason}"
    )

    try:
        # Import here to avoid circular imports
        from app.services.workflow import WorkflowService

        # Regenerate steps using the service method (without background queue)
        await WorkflowService.regenerate_workflow_steps(
            workflow_id,
            user_id,
            regeneration_reason,
            force_different_tools,
        )

        result = f"Successfully regenerated steps for workflow {workflow_id}"
        logger.info(result)
        return result

    except Exception as e:
        error_msg = f"Failed to regenerate workflow steps {workflow_id}: {str(e)}"
        logger.error(error_msg)
        raise


async def generate_workflow_steps(ctx: dict, workflow_id: str, user_id: str) -> str:
    """
    Generate workflow steps for a workflow.

    Args:
        ctx: ARQ context
        workflow_id: ID of the workflow to generate steps for
        user_id: ID of the user who owns the workflow

    Returns:
        Processing result message
    """
    logger.info(f"Generating workflow steps: {workflow_id} for user {user_id}")

    try:
        # Import here to avoid circular imports
        from app.services.workflow import WorkflowService

        # Generate steps using the service method
        await WorkflowService._generate_workflow_steps(workflow_id, user_id)

        result = f"Successfully generated steps for workflow {workflow_id}"
        logger.info(result)
        return result

    except Exception as e:
        error_msg = f"Failed to generate workflow steps {workflow_id}: {str(e)}"
        logger.error(error_msg)
        raise


async def create_workflow_completion_notification(
    workflow, execution_messages, user_id: str
):
    """Create or update workflow conversation with execution results and send notification."""
    try:
        # Import here to avoid circular imports
        from app.services.workflow_conversation_service import (
            get_or_create_workflow_conversation,
            add_workflow_execution_messages,
        )
        from app.services.notification_service import notification_service
        from app.models.notification.notification_models import (
            NotificationRequest,
            NotificationContent,
            ChannelConfig,
            NotificationSourceEnum,
            NotificationAction,
            ActionType,
            ActionStyle,
            ActionConfig,
            RedirectConfig,
        )

        # Get or create the workflow's persistent conversation
        conversation = await get_or_create_workflow_conversation(
            workflow_id=workflow.id,
            user_id=user_id,
            workflow_title=workflow.title,
        )

        # Add execution messages to the conversation
        if execution_messages:
            await add_workflow_execution_messages(
                conversation_id=conversation["conversation_id"],
                workflow_execution_messages=execution_messages,
                user_id=user_id,
            )

        # Send notification with action to view results
        notification_request = NotificationRequest(
            user_id=user_id,
            source=NotificationSourceEnum.BACKGROUND_JOB,
            content=NotificationContent(
                title=f"⚡ Workflow Completed: {workflow.title}",
                body=f"Your workflow '{workflow.title}' has completed successfully.",
                actions=[
                    NotificationAction(
                        type=ActionType.REDIRECT,
                        label="View Results",
                        style=ActionStyle.PRIMARY,
                        config=ActionConfig(
                            redirect=RedirectConfig(
                                url=f"/c/{conversation['conversation_id']}",
                                open_in_new_tab=False,
                                close_notification=True,
                            )
                        ),
                    )
                ],
            ),
            channels=[ChannelConfig(channel_type="inapp", enabled=True, priority=1)],
            metadata={
                "workflow_id": workflow.id,
                "conversation_id": conversation["conversation_id"],
            },
        )

        await notification_service.create_notification(notification_request)
        logger.info(f"Sent workflow completion notification for workflow {workflow.id}")

    except Exception as e:
        logger.error(f"Failed to create workflow completion notification: {str(e)}")
        # Don't raise - this shouldn't fail the workflow execution
