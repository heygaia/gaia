"""
Clean workflow service for GAIA workflow system.
Handles workflow CRUD operations and execution coordination.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.config.loggers import general_logger as logger
from app.db.mongodb.collections import workflows_collection
from app.models.workflow_models import (
    CreateWorkflowRequest,
    UpdateWorkflowRequest,
    Workflow,
    WorkflowExecutionRequest,
    WorkflowExecutionResponse,
    WorkflowStatusResponse,
)


# Helper functions
def transform_doc(doc: dict) -> dict:
    """Transform MongoDB document by adding id field from _id."""
    if doc and "_id" in doc:
        doc["id"] = doc["_id"]
    return doc


class WorkflowValidator:
    """Validator class for workflow operations."""

    @staticmethod
    def can_execute(workflow: Workflow) -> bool:
        """Check if workflow can be executed (just check if activated)."""
        return workflow.activated

    @staticmethod
    def validate_execution(workflow: Workflow) -> None:
        """Validate workflow can be executed, raise exception if not."""
        if not WorkflowValidator.can_execute(workflow):
            raise ValueError("Workflow is deactivated and cannot be executed")


class RedisPoolManager:
    """Singleton Redis pool manager for queue operations."""

    _pool = None

    @classmethod
    async def get_pool(cls):
        """Get or create Redis pool."""
        if not cls._pool:
            from arq import create_pool
            from arq.connections import RedisSettings
            from app.config.settings import settings

            redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
            cls._pool = await create_pool(redis_settings)
        return cls._pool


async def handle_workflow_error(
    workflow_id: str,
    user_id: str,
    error: Exception,
    deactivate: bool = False,
) -> None:
    """Centralized error handling for workflow operations."""
    try:
        update_data: Dict[str, Any] = {"updated_at": datetime.now(timezone.utc)}
        if deactivate:
            update_data["activated"] = False

        await workflows_collection.find_one_and_update(
            {"_id": workflow_id, "user_id": user_id},
            {"$set": update_data},
        )
        logger.error(f"Workflow {workflow_id} error: {error}")
    except Exception as update_error:
        logger.error(
            f"Failed to update workflow {workflow_id} error state: {update_error}"
        )


class WorkflowService:
    """Service class for workflow operations."""

    @staticmethod
    async def create_workflow(request: CreateWorkflowRequest, user_id: str) -> Workflow:
        """Create a new workflow."""
        try:
            # Calculate next_run for scheduled workflows
            trigger_config = request.trigger_config
            if trigger_config.type == "schedule" and trigger_config.cron_expression:
                trigger_config.update_next_run()

            # Create workflow object
            workflow = Workflow(
                title=request.title,
                description=request.description,
                steps=[],  # Steps will be generated
                trigger_config=trigger_config,
                activated=True,  # Default to activated
                user_id=user_id,
            )

            # Insert into database
            workflow_dict = workflow.model_dump()
            workflow_dict["_id"] = workflow_dict["id"]

            result = await workflows_collection.insert_one(workflow_dict)
            if not result.inserted_id:
                raise ValueError("Failed to create workflow in database")

            logger.info(f"Created workflow {workflow.id} for user {user_id}")

            # Schedule the workflow if it's a scheduled type and enabled
            if (
                trigger_config.type == "schedule"
                and trigger_config.enabled
                and trigger_config.next_run
            ):
                await WorkflowService._schedule_workflow_execution(
                    workflow.id, user_id, trigger_config.next_run
                )

            # Generate steps
            if request.generate_immediately:
                await WorkflowService._generate_workflow_steps(workflow.id, user_id)
            else:
                await WorkflowService._queue_workflow_generation(workflow.id, user_id)

            return workflow

        except Exception as e:
            logger.error(f"Error creating workflow: {str(e)}")
            raise

    @staticmethod
    async def get_workflow(workflow_id: str, user_id: str) -> Optional[Workflow]:
        """Get a workflow by ID."""
        try:
            workflow_doc = await workflows_collection.find_one(
                {"_id": workflow_id, "user_id": user_id}
            )

            if not workflow_doc:
                return None

            return Workflow(**transform_doc(workflow_doc))

        except Exception as e:
            logger.error(f"Error getting workflow {workflow_id}: {str(e)}")
            raise

    @staticmethod
    async def list_workflows(user_id: str) -> List[Workflow]:
        """List all workflows for a user."""
        try:
            cursor = workflows_collection.find({"user_id": user_id}).sort(
                "created_at", -1
            )
            workflows = []

            async for doc in cursor:
                workflows.append(Workflow(**transform_doc(doc)))

            logger.debug(f"Retrieved {len(workflows)} workflows for user {user_id}")
            return workflows

        except Exception as e:
            logger.error(f"Error listing workflows for user {user_id}: {str(e)}")
            raise

    @staticmethod
    async def update_workflow(
        workflow_id: str, request: UpdateWorkflowRequest, user_id: str
    ) -> Optional[Workflow]:
        """Update an existing workflow."""
        try:
            # Get current workflow to check for trigger changes
            current_workflow = await WorkflowService.get_workflow(workflow_id, user_id)
            if not current_workflow:
                return None

            update_data = {"updated_at": datetime.now(timezone.utc)}
            update_fields = request.model_dump(exclude_unset=True)

            # Handle trigger config changes
            if "trigger_config" in update_fields:
                new_trigger_config = update_fields["trigger_config"]

                # Calculate next_run for scheduled workflows
                if (
                    new_trigger_config.type == "schedule"
                    and new_trigger_config.cron_expression
                ):
                    new_trigger_config.update_next_run()

                # Check if we need to reschedule
                old_config = current_workflow.trigger_config
                schedule_changed = (
                    old_config.type != new_trigger_config.type
                    or old_config.cron_expression != new_trigger_config.cron_expression
                    or old_config.enabled != new_trigger_config.enabled
                )

                if schedule_changed:
                    # Cancel existing scheduled job
                    await WorkflowService._cancel_scheduled_workflow_execution(
                        workflow_id
                    )

                    # Schedule new execution if conditions are met
                    if (
                        new_trigger_config.type == "schedule"
                        and new_trigger_config.enabled
                        and new_trigger_config.next_run
                        and current_workflow.activated
                    ):
                        await WorkflowService._schedule_workflow_execution(
                            workflow_id, user_id, new_trigger_config.next_run
                        )

            update_data.update(update_fields)

            result = await workflows_collection.update_one(
                {"_id": workflow_id, "user_id": user_id}, {"$set": update_data}
            )

            if result.matched_count == 0:
                return None

            logger.info(f"Updated workflow {workflow_id} for user {user_id}")
            return await WorkflowService.get_workflow(workflow_id, user_id)

        except Exception as e:
            logger.error(f"Error updating workflow {workflow_id}: {str(e)}")
            raise

    @staticmethod
    async def delete_workflow(workflow_id: str, user_id: str) -> bool:
        """Delete a workflow."""
        try:
            # Cancel any scheduled executions before deleting
            await WorkflowService._cancel_scheduled_workflow_execution(workflow_id)

            result = await workflows_collection.delete_one(
                {"_id": workflow_id, "user_id": user_id}
            )

            if result.deleted_count == 0:
                return False

            logger.info(f"Deleted workflow {workflow_id} for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting workflow {workflow_id}: {str(e)}")
            raise

    @staticmethod
    async def execute_workflow(
        workflow_id: str, request: WorkflowExecutionRequest, user_id: str
    ) -> WorkflowExecutionResponse:
        """Execute a workflow."""
        try:
            workflow = await WorkflowService.get_workflow(workflow_id, user_id)
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")

            # Use validator to check execution readiness
            WorkflowValidator.validate_execution(workflow)

            # Just update the last execution timestamp
            result = await workflows_collection.find_one_and_update(
                {"_id": workflow_id, "user_id": user_id},
                {
                    "$set": {
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
            )

            if not result:
                raise ValueError(f"Failed to update workflow {workflow_id}")

            # Generate unique execution ID with UUID
            execution_id = f"exec_{workflow_id}_{uuid.uuid4().hex[:8]}"

            # Queue workflow execution
            await WorkflowService._queue_workflow_execution(
                workflow_id, user_id, request.context
            )

            logger.info(f"Started execution {execution_id} for workflow {workflow_id}")

            return WorkflowExecutionResponse(
                execution_id=execution_id,
                message="Workflow execution started",
            )

        except Exception as e:
            logger.error(f"Error executing workflow {workflow_id}: {str(e)}")
            raise

    @staticmethod
    async def get_workflow_status(
        workflow_id: str, user_id: str
    ) -> WorkflowStatusResponse:
        """Get the current status of a workflow."""
        try:
            workflow = await WorkflowService.get_workflow(workflow_id, user_id)
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")

            total_steps = len(workflow.steps)
            progress_percentage = 0.0

            if total_steps > 0:
                # Since we removed step status, just show progress as 0% unless workflow execution is finished
                progress_percentage = 0

            return WorkflowStatusResponse(
                workflow_id=workflow_id,
                activated=workflow.activated,
                current_step_index=workflow.current_step_index,
                total_steps=total_steps,
                progress_percentage=progress_percentage,
                last_updated=workflow.updated_at,
                error_message=workflow.error_message,
                logs=workflow.execution_logs,
            )

        except Exception as e:
            logger.error(f"Error getting workflow status {workflow_id}: {str(e)}")
            raise

    @staticmethod
    async def activate_workflow(workflow_id: str, user_id: str) -> Optional[Workflow]:
        """Activate a workflow (enable its trigger)."""
        try:
            workflow = await WorkflowService.get_workflow(workflow_id, user_id)
            if not workflow:
                return None

            # Update trigger to enabled and status to active
            trigger_config = workflow.trigger_config
            trigger_config.enabled = True

            return await WorkflowService.update_workflow(
                workflow_id,
                UpdateWorkflowRequest(trigger_config=trigger_config, activated=True),
                user_id,
            )

        except Exception as e:
            logger.error(f"Error activating workflow {workflow_id}: {str(e)}")
            raise

    @staticmethod
    async def deactivate_workflow(workflow_id: str, user_id: str) -> Optional[Workflow]:
        """Deactivate a workflow (disable its trigger)."""
        try:
            workflow = await WorkflowService.get_workflow(workflow_id, user_id)
            if not workflow:
                return None

            # Cancel any scheduled executions
            await WorkflowService._cancel_scheduled_workflow_execution(workflow_id)

            # Update trigger to disabled and status to inactive
            trigger_config = workflow.trigger_config
            trigger_config.enabled = False

            return await WorkflowService.update_workflow(
                workflow_id,
                UpdateWorkflowRequest(trigger_config=trigger_config, activated=False),
                user_id,
            )

        except Exception as e:
            logger.error(f"Error deactivating workflow {workflow_id}: {str(e)}")
            raise

    @staticmethod
    async def regenerate_workflow_steps(
        workflow_id: str,
        user_id: str,
        regeneration_reason: Optional[str] = None,
        force_different_tools: bool = True,
    ) -> Optional[Workflow]:
        """Regenerate steps for an existing workflow."""
        try:
            # Get the existing workflow
            workflow = await WorkflowService.get_workflow(workflow_id, user_id)
            if not workflow:
                return None

            # Generate new steps using the existing title and description
            steps_data = await WorkflowService._generate_steps_with_llm(
                workflow.description, workflow.title
            )

            # Update workflow with new steps
            result = await workflows_collection.find_one_and_update(
                {"_id": workflow_id, "user_id": user_id},
                {
                    "$set": {
                        "steps": steps_data,
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
                return_document=True,
            )

            if result:
                logger.info(
                    f"Regenerated {len(steps_data)} steps for workflow {workflow_id}"
                )
                return Workflow(**transform_doc(result))
            return None

        except Exception as e:
            logger.error(f"Error regenerating workflow steps {workflow_id}: {str(e)}")
            raise

    @staticmethod
    async def _generate_workflow_steps(workflow_id: str, user_id: str) -> None:
        """Generate workflow steps using LLM with structured output."""
        try:
            await workflows_collection.find_one_and_update(
                {"_id": workflow_id, "user_id": user_id},
                {
                    "$set": {
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
            )

            workflow = await WorkflowService.get_workflow(workflow_id, user_id)
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")

            # Generate steps using structured LLM output
            steps_data = await WorkflowService._generate_steps_with_llm(
                workflow.description, workflow.title
            )

            if steps_data:
                await workflows_collection.find_one_and_update(
                    {"_id": workflow_id, "user_id": user_id},
                    {
                        "$set": {
                            "steps": steps_data,
                            "updated_at": datetime.now(timezone.utc),
                        }
                    },
                )
                logger.info(
                    f"Generated {len(steps_data)} steps for workflow {workflow_id}"
                )
            else:
                await handle_workflow_error(
                    workflow_id,
                    user_id,
                    Exception("Failed to generate workflow steps"),
                )

        except Exception as e:
            logger.error(f"Error generating workflow steps for {workflow_id}: {str(e)}")
            await handle_workflow_error(workflow_id, user_id, e)

    @staticmethod
    async def _generate_steps_with_llm(description: str, title: str) -> list:
        """Generate workflow steps using LLM with structured output."""
        try:
            from pydantic import BaseModel, Field
            from langchain_core.output_parsers import PydanticOutputParser
            from langchain_core.prompts import PromptTemplate
            from app.langchain.llm.client import init_llm
            from app.langchain.tools.core.registry import tool_names

            # Define the structured output schema
            class WorkflowStep(BaseModel):
                id: str = Field(
                    description="Unique identifier for the step (e.g., 'step_1')"
                )
                title: str = Field(description="Clear, actionable title for the step")
                tool_name: str = Field(
                    description="Exact tool name from available tools"
                )
                tool_category: str = Field(
                    description="Category of the tool (mail, calendar, search, productivity, etc.)"
                )
                description: str = Field(
                    description="Detailed description of what this step accomplishes"
                )
                tool_inputs: dict = Field(
                    default_factory=dict, description="Expected inputs for the tool"
                )

            class WorkflowPlan(BaseModel):
                steps: list[WorkflowStep] = Field(
                    description="List of 4-7 actionable workflow steps",
                    min_length=4,
                    max_length=7,
                )

            # Create the parser
            parser = PydanticOutputParser(pydantic_object=WorkflowPlan)

            # Create prompt template
            prompt = PromptTemplate(
                template="""Create a practical workflow plan for this goal using ONLY the available tools listed below.

