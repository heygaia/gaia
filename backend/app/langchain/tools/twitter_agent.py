from app.langchain.llm.client import init_llm
from app.services.composio_service import composio_service
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.tools import StructuredTool
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
    return compiled_agent


async def run_twitter_agent(query: str) -> str:
    """
    Invokes the Twitter sub-agent with a query and streams the response.
    """
    twitter_agent = create_twitter_agent()
    response_stream = twitter_agent.astream(
        {"messages": [("user", query)]},
        {"recursion_limit": 15},
    )

    response = ""
    async for message in response_stream:
        if "agent" in message:
            response = message["agent"].get("messages")[-1].content

    return response


twitter_agent_tool = StructuredTool.from_function(
    func=run_twitter_agent,
    name="twitter_agent",
    description="""Use this tool for any requests related to Twitter. It can perform a wide variety of actions, including sending tweets, searching for users, and reading timelines. When using this tool, provide a clear and detailed query describing the task you want to accomplish.""",
)

tools = [twitter_agent_tool]
