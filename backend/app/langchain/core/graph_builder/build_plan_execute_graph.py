import operator
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Annotated, Any, Dict, Generic, List, Optional, Tuple, TypeVar

from app.config.loggers import chat_logger as logger
from app.langchain.llm.client import init_llm
from app.langchain.tools.core.registry import ALWAYS_AVAILABLE_TOOLS, tools
from app.langchain.tools.core.retrieval import retrieve_tools
from langchain_core.exceptions import OutputParserException
from langchain_core.messages import AIMessageChunk
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.config import get_stream_writer
from langgraph.constants import END, START
from langgraph.graph import StateGraph
from langgraph.store.memory import InMemoryStore
from langgraph.types import RetryPolicy
from langgraph_bigtool import create_agent
from pydantic import BaseModel
from typing_extensions import TypedDict

# Generic types for workflow processing
T = TypeVar("T", bound=BaseModel)  # For plan objects
R = TypeVar("R", bound=BaseModel)  # For replan result objects


@dataclass
class PlanExecuteConfig:
    """Configuration for plan-and-execute processing"""

    processing_name: str
    plan_template: str
    replan_template: str
    embeddings_model: str = "all-MiniLM-L6-v2"
    embeddings_dims: int = 384
    max_retry_attempts: int = 2
    skip_planning: bool = False  # Skip planning and use provided plan
    skip_replanning: bool = False  # Skip replanning after execution


class PlanExecuteState(TypedDict):
    """Base state for any plan-and-execute processing"""

    input: str  # The original input content
    plan: List[str]  # Current plan steps
    past_steps: Annotated[
        List[Tuple[str, str]], operator.add
    ]  # Completed steps with results
    response: str  # Final response
    metadata: Dict[str, Any]  # Additional processing-specific data


class PlanExecuteTemplateProvider(ABC):
    """Abstract base class for providing processing-specific templates and parsers"""

    @abstractmethod
    def get_plan_template(self) -> ChatPromptTemplate:
        """Return the planning prompt template"""
        pass

    @abstractmethod
    def get_replan_template(self) -> ChatPromptTemplate:
        """Return the re-planning prompt template"""
        pass

    @abstractmethod
    def get_plan_parser(self) -> PydanticOutputParser:
        """Return the parser for plan objects"""
        pass

    @abstractmethod
    def get_replan_parser(self) -> PydanticOutputParser:
        """Return the parser for replan result objects"""
        pass

    @abstractmethod
    def format_execution_task(
        self, task: str, plan: List[str], original_input: str
    ) -> str:
        """Format the task for execution"""
        pass


