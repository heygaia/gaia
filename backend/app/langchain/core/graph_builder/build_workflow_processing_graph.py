from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.config.loggers import chat_logger as logger
from app.db.mongodb.collections import workflow_collection
from app.langchain.core.graph_builder.build_plan_execute_graph import (
    PlanExecuteConfig,
    PlanExecuteProcessor,
    PlanExecuteTemplateProvider,
)
from app.langchain.tools.core.registry import ALWAYS_AVAILABLE_TOOLS, tools
from app.models.todo_workflow_models import WorkflowPlan
from bson import ObjectId
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate


class WorkflowTemplateProvider(PlanExecuteTemplateProvider):
    """Workflow-specific template provider"""

    def __init__(self):
        # Import workflow-specific models
        from app.models.todo_workflow_models import WorkflowPlan

        self.plan_model = WorkflowPlan
        # For now, we'll use the same model for replanning
        self.replan_model = WorkflowPlan

    def get_plan_template(self) -> ChatPromptTemplate:
        plan_template = """For the given workflow instructions, create a detailed step-by-step plan to accomplish the task effectively.
This plan should involve individual steps that can be executed using available tools such as:
- Searching for information
- Creating tasks or reminders
- Sending emails or notifications
- Managing calendar events
- Working with documents
- Any other relevant workflow actions

Do not add any superfluous steps. The result of the final step should accomplish the workflow objective.
Make sure that each step has all the information needed - do not skip steps.

{format_instructions}"""

        return ChatPromptTemplate.from_messages(
            [
                ("system", plan_template),
                ("placeholder", "{messages}"),
            ]
        )

    def get_replan_template(self) -> ChatPromptTemplate:
        replan_template = """For the given workflow objective, update the plan based on execution results.
This plan should involve individual tasks that can be executed using available tools to properly complete the workflow.
Do not add any superfluous steps. The result of the final step should accomplish the workflow objective.
Make sure that each step has all the information needed - do not skip steps.

Your objective was this:
{input}

Your original plan was this:
{plan}

You have currently done the following steps:
{past_steps}

Update your plan accordingly. If no more steps are needed and you can return the final result, set action to "complete" and provide the final response.
Otherwise, set action to "continue" and provide a list of remaining steps to be done. Only add steps to the plan that still NEED to be done.
Do not return previously done steps as part of the plan.

{format_instructions}"""

        return ChatPromptTemplate.from_template(replan_template)

    def get_plan_parser(self) -> PydanticOutputParser:
        return PydanticOutputParser(pydantic_object=self.plan_model)

    def get_replan_parser(self) -> PydanticOutputParser:
        return PydanticOutputParser(pydantic_object=self.replan_model)

    def format_execution_task(
        self, task: str, plan: List[str], original_input: str
    ) -> str:
        plan_str = "\n".join(f"{i + 1}. {step}" for i, step in enumerate(plan))
        return f"""For the following workflow plan:
{plan_str}

You are tasked with executing step 1: {task}

Original workflow instructions: {original_input}"""


class WorkflowStorage:
    """Handles storage and retrieval of workflow plans and results"""

    @staticmethod
    async def store_workflow_plan(
        workflow_plan: WorkflowPlan,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Store workflow plan in database and return workflow_id"""
        try:
            workflow_doc = {
                "user_id": user_id,
                "workflow_plan": workflow_plan.model_dump(),
                "status": "planned",
                "created_at": datetime.now(timezone.utc),
                "metadata": metadata or {},
            }

            result = await workflow_collection.insert_one(workflow_doc)
            workflow_id = str(result.inserted_id)

            logger.info(f"Stored workflow plan with ID: {workflow_id}")
            return workflow_id

        except Exception as e:
            logger.error(f"Failed to store workflow plan: {e}")
            raise

    @staticmethod
    async def get_workflow_plan(workflow_id: str) -> Optional[WorkflowPlan]:
        """Retrieve workflow plan from database"""
        try:
            doc = await workflow_collection.find_one({"_id": ObjectId(workflow_id)})
            if doc and "workflow_plan" in doc:
                return WorkflowPlan(**doc["workflow_plan"])
            return None

        except Exception as e:
            logger.error(f"Failed to retrieve workflow plan {workflow_id}: {e}")
            return None

    @staticmethod
    async def update_workflow_status(
        workflow_id: str, status: str, results: Optional[List[Dict[str, Any]]] = None
    ):
        """Update workflow status and results in database"""
        try:
            update_data = {"status": status, "updated_at": datetime.now(timezone.utc)}

            if results:
                update_data["results"] = results

            await workflow_collection.update_one(
                {"_id": ObjectId(workflow_id)}, {"$set": update_data}
            )

            logger.info(f"Updated workflow {workflow_id} status to {status}")

        except Exception as e:
            logger.error(f"Failed to update workflow status {workflow_id}: {e}")


@asynccontextmanager
async def build_workflow_processing_graph(
    skip_planning: bool = False,
    skip_replanning: bool = False,
    exclude_tools: Optional[List[str]] = None,
):
    """
    Build a workflow processing graph that can:
    1. Generate plans for workflows using LLM (optional - can be skipped)
    2. Execute workflows using the plan-and-execute pattern
    3. Store workflow plans and results in database
    4. Exclude create_workflow tool to prevent recursive workflow creation

    Args:
        skip_planning: If True, expects a pre-existing plan in the state
        skip_replanning: If True, will not replan after execution
        exclude_tools: List of tool names to exclude (create_workflow_tool is always excluded)
    """
    # Always exclude create_workflow_tool to prevent recursive workflow creation
    excluded_tools = ["create_workflow_tool"]
    if exclude_tools:
        excluded_tools.extend(exclude_tools)

    # Filter out excluded tools
    available_tools = [
        tool
        for tool in (tools + ALWAYS_AVAILABLE_TOOLS)
        if tool.name not in excluded_tools
    ]

    # Create configuration
    config = PlanExecuteConfig(
        processing_name="Workflow Processing",
        plan_template="",  # Will be set by template provider
        replan_template="",  # Will be set by template provider
        skip_planning=skip_planning,
        skip_replanning=skip_replanning,
    )

    # Create template provider
    template_provider = WorkflowTemplateProvider()

    # Create processor with filtered tools
    processor: PlanExecuteProcessor = PlanExecuteProcessor(
        config=config,
        template_provider=template_provider,
        available_tools=available_tools,
    )

    # Build and yield graph
    async with processor.build_graph() as graph:
        logger.info(
            f"Workflow processing graph built (skip_planning={skip_planning}, skip_replanning={skip_replanning})"
        )
        yield graph