TITLE: {title}
DESCRIPTION: {description}

CRITICAL REQUIREMENTS:
1. Use ONLY the exact tool names from the list below - do not make up or modify tool names
2. Choose tools that are logically appropriate for the goal
3. Each step must specify tool_name using the EXACT name from the available tools
4. Consider the tool category when selecting appropriate tools
5. Create 4-7 actionable steps that logically break down this goal into executable tasks
6. Use practical and helpful tools that accomplish the goal, avoid unnecessary tools

JSON OUTPUT REQUIREMENTS:
- NEVER include comments (//) in the JSON output
- Use only valid JSON syntax with no explanatory comments
- Tool inputs should contain realistic example values, not placeholders
- All string values must be properly quoted
- No trailing commas or syntax errors

GOOD WORKFLOW EXAMPLES:
- "Plan vacation to Europe" → 1) web_search_tool (research destinations), 2) get_weather (check climate), 3) create_calendar_event (schedule trip dates)
- "Organize project emails" → 1) search_gmail_messages (find project emails), 2) create_gmail_label (create organization), 3) apply_labels_to_emails (organize them)
- "Prepare for client meeting" → 1) search_gmail_messages (find relevant emails), 2) web_search_tool (research client), 3) create_calendar_event (block preparation time)
- "Submit quarterly report" → 1) query_file (review previous reports), 2) generate_document (create new report), 3) create_reminder (set deadline reminder)

