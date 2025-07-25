from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from app.config.loggers import chat_logger as logger
from app.db.mongodb.collections import workflow_collection
from app.langchain.core.graph_builder.build_plan_execute_graph import (
    PlanExecuteConfig,
    PlanExecuteProcessor,
    PlanExecuteState,
    PlanExecuteTemplateProvider,
)
from app.langchain.tools.core.registry import ALWAYS_AVAILABLE_TOOLS, tools
from app.models.workflow_models import (
    UpdateWorkflowRequest,
    WorkflowProcessingPlan,
    WorkflowProcessingReplanResult,
)
from bson import ObjectId
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate


class WorkflowTemplateProvider(PlanExecuteTemplateProvider):
    """Workflow-specific template provider"""

    def __init__(self):
        self.plan_model = WorkflowProcessingPlan
        self.replan_model = WorkflowProcessingReplanResult

    def get_plan_template(self) -> ChatPromptTemplate:
        plan_template = """For the given workflow instructions, create a detailed step-by-step plan to accomplish the task effectively.

IMPORTANT EXECUTION CONTEXT:
- Each step will be executed by an AI agent with access to various tools
- Each step should specify WHICH TOOL to use and HOW to use it
- Each step will have full visibility of ALL previous step outputs and results
- Each step will know its position in the overall plan (Step 1, Step 2, etc.)
- Design steps so they can build upon and reference outputs from previous steps

AVAILABLE TOOLS INCLUDE:
- web_search_tool: Search the internet for information
- create_google_doc: Create Google Documents
- send_email_tool: Send emails and notifications
- create_reminder_tool: Create scheduled reminders
- get_calendar_events: Retrieve calendar information
- And many other workflow automation tools

PLANNING GUIDELINES:
- Each step MUST specify a tool to use (e.g., "Use web_search_tool to find...")
- Do NOT create manual steps like "open browser" or "manually search"
- Make each step specific and actionable for an AI agent with tools
- Ensure steps can reference and build upon previous step outputs
- Do not add any superfluous steps
- The result of the final step should accomplish the workflow objective
- Make sure that each step has all the information needed - do not skip steps
- Consider how information flows between steps

EXAMPLE GOOD STEPS:
- "Use web_search_tool to search for latest news headlines from today"
- "Use create_google_doc to create a new document titled 'Daily News Summary'"
- "Use send_email_tool to notify stakeholders about the completed summary"

EXAMPLE BAD STEPS (DON'T DO THIS):
- "Open your web browser and search for news"
- "Manually review articles and take notes"
- "Save the document to your computer"

{format_instructions}"""

        return ChatPromptTemplate.from_messages(
            [
                ("system", plan_template),
                ("placeholder", "{messages}"),
            ]
        )

    def get_replan_template(self) -> ChatPromptTemplate:
        replan_template = """For the given workflow objective, update the plan based on execution results.

EXECUTION CONTEXT AWARENESS:
- Each step was executed by an AI agent with access to various tools
- Each step had visibility of all prior step outputs and results
- Steps were executed sequentially with accurate step numbering
- Each step was designed to build upon previous step outputs

REPLANNING GUIDELINES:
- Review the completed steps and their actual outputs carefully
- Consider how the outputs from completed steps affect remaining work
- Design remaining steps to leverage information from completed steps
- Each remaining step MUST specify a tool to use (e.g., "Use web_search_tool to...")
- Do NOT create manual steps - only tool-based automated steps
- Ensure new steps can reference and build upon the available outputs
- Make each remaining step specific and actionable for an AI agent with tools

Your objective was this:
{input}

Your original plan was this:
{plan}

You have currently done the following steps with their actual outputs:
{past_steps}

REPLANNING INSTRUCTIONS:
Based on the actual outputs from completed steps, update your plan accordingly.

If no more steps are needed and you can return the final result, set action to "complete" and provide the final response.

Otherwise, set action to "continue" and provide a list of remaining steps to be done.
- Only add steps to the plan that still NEED to be done
- Do not return previously completed steps as part of the plan
- Design new steps to leverage the outputs from completed steps
- Each step must specify which tool to use
- Ensure each step can reference previous outputs when relevant

{format_instructions}"""

        return ChatPromptTemplate.from_template(replan_template)

    def get_plan_parser(self) -> PydanticOutputParser:
        return PydanticOutputParser(pydantic_object=self.plan_model)

    def get_replan_parser(self) -> PydanticOutputParser:
        return PydanticOutputParser(pydantic_object=self.replan_model)

    def format_execution_task(
        self, task: str, plan: List[str], original_input: str
    ) -> str:
        """
        Format the execution task prompt with the current task, plan, and original input.

        Note: Past steps context will be automatically added by the base PlanExecuteProcessor.
        """
        # Format the full plan with step numbers
        plan_str = "\n".join(f"{i + 1}. {step}" for i, step in enumerate(plan))

        return f"""WORKFLOW EXECUTION CONTEXT:
You are an AI agent executing a specific step in a larger workflow plan.

COMPLETE WORKFLOW PLAN:
{plan_str}

STEP EXECUTION INSTRUCTIONS:
You are tasked with executing step 1: {task}

EXECUTION GUIDELINES:
- Focus ONLY on executing this specific step
- Do not attempt to execute future steps from the plan
- Use any outputs from previous steps (if provided) to inform your current execution
- ALWAYS provide a detailed summary of what you accomplished in this step
- Your response will be shared with future steps as context, so make it clear and structured
- Be thorough but stay within the scope of your assigned step
- If you need information that should come from a previous step, note this clearly

OUTPUT REQUIREMENTS:
- Always provide a comprehensive summary of your actions and results
- Include any data, information, or outputs generated during this step
- Clearly state what was accomplished and any relevant details for future steps
- If using tools, summarize what the tools returned and how it relates to the workflow goal

Original workflow instructions: {original_input}"""


