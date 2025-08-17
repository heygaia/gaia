from app.langchain.llm.client import init_llm
from app.services.composio_service import composio_service
from langgraph.checkpoint.memory import InMemorySaver
from langgraph_bigtool import create_agent

llm = init_llm()


def create_twitter_agent():
    """
    Builds and compiles a LangGraph agent with Twitter tools.
    """
    twitter_tools = composio_service.get_tools(tool_kit="TWITTER")
    tool_registry = {tool.name: tool for tool in twitter_tools}

    agent_executor = create_agent(
        llm=llm,
        tool_registry=tool_registry,
    )

    # Compile the agent executor
    compiled_agent = agent_executor.compile(checkpointer=InMemorySaver())