Available Tools: {tools}

{format_instructions}""",
                input_variables=["description", "title", "tools"],
                partial_variables={
                    "format_instructions": parser.get_format_instructions()
                },
            )

            # Initialize LLM
            llm = init_llm(streaming=False)

            # Create chain
            chain = prompt | llm | parser

            # Generate workflow plan
            result = await chain.ainvoke(
                {
                    "description": description,
                    "title": title,
                    "tools": ", ".join(tool_names),
                }
            )

            # Convert to list of dictionaries for storage
            steps_data = []
            for i, step in enumerate(result.steps, 1):
                step_dict = step.model_dump()
                step_dict["id"] = f"step_{i}"  # Ensure consistent ID format
                step_dict["order"] = i - 1  # Add order field (0-based)
                steps_data.append(step_dict)

            logger.info(f"Generated {len(steps_data)} workflow steps for: {title}")
            return steps_data

        except Exception as e:
            logger.error(f"Error in LLM workflow generation: {str(e)}")
            return []

    @staticmethod
    async def _queue_workflow_generation(workflow_id: str, user_id: str) -> None:
        """Queue workflow generation as a background task."""
        try:
            pool = await RedisPoolManager.get_pool()

            job = await pool.enqueue_job(
                "generate_workflow_steps", workflow_id, user_id
            )

            if job:
                logger.info(
                    f"Queued workflow generation for {workflow_id} with job ID {job.job_id}"
                )
            else:
                logger.error(f"Failed to queue workflow generation for {workflow_id}")
                await WorkflowService._generate_workflow_steps(workflow_id, user_id)

        except Exception as e:
            logger.error(
                f"Error queuing workflow generation for {workflow_id}: {str(e)}"
            )
            await WorkflowService._generate_workflow_steps(workflow_id, user_id)

    @staticmethod
    async def _queue_workflow_execution(
        workflow_id: str, user_id: str, context: Optional[dict] = None
    ) -> None:
        """Queue workflow execution as a background task."""
        try:
            pool = await RedisPoolManager.get_pool()

            job = await pool.enqueue_job(
                "process_workflow", workflow_id, user_id, context or {}
            )

            if job:
                logger.info(
                    f"Queued workflow execution for {workflow_id} with job ID {job.job_id}"
                )
            else:
                logger.error(f"Failed to queue workflow execution for {workflow_id}")

        except Exception as e:
            logger.error(
                f"Error queuing workflow execution for {workflow_id}: {str(e)}"
            )

    @staticmethod
    async def _schedule_workflow_execution(
        workflow_id: str, user_id: str, scheduled_at: datetime
    ) -> None:
        """Schedule workflow execution at a specific time using ARQ."""
        try:
            pool = await RedisPoolManager.get_pool()

            job = await pool.enqueue_job(
                "process_workflow",
                workflow_id,
                user_id,
                {},  # context
                _defer_until=scheduled_at,
            )

            if job:
                logger.info(
                    f"Scheduled workflow {workflow_id} for execution at {scheduled_at} with job ID {job.job_id}"
                )
            else:
                logger.error(f"Failed to schedule workflow execution for {workflow_id}")

        except Exception as e:
            logger.error(
                f"Error scheduling workflow execution for {workflow_id}: {str(e)}"
            )

    @staticmethod
    async def _cancel_scheduled_workflow_execution(workflow_id: str) -> None:
        """Cancel any pending scheduled executions for a workflow."""
        try:
            # Note: ARQ doesn't provide a direct way to cancel specific jobs by metadata
            # This is a limitation we'll accept for now
            # In a production system, you might want to track job IDs in the database
            logger.info(
                f"Scheduled execution cancellation requested for workflow {workflow_id}"
            )
            # TODO: Implement job cancellation when ARQ supports it better
        except Exception as e:
            logger.error(
                f"Error cancelling scheduled execution for {workflow_id}: {str(e)}"
            )
