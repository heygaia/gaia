"""
Workflow worker functions for ARQ task processing.
Contains all workflow-related background tasks and execution logic.
"""

from datetime import datetime, timezone
import uuid
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
    ctx: dict, workflow_id: str, user_id: str, context: Optional[dict] = None
) -> str:
    """
    Process a workflow execution task.
    Executes workflow steps sequentially via the existing LangChain graph.

    Args:
        ctx: ARQ context
        workflow_id: ID of the workflow to execute
        user_id: ID of the user who owns the workflow
        context: Optional execution context

    Returns:
        Processing result message
    """
    logger.info(f"Processing workflow execution: {workflow_id} for user {user_id}")

    try:
        # Import here to avoid circular imports
        from app.services.workflow import WorkflowService
        from app.models.workflow_models import UpdateWorkflowRequest
        from app.langchain.core.graph_manager import GraphManager

        # Get the workflow
        workflow = await WorkflowService.get_workflow(workflow_id, user_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        if not workflow.steps:
            raise ValueError(f"Workflow {workflow_id} has no steps to execute")

        # Update workflow updated timestamp
        await WorkflowService.update_workflow(
            workflow_id,
            UpdateWorkflowRequest(),
            user_id,
        )

        # Get the workflow processing graph
        graph = await GraphManager.get_graph("workflow_processing")
        if not graph:
            raise ValueError("Workflow processing graph not available")

        # Execute workflow steps sequentially
        execution_results = []
        accumulated_context = context or {}

        for step_index, step in enumerate(workflow.steps):
            try:
                logger.info(
                    f"Executing step {step_index + 1}/{len(workflow.steps)}: {step.title}"
                )

                # Update step execution timestamp using optimized field update
                step.executed_at = datetime.now(timezone.utc)
                await _update_workflow_step_field(
                    workflow_id, user_id, step_index, "executed_at", step.executed_at
                )

                # Execute the tool directly via graph
                graph_config = {
                    "configurable": {
                        "user_id": user_id,
                        "conversation_id": f"workflow_{workflow_id}",
                        "thread_id": f"workflow_{workflow_id}_step_{step_index}",
                    }
                }

                # Create a tool execution message
                tool_message = f"Use {step.tool_name} tool"
                if step.tool_inputs:
                    tool_message += f" with inputs: {step.tool_inputs}"

                # Execute via graph
                result = await graph.ainvoke(
                    {"messages": [{"role": "user", "content": tool_message}]},
                    config=graph_config,
                )

                # Extract result from graph response
                step_result = {
                    "step_id": step.id,
                    "tool_name": step.tool_name,
                    "result": result.get("messages", [])[-1].get("content", "")
                    if result.get("messages")
                    else "",
                    "executed_at": step.executed_at.isoformat(),
                }

                # Update step with results using optimized field update
                step.result = step_result
                await _update_workflow_step_field(
                    workflow_id, user_id, step_index, "result", step_result
                )
                execution_results.append(step_result)

                # Add to accumulated context for next steps
                accumulated_context[f"step_{step_index + 1}_result"] = step_result[
                    "result"
                ]

                logger.info(f"Completed step {step_index + 1}: {step.title}")

            except Exception as step_error:
                logger.error(
                    f"Failed to execute step {step_index + 1}: {str(step_error)}"
                )

                # Mark step as failed using optimized field update
                step.result = {"error": str(step_error)}
                await _update_workflow_step_field(
                    workflow_id, user_id, step_index, "result", step.result
                )

                raise step_error

        # All steps completed successfully - update execution metrics efficiently
        await _update_workflow_execution_metrics(
            workflow_id, user_id, total_executions=1, successful_executions=1
        )

        # Schedule next execution for scheduled workflows
        if (
            workflow.trigger_config.type == "schedule"
            and workflow.trigger_config.enabled
            and workflow.trigger_config.cron_expression
            and workflow.activated
        ):
            # Calculate next run time
            next_run = workflow.trigger_config.calculate_next_run()
            if next_run:
                # Update the next_run field in database
                from app.db.mongodb.collections import workflows_collection

                await workflows_collection.update_one(
                    {"_id": workflow_id, "user_id": user_id},
                    {"$set": {"trigger_config.next_run": next_run}},
                )

                # Schedule the next execution
                from app.services.workflow.scheduler_service import (
                    WorkflowSchedulerService,
                )

                await WorkflowSchedulerService.schedule_workflow_execution(
                    workflow_id, user_id, next_run
                )
                logger.info(
                    f"Scheduled next execution of workflow {workflow_id} for {next_run}"
                )

        # Create result summary and notification
        await create_workflow_completion_notification(
            workflow, execution_results, user_id
        )

        result = f"Successfully executed workflow {workflow_id} with {len(workflow.steps)} steps"
        logger.info(result)
        return result

    except Exception as e:
        error_msg = f"Failed to process workflow {workflow_id}: {str(e)}"
        logger.error(error_msg)

        # Mark workflow as failed using optimized execution metrics update
        try:
            await _update_workflow_execution_metrics(
                workflow_id, user_id, total_executions=1, successful_executions=0
            )
        except Exception as update_e:
            logger.error(
                f"Failed to mark workflow {workflow_id} as failed: {str(update_e)}"
            )

        raise


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
    workflow, execution_results, user_id: str
):
    """Create a new conversation with workflow results and send notification."""
    try:
        # Import here to avoid circular imports
        from app.db.mongodb.collections import conversations_collection
        from app.services.notification_service import notification_service
        from app.models.notification.notification_models import NotificationRequest

        # Create conversation content
        content = f"""🎯 **Workflow Completed: {workflow.title}**

📝 **Original Goal:** {workflow.goal}

✅ **Execution Summary:**
• Total Steps: {len(workflow.steps)}
• Completed: {len(execution_results)}
• Duration: {(datetime.now(timezone.utc) - workflow.last_executed_at).total_seconds():.1f}s

🔧 **Step Results:**
"""

        for i, result in enumerate(execution_results, 1):
            status_text = "❌ Failed" if result.get("error") else "✅ Completed"
            content += f"\n{i}. **{result['step_id']}** - {status_text}"
            if result.get("result"):
                # Truncate long results
                result_text = (
                    str(result["result"])[:200] + "..."
                    if len(str(result["result"])) > 200
                    else str(result["result"])
                )
                content += f"\n   📄 {result_text}"

        content += f"\n\n🕒 **Completed:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"

        # Create new conversation
        conversation_doc = {
            "_id": f"conv_{uuid.uuid4().hex[:12]}",
            "user_id": user_id,
            "title": f"Workflow Results: {workflow.title}",
            "messages": [
                {
                    "role": "assistant",
                    "content": content,
                    "timestamp": datetime.now(timezone.utc),
                    "metadata": {
                        "type": "workflow_completion",
                        "workflow_id": workflow.id,
                        "created_by": "GAIA",
                    },
                }
            ],
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "is_pinned": False,
            "metadata": {
                "created_by": "workflow_system",
                "workflow_id": workflow.id,
                "workflow_title": workflow.title,
            },
        }

        # Insert conversation
        await conversations_collection.insert_one(conversation_doc)
        logger.info(
            f"Created workflow completion conversation for workflow {workflow.id}"
        )

        # Send notification
        from app.models.notification.notification_models import (
            NotificationContent,
            ChannelConfig,
            NotificationSourceEnum,
        )

        notification_request = NotificationRequest(
            user_id=user_id,
            source=NotificationSourceEnum.BACKGROUND_JOB,
            content=NotificationContent(
                title=f"Workflow Completed: {workflow.title}",
                body=f"Your workflow '{workflow.title}' has completed successfully with {len(execution_results)} steps.",
            ),
            channels=[ChannelConfig(channel_type="inapp", enabled=True, priority=1)],
            metadata={
                "workflow_id": workflow.id,
                "conversation_id": conversation_doc["_id"],
            },
        )

        await notification_service.create_notification(notification_request)
        logger.info(f"Sent workflow completion notification for workflow {workflow.id}")

    except Exception as e:
        logger.error(f"Failed to create workflow completion notification: {str(e)}")
        # Don't raise - this shouldn't fail the workflow execution
