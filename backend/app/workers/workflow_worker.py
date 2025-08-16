"""
Workflow worker functions for ARQ task processing.
Contains all workflow-related background tasks and execution logic.
"""

from datetime import datetime, timezone
import uuid
from typing import Optional

from app.config.loggers import arq_worker_logger as logger


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
        from app.services.workflow_service import WorkflowService
        from app.models.workflow_models import UpdateWorkflowRequest, WorkflowStatus
        from app.langchain.core.graph_manager import GraphManager

        # Get the workflow
        workflow = await WorkflowService.get_workflow(workflow_id, user_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        if not workflow.steps:
            raise ValueError(f"Workflow {workflow_id} has no steps to execute")

        # Update workflow status to running
        await WorkflowService.update_workflow(
            workflow_id,
            UpdateWorkflowRequest(status=WorkflowStatus.RUNNING),
            user_id,
        )

        # Get the processing graph
        graph = await GraphManager.get_graph("reminder_processing")
        if not graph:
            raise ValueError("Processing graph not available")

        # Execute workflow steps sequentially
        execution_results = []
        accumulated_context = context or {}

        for step_index, step in enumerate(workflow.steps):
            try:
                logger.info(
                    f"Executing step {step_index + 1}/{len(workflow.steps)}: {step.title}"
                )

                # Update current step status
                step.status = WorkflowStatus.RUNNING
                step.executed_at = datetime.now(timezone.utc)

                # Update workflow with current step progress
                await WorkflowService.update_workflow(
                    workflow_id,
                    UpdateWorkflowRequest(steps=workflow.steps),
                    user_id,
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
                    "status": "completed",
                    "result": result.get("messages", [])[-1].get("content", "")
                    if result.get("messages")
                    else "",
                    "executed_at": step.executed_at.isoformat(),
                }

                # Update step with results
                step.status = WorkflowStatus.COMPLETED
                step.result = step_result
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

                # Mark step as failed
                step.status = WorkflowStatus.FAILED
                step.result = {"error": str(step_error)}

                # Update workflow with failed step
                await WorkflowService.update_workflow(
                    workflow_id,
                    UpdateWorkflowRequest(
                        status=WorkflowStatus.FAILED,
                        steps=workflow.steps,
                    ),
                    user_id,
                )

                raise step_error

        # All steps completed successfully
        workflow.total_executions += 1
        workflow.successful_executions += 1
        workflow.last_executed_at = datetime.now(timezone.utc)

        await WorkflowService.update_workflow(
            workflow_id,
            UpdateWorkflowRequest(
                status=WorkflowStatus.COMPLETED,
                steps=workflow.steps,
            ),
            user_id,
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

        # Mark workflow as failed
        try:
            from app.services.workflow_service import WorkflowService
            from app.models.workflow_models import UpdateWorkflowRequest, WorkflowStatus

            workflow = await WorkflowService.get_workflow(workflow_id, user_id)
            if workflow:
                workflow.total_executions += 1

            await WorkflowService.update_workflow(
                workflow_id,
                UpdateWorkflowRequest(
                    status=WorkflowStatus.FAILED,
                ),
                user_id,
            )
        except Exception as update_e:
            logger.error(
                f"Failed to mark workflow {workflow_id} as failed: {str(update_e)}"
            )

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
        from app.services.workflow_service import WorkflowService

        # Generate steps using the service method
        await WorkflowService._generate_workflow_steps(workflow_id, user_id)

        result = f"Successfully generated steps for workflow {workflow_id}"
        logger.info(result)
        return result

    except Exception as e:
        error_msg = f"Failed to generate workflow steps {workflow_id}: {str(e)}"
        logger.error(error_msg)
        raise


async def check_scheduled_workflows(ctx: dict) -> str:
    """
    Check for scheduled workflows that need to be executed.

    Args:
        ctx: ARQ context

    Returns:
        Processing result message
    """
    logger.info("Checking for scheduled workflows")

    try:
        from app.db.mongodb.collections import workflows_collection
        from app.models.workflow_models import WorkflowStatus
        from arq import create_pool
        from arq.connections import RedisSettings
        from app.config.settings import settings

        # Find workflows that are scheduled and enabled
        cursor = workflows_collection.find(
            {
                "status": WorkflowStatus.ACTIVE,
                "trigger_config.type": "schedule",
                "trigger_config.enabled": True,
                "trigger_config.next_run": {"$lte": datetime.now(timezone.utc)},
            }
        )

        executed_count = 0
        redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
        pool = await create_pool(redis_settings)

        try:
            async for workflow_doc in cursor:
                try:
                    # Queue workflow execution with empty context
                    job = await pool.enqueue_job(
                        "process_workflow",
                        workflow_doc["_id"],
                        workflow_doc["user_id"],
                        {},  # Add context parameter
                    )

                    if job:
                        executed_count += 1
                        logger.info(f"Queued scheduled workflow {workflow_doc['_id']}")

                except Exception as e:
                    logger.error(
                        f"Failed to queue scheduled workflow {workflow_doc['_id']}: {str(e)}"
                    )
        finally:
            await pool.close()

        result = f"Checked scheduled workflows, queued {executed_count} for execution"
        logger.info(result)
        return result

    except Exception as e:
        error_msg = f"Failed to check scheduled workflows: {str(e)}"
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
            content += f"\n{i}. **{result['step_id']}** - {result['status'].title()}"
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