class WorkflowStorage:
    """
    Handles storage and retrieval of workflow plans and results.

    Note: This class is available for future advanced workflow persistence features,
    but is not used in the current factory pattern implementation to maintain
    consistency with the GraphManager approach used throughout the system.
    """

    @staticmethod
    async def store_workflow_plan(
        workflow_plan: WorkflowProcessingPlan,
        workflow_id: Optional[str] = None,
    ):
        """
        Store workflow plan in database by updating an existing workflow.
        If workflow_id is provided in metadata, updates that workflow; otherwise creates new one.
        """
        try:
            # Update existing workflow with plan
            update_data: dict = {
                "payload.plan": workflow_plan.model_dump(),
            }
            update_data = UpdateWorkflowRequest(
                **update_data,
            ).model_dump(by_alias=True, exclude_unset=True)

            # Update the workflow
            await workflow_collection.update_one(
                {"_id": ObjectId(workflow_id)}, {"$set": update_data}
            )

            logger.info(
                f"Updated workflow plan for existing workflow ID: {workflow_id}"
            )

        except Exception as e:
            logger.error(f"Failed to store workflow plan: {e}")
            raise

    @staticmethod
    async def get_workflow_plan(workflow_id: str) -> Optional[WorkflowProcessingPlan]:
        """Retrieve workflow plan from database"""
        try:
            doc = await workflow_collection.find_one({"_id": ObjectId(workflow_id)})
            if doc and "workflow_plan" in doc:
                return WorkflowProcessingPlan(**doc["workflow_plan"])
            return None

        except Exception as e:
            logger.error(f"Failed to retrieve workflow plan {workflow_id}: {e}")
            return None

    @staticmethod
    async def handle_workflow_persistence(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle workflow persistence based on state metadata.

        This utility function can be used during graph execution to conditionally
        store or retrieve workflow plans based on runtime configuration.

        Args:
            state: The workflow state including metadata (as dict)

        Returns:
            Updated state dict with any retrieved plan
        """
        metadata = state.get("metadata", {})
        workflow_id = metadata.get("workflow_id")
        persist_workflow = metadata.get("persist_workflow", True)
        force_new_plan = metadata.get("force_new_plan", False)

        # If workflow persistence is disabled, return state as-is
        if not persist_workflow:
            return state

        # Check if we should try to retrieve an existing plan
        if workflow_id and not force_new_plan and not state.get("plan"):
            try:
                existing_plan = await WorkflowStorage.get_workflow_plan(workflow_id)
                if existing_plan and existing_plan.steps:
                    logger.info(f"Retrieved existing plan for workflow {workflow_id}")
                    # Return updated state with retrieved plan
                    return {**state, "plan": existing_plan.steps}
            except Exception as e:
                logger.error(f"Error retrieving plan for workflow {workflow_id}: {e}")

        return state


# Workflow processing graph factory function
@asynccontextmanager
async def build_workflow_processing_graph(
    exclude_tools: Optional[List[str]] = None,
):
    """
    Factory function to build a workflow processing graph with conditional edges.

    This function creates a workflow processing graph that:
    1. Can be registered in the GraphManager for reuse
    2. Has runtime-configurable execution paths via conditional edges
    3. Accepts control parameters in the state metadata
    4. Integrates with WorkflowStorage for persistence

    The graph will check these keys in state["metadata"]:
    - skip_planning: If True, bypasses planning and uses existing plan
    - skip_replanning: If True, skips replanning after execution
    - persist_workflow: If True, saves workflow plan to database (default: True)
    - force_new_plan: If True, creates a new plan even if one exists

    Args:
        exclude_tools: Tools to exclude beyond create_workflow_tool
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

    # Create base configuration - control flags are now managed via state
    config = PlanExecuteConfig(
        processing_name="Workflow Processing",
        plan_template="",  # Will be set by template provider
        replan_template="",  # Will be set by template provider
    )

    # Create template provider
    template_provider = WorkflowTemplateProvider()

    # Create a WorkflowProcessor class that extends PlanExecuteProcessor
    class WorkflowProcessor(PlanExecuteProcessor):
        """
        Custom workflow processor that extends the PlanExecuteProcessor with workflow-specific
        functionality like persistence and workflow ID tracking.
        """

        async def _create_plan(self, state: PlanExecuteState) -> Dict[str, Any]:
            """Override _create_plan to add workflow persistence"""
            # Convert state to dict for persistence handling
            state_dict = dict(state)

            # First try to load from persistence
            updated_state_dict = await WorkflowStorage.handle_workflow_persistence(
                state_dict
            )

            # If we already have a plan from persistence, use it
            if "plan" in updated_state_dict and updated_state_dict["plan"]:
                logger.info("Using persisted workflow plan")
                return {"plan": updated_state_dict["plan"]}

            # Otherwise create a new plan using the parent method
            plan_result = await super()._create_plan(state)

            # Store the new plan if needed
            metadata = state.get("metadata", {})
            workflow_id = metadata.get("workflow_id")

            if not workflow_id or not isinstance(workflow_id, str):
                logger.warning(
                    "No valid workflow_id found in metadata, skipping plan persistence"
                )
                return plan_result

            if metadata.get("persist_workflow", True) and "plan" in plan_result:
                try:
                    # Create workflow plan with required title
                    workflow_title = metadata.get("title", "Workflow Plan")
                    instructions = metadata.get("instructions", state.get("input", ""))

                    # Add instructions to metadata
                    if "instructions" not in metadata and instructions:
                        metadata["instructions"] = instructions

                    # Add title to metadata if not present
                    if "title" not in metadata:
                        metadata["title"] = workflow_title

                    workflow_plan = WorkflowProcessingPlan(
                        steps=plan_result["plan"],
                    )

                    # Store workflow plan in existing workflow document or create new

                    workflow_id = await WorkflowStorage.store_workflow_plan(
                        workflow_plan=workflow_plan,
                    )

                    # Add workflow_id to metadata
                    if "metadata" not in plan_result:
                        plan_result["metadata"] = {}
                    plan_result["metadata"]["workflow_id"] = workflow_id

                    logger.info(f"Stored new workflow plan with ID: {workflow_id}")
                except Exception as e:
                    logger.error(f"Failed to persist workflow plan: {e}")

            return plan_result

    # Create custom processor with persistence support
    processor = WorkflowProcessor(
        config=config,
        template_provider=template_provider,
        available_tools=available_tools,
        model="gpt-4o",
    )

    # Build and yield graph
    async with processor.build_graph() as graph:
        logger.info(
            "Workflow processing graph built with conditional edges for runtime configuration"
        )
        yield graph