class PlanExecuteProcessor(Generic[T, R]):
    """
    Generic plan-and-execute processor that handles plan-and-execute pattern for any type of processing.

    This processor provides:
    - Explicit long-term planning for complex processing tasks
    - Step-by-step execution with tool usage
    - Ability to revise the plan based on intermediate results
    - Structured streaming of execution events
    - Option to skip planning (use provided plan) or replanning
    """

    def __init__(
        self,
        config: PlanExecuteConfig,
        template_provider: PlanExecuteTemplateProvider,
        llm=None,
        available_tools: Optional[List] = None,
        model: Optional[str] = None,
    ):
        self.config = config
        self.template_provider = template_provider
        self.llm = llm or init_llm(model=model)
        self.available_tools = available_tools or (tools + ALWAYS_AVAILABLE_TOOLS)

        # Initialize components
        self._setup_tools()
        self._setup_parsers()
        self._setup_prompts()

    def _setup_tools(self):
        """Set up tool registry and embeddings store"""
        self.tool_registry = {tool.name: tool for tool in self.available_tools}

        # Set up embeddings and store
        self.embeddings = HuggingFaceEmbeddings(model_name=self.config.embeddings_model)
        self.store = InMemoryStore(
            index={
                "embed": self.embeddings,
                "dims": self.config.embeddings_dims,
                "fields": ["description"],
            }
        )

        # Store all tools for vector search
        for tool in self.available_tools:
            self.store.put(
                ("tools",),
                tool.name,
                {"description": f"{tool.name}: {tool.description}"},
            )

    def _setup_parsers(self):
        """Set up output parsers"""
        self.plan_parser = self.template_provider.get_plan_parser()
        self.replan_parser = self.template_provider.get_replan_parser()

    def _setup_prompts(self):
        """Set up prompt templates"""
        self.planner = (
            self.template_provider.get_plan_template() | self.llm | self.plan_parser
        )
        self.replanner = (
            self.template_provider.get_replan_template() | self.llm | self.replan_parser
        )

    async def _create_plan(self, state: PlanExecuteState) -> Dict[str, Any]:
        """
        Create initial plan for processing, with support for persistence.

        Subclasses can implement their own persistence mechanisms by overriding
        this method or by handling persistence in a wrapper function.
        """
        try:
            logger.info(f"Creating plan for {self.config.processing_name}")

            # Check if a plan already exists in the state
            if state.get("plan") and len(state["plan"]) > 0:
                logger.info(f"Using existing plan with {len(state['plan'])} steps")
                return {"plan": state["plan"]}  # Return dict with existing plan

            # Create a new plan
            result = await self.planner.ainvoke(
                {
                    "messages": [("user", state["input"])],
                    "format_instructions": self.plan_parser.get_format_instructions(),
                }
            )

            logger.info(f"Plan created with {len(result.steps)} steps")

            # Store plan details in metadata for possible persistence
            metadata = state.get("metadata", {})
            metadata["plan_created_at"] = datetime.now(timezone.utc).isoformat()

            return {"plan": result.steps, "metadata": metadata}

        except Exception as e:
            logger.error(f"Planning error in {self.config.processing_name}: {e}")
            raise ValueError(
                f"Failed to create {self.config.processing_name} plan. Please try again later."
            )

    async def _execute_step(self, state: PlanExecuteState) -> Dict[str, Any]:
        """
        Execute the next step in the plan and advance the plan.

        This method executes the first step in the current plan and then
        removes it from the plan, allowing the next step to be executed
        in the next iteration.
        """
        plan = state["plan"]
        if not plan:
            return {"past_steps": [("No steps", "Plan is empty")], "plan": []}

        current_task = plan[0]
        past_steps = state.get("past_steps", [])

        # Get the base formatted task from the template provider
        base_formatted_task = self.template_provider.format_execution_task(
            current_task, plan, state["input"]
        )

        # Enhance the formatted task with past steps context
        past_steps_str = ""
        if past_steps and len(past_steps) > 0:
            past_steps_str = "\n\nPREVIOUS STEPS COMPLETED:\n"
            for idx, (step_task, step_result) in enumerate(past_steps):
                past_steps_str += f"Step {idx + 1}: {step_task}\n"
                past_steps_str += f"Output: {step_result}\n"
                past_steps_str += "---\n"

        # Calculate current step number and enhance the task
        current_step_number = len(past_steps) + 1
        formatted_task = base_formatted_task

        # Insert past steps context and update step numbering
        if past_steps_str:
            # Insert past steps context before the step execution instructions
            formatted_task = formatted_task.replace(
                "STEP EXECUTION INSTRUCTIONS:",
                f"{past_steps_str}STEP EXECUTION INSTRUCTIONS:",
            ).replace(
                "You are tasked with",
                "Based on the previous steps above, you are tasked with",
            )

        # Update step numbering to be accurate
        formatted_task = formatted_task.replace(
            "executing step 1:", f"executing step {current_step_number}:"
        ).replace("step 1:", f"step {current_step_number}:")

        # Add additional guidance about focusing on current step
        if "EXECUTION GUIDELINES:" not in formatted_task:
            formatted_task += "\n\nADDITIONAL GUIDANCE: Focus ONLY on executing this specific step. Do not attempt to execute future steps. Use the outputs from previous steps when relevant to inform your execution of the current step. Your response will be shared with future steps, so make it clear and structured."

        logger.info(f"Executing step {current_step_number}: {current_task}")
        if past_steps:
            logger.info(f"With context from {len(past_steps)} previous steps")

        try:
            # Create agent executor
            agent_executor = create_agent(
                llm=self.llm,
                tool_registry=self.tool_registry,
                retrieve_tools_function=retrieve_tools,
            )

            compiled_agent = agent_executor.compile(checkpointer=InMemorySaver())
            writer = get_stream_writer()

            # Stream the agent execution
            agent_response_content = ""
            tool_calls_made = False

            async for event in compiled_agent.astream(
                {"messages": [("user", formatted_task)]},
                stream_mode=["messages", "custom"],
            ):
                stream_mode, payload = event

                if stream_mode == "messages":
                    # Handle different payload structures from langgraph_bigtool
                    if isinstance(payload, tuple) and len(payload) == 2:
                        chunk, metadata = payload
                    else:
                        chunk = payload

                    if chunk and isinstance(chunk, AIMessageChunk):
                        content = str(chunk.content)
                        if content and content.strip():
                            agent_response_content += content

                elif stream_mode == "custom":
                    logger.info(
                        f"Tool event in {self.config.processing_name}: {payload}"
                    )
                    tool_calls_made = True
                    writer(payload)

            # Ensure we have some output even if streaming didn't capture everything
            if not agent_response_content.strip():
                logger.warning(
                    f"No content captured from agent response for step: {current_task}"
                )
                if tool_calls_made:
                    agent_response_content = f"Step {current_step_number} completed: {current_task}\n\nTool calls were made during this step. The step was executed successfully using the available tools."
                else:
                    agent_response_content = f"Step {current_step_number} completed: {current_task}\n\nThis step was processed but no detailed output was captured."

            logger.info(f"Step executed successfully: {current_task}")
            logger.info(f"Agent response length: {len(agent_response_content)}")

            # Remove the completed step from the plan and add it to past_steps
            remaining_plan = plan[1:] if len(plan) > 1 else []
            logger.info(f"Remaining steps in plan: {len(remaining_plan)}")

            # Return only the NEW step (not the accumulated list) due to operator.add
            return {
                "past_steps": [(current_task, agent_response_content)],
                "plan": remaining_plan,
            }

        except Exception as e:
            logger.error(f"Execution error in {self.config.processing_name}: {e}")

            # Return only the NEW step with error (not the accumulated list) due to operator.add
            remaining_plan = plan[1:] if len(plan) > 1 else []
            return {
                "past_steps": [(current_task, f"Error executing step: {str(e)}")],
                "plan": remaining_plan,
            }

    async def _replan(self, state: PlanExecuteState) -> Dict[str, Any]:
        """Re-plan based on execution results"""
        try:
            logger.info(f"Re-planning for {self.config.processing_name}")

            # TODO: Add error or something to indicate replan is needed
            replanner_input = {
                "input": state["input"],
                "plan": state.get("plan", []),
                "past_steps": state.get("past_steps", []),
                "format_instructions": self.replan_parser.get_format_instructions()
                + """
\nNote: In output schema `description` and `properties` are for your understanding only.
\nThey are not part of the output schema.
""",
            }

            result = await self.replanner.ainvoke(replanner_input)

            if result.action == "complete":
                logger.info(f"Processing {self.config.processing_name} completed")
                return {
                    "response": result.response
                    or f"{self.config.processing_name} completed."
                }
            else:
                logger.info(
                    f"Continuing with {len(result.steps or [])} remaining steps"
                )
                return {"plan": result.steps or []}

        except Exception as e:
            logger.error(f"Replanning error in {self.config.processing_name}: {e}")
            return {
                "response": f"{self.config.processing_name} completed with some errors."
            }

    def _should_end(self, state: PlanExecuteState) -> str:
        """Determine if processing should end or continue"""
        if "response" in state and state["response"]:
            return END
        return "agent"

    def _should_skip_planning(self, state: PlanExecuteState) -> str:
        """Determine if planning should be skipped based on state"""
        # Check if skip_planning is explicitly set in metadata
        metadata = state.get("metadata", {})
        if metadata.get("skip_planning", False) or len(state.get("plan", [])) > 0:
            logger.info(
                "Skipping planning phase due to runtime configuration or existing plan"
            )
            return "agent"
        return "planner"

    def _should_skip_replanning(self, state: PlanExecuteState) -> str:
        """Determine if replanning should be skipped based on state"""
        # Check if skip_replanning is explicitly set in metadata
        metadata = state.get("metadata", {})
        if metadata.get("skip_replanning", False):
            logger.info("Skipping replanning phase due to runtime configuration")
            return END
        return "replan"

    def _has_more_steps(self, state: PlanExecuteState) -> str:
        """
        Determine which state to transition to after executing a step.
        Check if there are more steps to execute in the plan.
        If there are steps remaining in the plan and skipping replanning,
        route back to agent.
        Otherwise, determine if we should go to replanning or end based on configuration.
        """
        plan = state.get("plan", [])
        metadata = state.get("metadata", {})

        if plan:
            logger.info(f"Plan has {len(plan)} more steps to execute")
            if metadata.get("skip_replanning", False):
                return "agent"
            return "replan"
        logger.info("No more steps to execute - END")
        return END

    def _create_processing_graph(self) -> StateGraph:
        """
        Create the processing state graph with conditional edges for runtime configuration.

        This allows the graph to be configured at runtime through state parameters rather than
        requiring different graph instances for different configurations.
        """
        processing = StateGraph(PlanExecuteState)

        # Always add all nodes, but conditionally route between them
        processing.add_node(
            "planner",
            self._create_plan,
            retry_policy=RetryPolicy(
                retry_on=OutputParserException,
                max_attempts=self.config.max_retry_attempts,
            ),
        )

        processing.add_node("agent", self._execute_step)
        processing.add_node(
            "replan",
            self._replan,
            retry_policy=RetryPolicy(
                retry_on=OutputParserException,
                max_attempts=self.config.max_retry_attempts,
            ),
        )

        # Add conditional edges for planning
        processing.add_conditional_edges(
            START,
            self._should_skip_planning,
            {
                "planner": "planner",  # Go to planner if not skipping
                "agent": "agent",  # Skip to agent if skipping planning
            },
        )

        # Connect planner to agent
        processing.add_edge("planner", "agent")

        # After executing a step, check if there are more steps to execute
        processing.add_conditional_edges(
            "agent",
            self._has_more_steps,
            {
                "agent": "agent",  # Loop back to agent if more steps and skipping replanning
                "replan": "replan",  # Go to replan if not skipping replanning
                END: END,  # End if no more steps and skipping replanning
            },
        )

        # Connect replan to either agent or end based on result
        processing.add_conditional_edges(
            "replan",
            self._should_end,
            ["agent", END],
        )

        return processing

    @asynccontextmanager
    async def build_graph(self):
        """
        Build and yield the compiled processing graph.

        Yields:
            Compiled StateGraph ready for execution
        """
        try:
            processing = self._create_processing_graph()
            checkpointer = InMemorySaver()

            # Compile the graph
            graph = processing.compile(checkpointer=checkpointer, store=self.store)

            # Log the graph structure
            logger.info(
                f"Built {self.config.processing_name} Graph (Plan-and-Execute):"
            )
            print(f"\n{self.config.processing_name} Graph Structure:")
            print(graph.get_graph().draw_mermaid())

            yield graph

        except Exception as e:
            logger.error(f"Failed to build {self.config.processing_name} graph: {e}")
            raise
