"""
LANGGRAPH BIGTOOL OVERRIDE

This overrides `create_agent` from langgraph_bigtool to support dynamic model configuration.

WHY THIS EXISTS:
- Need to switch between OpenAI, Gemini, and Cerebras models dynamically at runtime
- Extract model_name and provider from config and apply to LLM before tool binding

WHAT'S MODIFIED:
In call_model() and acall_model():
```python
# Added dynamic model configuration:
model_name = config.get("configurable").get("model_name", "gpt-4o-mini")
provider = config.get("configurable").get("provider", None)
_llm = llm.with_config(configurable={"model_name": model_name, "provider": provider})
```

IMPORT CHANGE REQUIRED:
Replace library import in build_graph.py:
```python
# Change this:
from langgraph_bigtool import create_agent
# To this:
from app.override.langgraph_bigtool.create_agent import create_agent
```

NOTE: Type/linting errors in this file are expected since it's copied from external library.
"""

from typing import Any, Callable

from langchain_core.language_models import LanguageModelLike
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool, StructuredTool
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.store.base import BaseStore
from langgraph.types import Send
from langgraph.utils.runnable import RunnableCallable
from langgraph_bigtool.graph import State, _format_selected_tools
from langgraph_bigtool.tools import get_default_retrieval_tool, get_store_arg


def create_agent(
    llm: LanguageModelLike,
    tool_registry: dict[str, BaseTool | Callable],
    *,
    limit: int = 2,
    filter: dict[str, Any] | None = None,
    namespace_prefix: tuple[str, ...] = ("tools",),
    retrieve_tools_function: Callable | None = None,
    retrieve_tools_coroutine: Callable | None = None,
    context_schema=None,
    trim_messages_node: Callable | None = None,
) -> StateGraph:
    """Create an agent with a registry of tools.

    The agent will function as a typical ReAct agent, but is equipped with a tool
    for retrieving tools from a registry. The agent will start with only this tool.
    As it is executed, retrieved tools will be bound to the model.

    Args:
        llm: Language model to use for the agent.
        tool_registry: a dict mapping string IDs to tools or callables.
        limit: Maximum number of tools to retrieve with each tool selection step.
        filter: Optional key-value pairs with which to filter results.
        namespace_prefix: Hierarchical path prefix to search within the Store. Defaults
            to ("tools",).
        retrieve_tools_function: Optional function to use for retrieving tools. This
            function should return a list of tool IDs. If not specified, uses semantic
            against the Store with limit, filter, and namespace_prefix set above.
        retrieve_tools_coroutine: Optional coroutine to use for retrieving tools. This
            function should return a list of tool IDs. If not specified, uses semantic
            against the Store with limit, filter, and namespace_prefix set above.
    """
    if retrieve_tools_function is None and retrieve_tools_coroutine is None:
        retrieve_tools_function, retrieve_tools_coroutine = get_default_retrieval_tool(
            namespace_prefix, limit=limit, filter=filter
        )
    retrieve_tools = StructuredTool.from_function(
        func=retrieve_tools_function, coroutine=retrieve_tools_coroutine
    )
    # If needed, get argument name to inject Store
    store_arg = get_store_arg(retrieve_tools)

    # NOTE: The following functions are copied from langgraph_bigtool library
    # Type errors and linting warnings in this section are EXPECTED and can be ignored
    # as they result from copying external library code that may not match our project's
    # strict typing requirements. The functionality is preserved from the original library.

    def call_model(state: State, config: RunnableConfig, *, store: BaseStore) -> State:
        if trim_messages_node:
            messages = trim_messages_node(state, config, store)
            state["messages"] = messages

        model_configurations = config.get("configurable", {}).get(
            "model_configurations", {}
        )
        model_name = model_configurations.get("model_name", "gpt-4o-mini")
        provider = model_configurations.get("provider", None)
        _llm = llm.with_config(
            configurable={"model_name": model_name, "provider": provider}
        )
        selected_tools = [tool_registry[id] for id in state["selected_tool_ids"]]
        llm_with_tools = _llm.bind_tools([retrieve_tools, *selected_tools])
        response = llm_with_tools.invoke(state["messages"])
        return {"messages": [response]}

    async def acall_model(
        state: State, config: RunnableConfig, *, store: BaseStore
    ) -> State:
        if trim_messages_node:
            messages = trim_messages_node(state, config, store)
            state["messages"] = messages

        model_configurations = config.get("configurable", {}).get(
            "model_configurations", {}
        )
        model_name = model_configurations.get("model_name", "gpt-4o-mini")
        provider = model_configurations.get("provider", None)
        selected_tools = [tool_registry[id] for id in state["selected_tool_ids"]]
        _llm = llm.with_config(
            configurable={"model_name": model_name, "provider": provider}
        )
        llm_with_tools = _llm.bind_tools([retrieve_tools, *selected_tools])
        response = await llm_with_tools.ainvoke(state["messages"])
        return {"messages": [response]}

    tool_node = ToolNode(tool for tool in tool_registry.values())

    def select_tools(
        tool_calls: list[dict], config: RunnableConfig, *, store: BaseStore
    ) -> State:
        selected_tools = {}
        for tool_call in tool_calls:
            kwargs = {**tool_call["args"]}
            if store_arg:
                kwargs[store_arg] = store
            result = retrieve_tools.invoke(kwargs)
            selected_tools[tool_call["id"]] = result

        tool_messages, tool_ids = _format_selected_tools(selected_tools, tool_registry)
        return {"messages": tool_messages, "selected_tool_ids": tool_ids}

    async def aselect_tools(
        tool_calls: list[dict], config: RunnableConfig, *, store: BaseStore
    ) -> State:
        selected_tools = {}
        for tool_call in tool_calls:
            kwargs = {**tool_call["args"]}
            if store_arg:
                kwargs[store_arg] = store
            result = await retrieve_tools.ainvoke(kwargs)
            selected_tools[tool_call["id"]] = result

        tool_messages, tool_ids = _format_selected_tools(selected_tools, tool_registry)
        return {"messages": tool_messages, "selected_tool_ids": tool_ids}

    def should_continue(state: State, *, store: BaseStore):
        messages = state["messages"]
        last_message = messages[-1]
        if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
            return END
        else:
            destinations = []
            for call in last_message.tool_calls:
                if call["name"] == retrieve_tools.name:
                    destinations.append(Send("select_tools", [call]))
                else:
                    tool_call = tool_node.inject_tool_args(call, state, store)
                    destinations.append(Send("tools", [tool_call]))

            return destinations

    builder = StateGraph(State, context_schema=context_schema)

    if retrieve_tools_function is not None and retrieve_tools_coroutine is not None:
        select_tools_node = RunnableCallable(select_tools, aselect_tools)
    elif retrieve_tools_function is not None and retrieve_tools_coroutine is None:
        select_tools_node = select_tools
    elif retrieve_tools_coroutine is not None and retrieve_tools_function is None:
        select_tools_node = aselect_tools
    else:
        raise ValueError(
            "One of retrieve_tools_function or retrieve_tools_coroutine must be "
            "provided."
        )

    builder.add_node("agent", RunnableCallable(call_model, acall_model))
    builder.add_node("select_tools", select_tools_node)
    builder.add_node("tools", tool_node)

    builder.set_entry_point("agent")

    builder.add_conditional_edges(
        "agent",
        should_continue,
        path_map=["select_tools", "tools", END],
    )
    builder.add_edge("tools", "agent")
    builder.add_edge("select_tools", "agent")

    return builder
