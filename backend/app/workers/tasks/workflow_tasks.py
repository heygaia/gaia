"""
Workflow worker functions for ARQ task processing.
Contains all workflow-related background tasks and execution logic.
"""

from datetime import datetime, timezone
from typing import Optional, Tuple

from app.config.loggers import arq_worker_logger as logger
from bson import ObjectId


async def get_user_authentication_tokens(
    user_id: str,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Retrieve user authentication tokens for workflow execution.

    This wrapper function handles token retrieval and refresh for background workflow execution,
    following the same pattern as chat streams to ensure consistent authentication.

    Args:
        user_id: The user ID to get tokens for

    Returns:
        Tuple of (access_token, refresh_token) or (None, None) if not available
    """
    try:
        from app.config.token_repository import token_repository

        token = await token_repository.get_token(
            str(user_id), "google", renew_if_expired=True
        )
        if token:
            access_token = (
                str(token.get("access_token", ""))
                if token.get("access_token")
                else None
            )
            refresh_token = (
                str(token.get("refresh_token", ""))
                if token.get("refresh_token")
                else None
            )
            if access_token and refresh_token:
                logger.info(
                    f"Successfully retrieved authentication tokens for user {user_id}"
                )
                return access_token, refresh_token
            else:
                logger.warning(
                    f"Tokens found but empty for user {user_id} - access_token: {bool(access_token)}, refresh_token: {bool(refresh_token)}"
                )
                return None, None
        else:
            logger.warning(f"No authentication tokens found for user {user_id}")
            return None, None

    except Exception as e:
        logger.error(f"Error retrieving authentication tokens for user {user_id}: {e}")
        return None, None


async def process_workflow_generation_task(
    ctx: dict, todo_id: str, user_id: str, title: str, description: str = ""
) -> str:
    """
    Process workflow generation task for todos.
    Migrated from RabbitMQ to ARQ for unified task processing.

    Args:
        ctx: ARQ context
        todo_id: Todo ID to generate workflow for
        user_id: User ID who owns the todo
        title: Todo title
        description: Todo description

    Returns:
        Processing result message
    """
    from app.db.mongodb.collections import todos_collection
    from app.models.workflow_models import (
        CreateWorkflowRequest,
        TriggerConfig,
        TriggerType,
    )
    from app.services.todo_service import TodoService
    from app.services.workflow.service import WorkflowService

    logger.info(f"Processing workflow generation for todo {todo_id}: {title}")

    try:
        # Create standalone workflow using the new workflow system
        workflow_request = CreateWorkflowRequest(
            title=f"Todo: {title}",
            description=description or f"Workflow for todo: {title}",
            trigger_config=TriggerConfig(type=TriggerType.MANUAL, enabled=True),
            generate_immediately=True,  # Generate steps immediately
        )

        workflow = await WorkflowService.create_workflow(workflow_request, user_id)

        if workflow and workflow.id:
            # Update the todo with the workflow_id for linking
            update_data = {
                "workflow_id": workflow.id,
                "updated_at": datetime.now(timezone.utc),
            }

            result = await todos_collection.update_one(
                {"_id": ObjectId(todo_id), "user_id": user_id}, {"$set": update_data}
            )

            if result.modified_count > 0:
                logger.info(
                    f"Successfully generated and linked standalone workflow {workflow.id} for todo {todo_id} with {len(workflow.steps)} steps"
                )

                # Invalidate cache for this todo
                await TodoService._invalidate_cache(user_id, None, todo_id, "update")

                return f"Successfully generated standalone workflow {workflow.id} for todo {todo_id}"
            else:
                raise ValueError(f"Todo {todo_id} not found or not updated")

        else:
            # Mark workflow generation as failed
            logger.error(
                f"Failed to generate workflow for todo {todo_id}: No workflow created"
            )
            raise ValueError("Workflow generation failed: No workflow created")

    except Exception as e:
        # Log the error but don't try to update legacy workflow fields
        error_msg = (
            f"Failed to process workflow generation for todo {todo_id}: {str(e)}"
        )
        logger.error(error_msg)
        raise


async def execute_workflow_by_id(
    ctx: dict, workflow_id: str, context: Optional[dict] = None
) -> str:
    """
    ARQ-compatible workflow execution function.
    Fetches workflow by ID and executes it using execute_workflow_as_chat.

    Args:
        ctx: ARQ context
        workflow_id: ID of the workflow to execute
        context: Optional execution context

    Returns:
        Processing result message
    """
    logger.info(f"Processing workflow execution: {workflow_id}")

    try:
        # Get workflow from database
        from app.services.workflow.scheduler import WorkflowScheduler

        scheduler = WorkflowScheduler()
        await scheduler.initialize()

        try:
            workflow = await scheduler.get_task(workflow_id)
            if not workflow:
                return f"Workflow {workflow_id} not found"

            # Execute the workflow and get messages
            execution_messages = await execute_workflow_as_chat(
                workflow, workflow.user_id, context or {}
            )

            # Store messages and send notification
            await create_workflow_completion_notification(
                workflow, execution_messages, workflow.user_id
            )

            return f"Workflow {workflow_id} executed successfully with {len(execution_messages)} messages"

        finally:
            await scheduler.close()

    except Exception as e:
        error_msg = f"Error executing workflow {workflow_id}: {str(e)}"
        logger.error(error_msg)
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
    from app.services.workflow_conversation_service import (
        get_or_create_workflow_conversation,
    )

    try:
        logger.info(
            f"Executing workflow {workflow.id} as chat session for user {user_id}"
        )

        # Get user tokens for authentication (same as chat stream)
        access_token, refresh_token = await get_user_authentication_tokens(user_id)

        if not access_token:
            logger.error(
                f"No access token available for user {user_id} - workflow tools requiring authentication will fail"
            )
        else:
            logger.info(
                f"Access token available for user {user_id} - tools can authenticate"
            )

        # Get user information for tools that may need it (e.g., email tools)
        user_obj: dict = {"user_id": user_id}
        try:
            from app.services.user_service import get_user_by_id

            user_data = await get_user_by_id(user_id)
            if user_data:
                if user_data.get("email"):
                    user_obj["email"] = str(user_data.get("email"))
                if user_data.get("name"):
                    user_obj["name"] = str(user_data.get("name"))
                user_obj["user_id"] = user_id
                logger.info(
                    f"Enhanced user object for workflow execution: email={bool(user_obj.get('email'))}, name={bool(user_obj.get('name'))}"
                )
        except Exception as e:
            logger.warning(f"Could not get user data for {user_id}: {e}")
            # Continue with minimal user object

        # Get or create the workflow conversation for thread context
        conversation = await get_or_create_workflow_conversation(
            workflow_id=workflow.id,
            user_id=user_id,
            workflow_title=workflow.title,
        )

        # Convert workflow to SelectedWorkflowData format for proper handling
        from app.models.message_models import (
            SelectedWorkflowData,
            MessageRequestWithHistory,
        )
        from app.langchain.core.agent import call_agent_silent

        # Convert workflow steps to the format expected by SelectedWorkflowData
        workflow_steps = []
        for step in workflow.steps:
            workflow_steps.append(
                {
                    "id": step.id,
                    "title": step.title,
                    "description": step.description,
                    "tool_name": step.tool_name,
                    "tool_category": step.tool_category,
                }
            )

        selected_workflow_data = SelectedWorkflowData(
            id=workflow.id,
            title=workflow.title,
            description=workflow.description,
            steps=workflow_steps,
        )

        # Create a simple MessageRequestWithHistory for workflow execution
        request = MessageRequestWithHistory(
            message=f"Execute workflow: {workflow.title}",
            messages=[],
            fileIds=[],
            fileData=[],
            selectedTool=None,
            selectedWorkflow=selected_workflow_data,
        )

        # Execute using the same logic as normal chat
        complete_message, tool_data = await call_agent_silent(
            request=request,
            conversation_id=conversation["conversation_id"],
            user=user_obj,
            user_time=datetime.now(timezone.utc),
            access_token=access_token,
            refresh_token=refresh_token,
        )

        # Create execution messages with proper tool data
        execution_messages = []

        # Create a simple user message showing workflow execution (like frontend)
        user_message = MessageModel(
            type="user",
            response="",
            date=datetime.now(timezone.utc).isoformat(),
            message_id=str(uuid4()),
            selectedWorkflow=selected_workflow_data,
        )
        execution_messages.append(user_message)

        # Create the bot message with complete response and tool data
        bot_message = MessageModel(
            type="bot",
            response=complete_message,
            date=datetime.now(timezone.utc).isoformat(),
            message_id=str(uuid4()),
            **tool_data,  # Include all captured tool data
        )
        execution_messages.append(bot_message)

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
        from app.models.notification.notification_models import (
            ActionConfig,
            ActionStyle,
            ActionType,
            ChannelConfig,
            NotificationAction,
            NotificationContent,
            NotificationRequest,
            NotificationSourceEnum,
            RedirectConfig,
        )
        from app.services.notification_service import notification_service
        from app.services.workflow_conversation_service import (
            add_workflow_execution_messages,
            get_or_create_workflow_conversation,
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
                title=f"Workflow Completed: {workflow.title}",
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
