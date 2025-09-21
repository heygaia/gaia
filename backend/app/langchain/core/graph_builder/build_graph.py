from contextlib import asynccontextmanager
from typing import Optional

from app.config.loggers import app_logger as logger
from app.core.lazy_loader import MissingKeyStrategy, lazy_provider
from app.langchain.core.graph_builder.checkpointer_manager import (
    get_checkpointer_manager,
)
from app.langchain.core.nodes import (
    delete_system_messages,
    follow_up_actions_node,
    trim_messages_node,
)
from app.langchain.llm.client import init_llm
from app.langchain.tools.core.retrieval import get_retrieve_tools_function
from app.langchain.tools.core.store import get_tools_store
from app.override.langgraph_bigtool.create_agent import create_agent
from langchain_core.language_models import LanguageModelLike
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import END


@asynccontextmanager
async def build_graph(
    chat_llm: Optional[LanguageModelLike] = None,
    in_memory_checkpointer: bool = False,
):
    """Construct and compile the state graph."""
    # Lazy import to avoid circular dependency
    from app.langchain.tools.core.registry import tool_registry

    # Get default LLM if none provided
    if chat_llm is None:
        chat_llm = init_llm()

    store = get_tools_store()

    # Create agent with custom tool retrieval logic
    builder = create_agent(
        llm=chat_llm,
        tool_registry=tool_registry.get_tool_registry(),
        retrieve_tools_function=get_retrieve_tools_function(tool_space="general"),
        trim_messages_node=trim_messages_node,
    )

    # Injector nodes add tool calls to the state messages
    builder.add_node("trim_messages", trim_messages_node)  # type: ignore[call-arg]
    builder.add_node("follow_up_actions", follow_up_actions_node)  # type: ignore[call-arg]
    builder.add_node("delete_system_messages", delete_system_messages)  # type: ignore[call-arg]
    builder.add_edge("agent", "follow_up_actions")
    builder.add_edge("follow_up_actions", END)
    builder.add_edge("agent", "delete_system_messages")

    checkpointer_manager = await get_checkpointer_manager()

    if in_memory_checkpointer or not checkpointer_manager:
        # Use in-memory checkpointer for testing or simple use cases
        in_memory_checkpointer_instance = InMemorySaver()
        # Setup the checkpointer
        graph = builder.compile(
            # type: ignore[call-arg]
            checkpointer=in_memory_checkpointer_instance,
            store=store,
        )
        logger.debug("Graph compiled with in-memory checkpointer")
        yield graph
    else:
        postgres_checkpointer = checkpointer_manager.get_checkpointer()
        graph = builder.compile(checkpointer=postgres_checkpointer, store=store)
        logger.debug("Graph compiled with PostgreSQL checkpointer")
        yield graph


@lazy_provider(
    name="default_graph",
    required_keys=[],  # No specific keys required since dependencies are handled by sub-providers
    strategy=MissingKeyStrategy.WARN,
    auto_initialize=False,
)
async def build_default_graph():
    """Build and return the default graph using lazy providers."""
    logger.debug("Building default graph with lazy providers")

    # Build the graph using the existing function
    async with build_graph() as graph:
        logger.info("Default graph built successfully")
        return graph
