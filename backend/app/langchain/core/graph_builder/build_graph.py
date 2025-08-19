from contextlib import asynccontextmanager
from typing import Optional

from app.langchain.core.graph_builder.checkpointer_manager import (
    checkpointer_manager,
)
from app.langchain.core.nodes.follow_up_actions_node import follow_up_actions_node
from app.langchain.llm.client import init_llm
from app.langchain.tools.core.retrieval import get_retrieve_tools_function
from app.langchain.tools.core.store import get_tools_store
from langchain_core.language_models import LanguageModelLike
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import END
from langgraph_bigtool import create_agent

llm = init_llm()


@asynccontextmanager
async def build_graph(
    chat_llm: Optional[LanguageModelLike] = None,
    in_memory_checkpointer: bool = False,
):
    """Construct and compile the state graph."""
    # Lazy import to avoid circular dependency
    from app.langchain.tools.core.registry import tool_registry

    store = get_tools_store()

    # Create agent with custom tool retrieval logic
    builder = create_agent(
        llm=chat_llm if chat_llm else llm,
        tool_registry=tool_registry.get_tool_registry(),
        retrieve_tools_function=get_retrieve_tools_function(tool_space="general"),
    )

    # Injector nodes add tool calls to the state messages
    builder.add_node("follow_up_actions", follow_up_actions_node)  # type: ignore[call-arg]
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
        postgres_checkpointer = checkpointer_manager.get_checkpointer()
        graph = builder.compile(checkpointer=postgres_checkpointer, store=store)
        print(graph.get_graph().draw_mermaid())
        yield graph
