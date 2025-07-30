from contextlib import asynccontextmanager
from typing import List, Optional

from langchain_core.language_models import LanguageModelLike
from langchain_huggingface import HuggingFaceEmbeddings
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.constants import END
from langgraph.store.memory import InMemoryStore
from langgraph_bigtool import create_agent

from app.config.settings import settings
from app.langchain.llm.client import init_llm

# from app.langchain.tools.core.injectors import (
# inject_deep_research_tool_call,
# inject_web_search_tool_call,
# should_call_tool,
# )
from app.langchain.tools.core.registry import ALWAYS_AVAILABLE_TOOLS, tools
from app.langchain.tools.core.retrieval import retrieve_tools
from app.langchain.core.nodes.follow_up_actions_node import follow_up_actions_node


llm = init_llm()


@asynccontextmanager
async def build_graph(
    chat_llm: Optional[LanguageModelLike] = None,
    exclude_tools: List[str] = [],
    in_memory_checkpointer: bool = False,
):
    """Construct and compile the state graph."""
    # Register both regular and always available tools
    all_tools = tools + ALWAYS_AVAILABLE_TOOLS

    # Filter out any tools that should be excluded
    if exclude_tools:
        all_tools = [tool for tool in all_tools if tool.name not in exclude_tools]

    tool_registry = {tool.name: tool for tool in all_tools}

    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # Create store for tool discovery
    store = InMemoryStore(
        index={
            "embed": embeddings,
            "dims": 384,
            "fields": ["description"],
        }
    )

    # Store all tools for vector search (both regular and always available)
    for tool in all_tools:
        store.put(
            ("tools",),
            tool.name,
            {
                "description": f"{tool.name}: {tool.description}",
            },
        )

    # Create agent with custom tool retrieval logic
    builder = create_agent(
        llm=chat_llm if chat_llm else llm,
        tool_registry=tool_registry,
        retrieve_tools_function=retrieve_tools,
    )

    # Injector nodes add tool calls to the state messages
    builder.add_node("follow_up_actions", follow_up_actions_node)
    # builder.add_node("inject_deep_research", inject_deep_research_tool_call)

    # Conditional edges from chatbot to injector nodes or end
    # builder.add_conditional_edges(
    #     START,
    #     should_call_tool,
    #     {
    #         # call_1, call_2, and call_chatbot are the return values from should_call_tool
    #         # "return_value" : "name of node to call"
    #         "call_1": "inject_web_search",
    #         "call_2": "inject_deep_research",
    #         "call_chatbot": "agent",
    #     },
    # )

    # After injecting tool call, route to shared tools node to execute
    # builder.add_edge("inject_web_search", "tools")
    builder.add_edge("agent", "follow_up_actions")
    builder.add_edge("follow_up_actions", END)

    if in_memory_checkpointer:
        # Use in-memory checkpointer for testing or simple use cases
        in_memory_checkpointer_instance = InMemorySaver()
        # Setup the checkpointer
        graph = builder.compile(
            checkpointer=in_memory_checkpointer_instance,  # type: ignore[call-arg]
            store=store,
        )
        print(graph.get_graph().draw_mermaid())
        yield graph
    else:
        async with AsyncPostgresSaver.from_conn_string(
            settings.POSTGRES_URL
        ) as postgres_checkpointer:
            await postgres_checkpointer.setup()
            graph = builder.compile(checkpointer=postgres_checkpointer, store=store)
            print(graph.get_graph().draw_mermaid())
            yield graph
