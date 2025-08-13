import operator
from contextlib import asynccontextmanager
from typing import Annotated, List, Tuple

from app.config.loggers import chat_logger as logger
from app.langchain.llm.client import init_llm
from app.langchain.templates.mail_templates import (
    EMAIL_PROCESSING_PLAN_TEMPLATE,
    EMAIL_PROCESSING_REPLAN_TEMPLATE,
)
from app.langchain.tools.core.registry import ALWAYS_AVAILABLE_TOOLS, tools
from app.langchain.tools.core.retrieval import retrieve_tools
from app.models.mail_models import EmailProcessingPlan, EmailProcessingReplanResult
from langchain_core.exceptions import OutputParserException
from langchain_core.messages import AIMessageChunk
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.config import get_stream_writer
from langgraph.constants import END, START
from langgraph.graph import StateGraph
from langgraph.store.memory import InMemoryStore
from langgraph.types import RetryPolicy
from langgraph_bigtool import create_agent
from typing_extensions import TypedDict

llm = init_llm()

# Create output parsers for structured responses
email_plan_parser = PydanticOutputParser(pydantic_object=EmailProcessingPlan)
email_replan_parser = PydanticOutputParser(pydantic_object=EmailProcessingReplanResult)


# Define the state for plan-and-execute
class EmailPlanExecute(TypedDict):
    input: str  # The original email content
    plan: List[str]  # Current plan steps
    past_steps: Annotated[List[Tuple], operator.add]  # Completed steps with results
    response: str  # Final response


@asynccontextmanager
async def build_mail_processing_graph():
    """
    Build a plan-and-execute processing graph for handling user emails with LLM assistance.

    This graph is designed for scenarios where the LLM processes incoming user emails
    using a plan-and-execute pattern:
    1. First, creates a plan of steps needed to process the email
    2. Executes each step using available tools
    3. Re-plans based on execution results if needed
    4. Returns a final response

    The plan-and-execute pattern provides:
    - Explicit long-term planning for complex email processing
    - Step-by-step execution with tool usage
    - Ability to revise the plan based on intermediate results
    """
    # Register both regular and always available tools
    all_tools = tools + ALWAYS_AVAILABLE_TOOLS
    tool_registry = {tool.name: tool for tool in all_tools}

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
    )

    # Create store for tool discovery
    store = InMemoryStore(
        index={
            "embed": embeddings,
            "dims": 768,
            "fields": ["description"],
        }
    )

    # Store all tools for vector search
    for tool in all_tools:
        store.put(
            ("tools",),
            tool.name,
            {
                "description": f"{tool.name}: {tool.description}",
            },
        )

    # Create agent for tool execution
    agent_executor = create_agent(
        llm=llm,
        tool_registry=tool_registry,
        retrieve_tools_function=retrieve_tools,
    )

    # Planning prompt - use template from mail_templates
    planner_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", EMAIL_PROCESSING_PLAN_TEMPLATE.template),
            ("placeholder", "{messages}"),
        ]
    )

    planner = planner_prompt | llm | email_plan_parser

    # Re-planning prompt - use template from mail_templates
    replanner = EMAIL_PROCESSING_REPLAN_TEMPLATE | llm | email_replan_parser

    # Graph node functions
    async def plan_step(state: EmailPlanExecute):
        """Create initial plan for email processing"""
        try:
            result = await planner.ainvoke(
                {
                    "messages": [("user", state["input"])],
                    "format_instructions": email_plan_parser.get_format_instructions(),
                },
            )

            # result is now a structured EmailProcessingPlan object
            return {"plan": result.steps}
        except Exception as e:
            logger.error(f"Planning error: {e}")
            raise ValueError(
                "Failed to create email processing plan. Please try again later."
            )

    async def execute_step(state: EmailPlanExecute):
        """Execute the next step in the plan"""
        plan = state["plan"]
        plan_str = "\n".join(f"{i + 1}. {step}" for i, step in enumerate(plan))
        task = plan[0]
        task_formatted = f"""For the following email processing plan:
{plan_str}

You are tasked with executing step 1: {task}

Original email content: {state["input"]}"""

        try:
            writer = get_stream_writer()

            # Compile the agent executor if it's not already compiled
            compiled_agent = agent_executor.compile(checkpointer=InMemorySaver())

            # Stream the agent execution to capture tool events
            # The custom events will automatically propagate up through the graph
            agent_response_content = ""
            async for event in compiled_agent.astream(
                {"messages": [("user", task_formatted)]},
                stream_mode=["messages", "custom"],
            ):
                stream_mode, payload = event
                if stream_mode == "messages":
                    chunk, metadata = payload
                    if chunk is None:
                        continue

                    if isinstance(chunk, AIMessageChunk):
                        content = str(chunk.content)
                        if content:
                            agent_response_content += content

                elif stream_mode == "custom":
                    # Custom events automatically bubble up through LangGraph
                    logger.info(f"Tool event in execute_step: {payload}")
                    writer(payload)

            return {
                "past_steps": [(task, agent_response_content)],
            }
        except Exception as e:
            logger.error(f"Execution error: {e}")
            return {
                "past_steps": [(task, f"Error executing step: {str(e)}")],
            }

    async def replan_step(state: EmailPlanExecute):
        """Re-plan based on execution results"""
        try:
            # Convert state to proper format for replanner
            replanner_input = {
                "input": state["input"],
                "plan": state.get("plan", []),
                "past_steps": state.get("past_steps", []),
                "format_instructions": email_replan_parser.get_format_instructions(),
            }
            result = await replanner.ainvoke(replanner_input)

            # result is now a structured EmailProcessingReplanResult object
            if result.action == "complete":
                return {"response": result.response or "Email processing completed."}
            else:
                # Continue with remaining steps
                return {"plan": result.steps or []}

        except Exception as e:
            logger.error(f"Replanning error: {e}")
            return {"response": "Email processing completed with some errors."}

    def should_end(state: EmailPlanExecute):
        """Determine if we should end or continue executing"""
        if "response" in state and state["response"]:
            return END
        else:
            return "agent"

    # Create the state graph
    workflow = StateGraph(EmailPlanExecute)

    # Add nodes
    workflow.add_node(
        "planner",
        plan_step,
        retry_policy=RetryPolicy(
            retry_on=OutputParserException,
            max_attempts=2,
        ),
    )
    workflow.add_node("agent", execute_step)
    workflow.add_node("replan", replan_step)

    # Add edges
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "agent")
    workflow.add_edge("agent", "replan")
    workflow.add_conditional_edges(
        "replan",
        should_end,
        ["agent", END],
    )

    # Use an in-memory checkpointer for simplicity
    checkpointer = InMemorySaver()

    # Compile and yield the final graph
    graph = workflow.compile(checkpointer=checkpointer, store=store)

    print(graph.get_graph().draw_mermaid())

    yield graph
