import operator
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from dataclasses import dataclass
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
    ):
        self.config = config
        self.template_provider = template_provider
        self.llm = llm or init_llm()
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
        """Create initial plan for processing"""
        try:
            logger.info(f"Creating plan for {self.config.processing_name}")

            result = await self.planner.ainvoke(
                {
                    "messages": [("user", state["input"])],
                    "format_instructions": self.plan_parser.get_format_instructions(),
                }
            )

            logger.info(f"Plan created with {len(result.steps)} steps")
            return {"plan": result.steps}

        except Exception as e:
            logger.error(f"Planning error in {self.config.processing_name}: {e}")
            raise ValueError(
                f"Failed to create {self.config.processing_name} plan. Please try again later."
            )

    async def _execute_step(self, state: PlanExecuteState) -> Dict[str, Any]:
        """Execute the next step in the plan"""
        plan = state["plan"]
        if not plan:
            return {"past_steps": [("No steps", "Plan is empty")]}

        current_task = plan[0]
        formatted_task = self.template_provider.format_execution_task(
            current_task, plan, state["input"]
        )

        logger.info(f"Executing step: {current_task}")

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
            async for event in compiled_agent.astream(
                {"messages": [("user", formatted_task)]},
                stream_mode=["messages", "custom"],
            ):
                stream_mode, payload = event

                if stream_mode == "messages":
                    chunk, metadata = payload
                    if chunk and isinstance(chunk, AIMessageChunk):
                        content = str(chunk.content)
                        if content:
                            agent_response_content += content

                elif stream_mode == "custom":
                    logger.info(
                        f"Tool event in {self.config.processing_name}: {payload}"
                    )
                    writer(payload)

            logger.info(f"Step executed successfully: {current_task}")
            return {"past_steps": [(current_task, agent_response_content)]}

        except Exception as e:
            logger.error(f"Execution error in {self.config.processing_name}: {e}")
            return {"past_steps": [(current_task, f"Error executing step: {str(e)}")]}

    async def _replan(self, state: PlanExecuteState) -> Dict[str, Any]:
        """Re-plan based on execution results"""
        try:
            logger.info(f"Re-planning for {self.config.processing_name}")

            replanner_input = {
                "input": state["input"],
                "plan": state.get("plan", []),
                "past_steps": state.get("past_steps", []),
                "format_instructions": self.replan_parser.get_format_instructions(),
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

    def _create_processing_graph(self) -> StateGraph:
        """Create the processing state graph"""
        processing = StateGraph(PlanExecuteState)

        # Conditionally add nodes based on configuration
        if not self.config.skip_planning:
            processing.add_node(
                "planner",
                self._create_plan,
                retry_policy=RetryPolicy(
                    retry_on=OutputParserException,
                    max_attempts=self.config.max_retry_attempts,
                ),
            )

        processing.add_node("agent", self._execute_step)

        if not self.config.skip_replanning:
            processing.add_node("replan", self._replan)

        # Add edges based on configuration
        if not self.config.skip_planning:
            processing.add_edge(START, "planner")
            processing.add_edge("planner", "agent")
        else:
            processing.add_edge(START, "agent")

        if not self.config.skip_replanning:
            processing.add_edge("agent", "replan")
            processing.add_conditional_edges(
                "replan",
                self._should_end,
                ["agent", END],
            )
        else:
            processing.add_edge("agent", END)

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
