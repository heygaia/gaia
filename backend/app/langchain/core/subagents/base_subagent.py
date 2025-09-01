"""
Base sub-agent factory for creating provider-specific agents.

This module provides the core framework for building specialized sub-agents
that can handle specific tool categories with deep domain expertise.
"""

from typing import Literal

from app.config.loggers import langchain_logger as logger
from app.langchain.core.nodes import trim_messages_node
from app.langchain.core.nodes.filter_messages import create_filter_messages_node
from app.langchain.tools.core.retrieval import get_retrieve_tools_function
from app.langchain.tools.core.store import get_tools_store
from app.langchain.tools.memory_tools import get_all_memory, search_memory
from app.override.langgraph_bigtool.create_agent import create_agent
from langchain_core.language_models import LanguageModelLike
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore
from langgraph.utils.runnable import RunnableCallable
from langgraph_bigtool.graph import State


class SubAgentFactory:
    """Factory for creating provider-specific sub-agents with specialized tool registries."""

    @staticmethod
    def create_provider_subagent(
        provider: str,
        name: str,
        llm: LanguageModelLike,
        tool_space: str = "general",
        history_type: Literal["last_message", "full_history"] = "last_message",
    ):
        """
        Creates a specialized sub-agent graph for a specific provider with tool registry.

        Args:
            provider: Provider name (gmail, notion, twitter, linkedin)
            llm: Language model to use
            tool_space: Tool space to use for retrieval (e.g., "gmail_delegated", "general")

        Returns:
            Compiled LangGraph agent with tool registry and retrieval
        """
        logger.info(
            f"Creating {provider} sub-agent graph using tool space '{tool_space}' with retrieve tools functionality"
        )

        # Get the entire tool registry - filtering will be handled by retrieve_tools_function
        from app.langchain.tools.core.registry import tool_registry

        store = get_tools_store()

        def transform_output(
            state: State, config: RunnableConfig, store: BaseStore
        ) -> State:
            messages = state["messages"]
            last_message = messages[-1]

            if isinstance(last_message, AIMessage) and not last_message.tool_calls:
                if history_type == "last_message":
                    # Keep only the last AI message in history
                    state["messages"] = [last_message]
                return state

            return state


        # Create agent with entire tool registry and tool retrieval filtering
        # The retrieve_tools_function will filter tools based on tool_space
        builder = create_agent(
            llm=llm,
            tool_registry=tool_registry.get_tool_registry(),
            agent_name=name,
            retrieve_tools_function=get_retrieve_tools_function(
                tool_space=tool_space,
                include_core_tools=False,  # Provider agents don't need core tools
                additional_tools=[get_all_memory, search_memory],
            ),
            pre_model_hooks=[
                create_filter_messages_node(
                    agent_name=name,
                    allow_empty_agent_name=False,
                ),
                trim_messages_node,
            ],
            end_graph_hooks=[transform_output],
        )

        subagent_graph = builder.compile(store=store, name=name, checkpointer=False)

        def call_agent(state: State):
            response = subagent_graph.invoke(state)  # type: ignore[call-arg]

            if history_type == "last_message":
                # Keep only the last AI message in history
                response["messages"] = [response["messages"][-1]]

            return {"messages": response["messages"]}

        async def acall_agent(state: State):
            response = await subagent_graph.ainvoke(state)  # type: ignore[call-arg]

            if history_type == "last_message":
                # Keep only the last AI message in history
                response["messages"] = [response["messages"][-1]]

            return {"messages": response["messages"]}

        logger.info(f"Successfully created {provider} sub-agent graph")
        return RunnableCallable(call_agent, acall_agent)
