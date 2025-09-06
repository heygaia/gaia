from contextlib import asynccontextmanager
from typing import Optional

from app.langchain.core.graph_builder.checkpointer_manager import (
    checkpointer_manager,
)
from app.langchain.core.nodes import (
    create_delete_system_messages_node,
    follow_up_actions_node,
    trim_messages_node,
)
from app.langchain.core.nodes.filter_messages import create_filter_messages_node
from app.langchain.core.subagents.provider_subagents import ProviderSubAgents
from app.langchain.llm.client import init_llm
from app.langchain.prompts.agent_prompts import AGENT_SYSTEM_PROMPT
from app.langchain.tools.core.retrieval import get_retrieve_tools_function
from app.langchain.tools.core.store import get_tools_store
from app.override.langgraph_bigtool.create_agent import create_agent
from langchain_core.language_models import LanguageModelLike
from langgraph.checkpoint.memory import InMemorySaver

llm = init_llm()


@asynccontextmanager
async def build_graph(
    chat_llm: Optional[LanguageModelLike] = None,
    in_memory_checkpointer: bool = False,
):
    """Construct and compile the state graph with integrated sub-agent graphs."""
    # Lazy import to avoid circular dependency
    from app.langchain.tools.core.registry import tool_registry

    store = get_tools_store()
    effective_llm = chat_llm if chat_llm else llm

    sub_agents = ProviderSubAgents.get_all_subagents(effective_llm)

    # Create main agent with custom tool retrieval logic
    builder = create_agent(
        llm=effective_llm,
        agent_name="main_agent",
        tool_registry=tool_registry.get_tool_registry(),
        retrieve_tools_function=get_retrieve_tools_function(tool_space="general"),
        sub_agents=sub_agents,  # pyright: ignore[reportArgumentType]
        pre_model_hooks=[
            create_filter_messages_node(
                agent_name="main_agent",
            ),
            trim_messages_node,
        ],
        end_graph_hooks=[
            follow_up_actions_node,
            create_delete_system_messages_node(
                prompt=AGENT_SYSTEM_PROMPT,
            ),
        ],
    )

    if in_memory_checkpointer:
        # Use in-memory checkpointer for testing or simple use cases
        in_memory_checkpointer_instance = InMemorySaver()
        # Setup the checkpointer
        graph = builder.compile(
            # type: ignore[call-arg]
            checkpointer=in_memory_checkpointer_instance,
            store=store,
        )
        print(graph.get_graph().draw_mermaid())
        yield graph
    else:
        postgres_checkpointer = checkpointer_manager.get_checkpointer()
        graph = builder.compile(checkpointer=postgres_checkpointer, store=store)
        print(graph.get_graph().draw_mermaid())
        yield graph
