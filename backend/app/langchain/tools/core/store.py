import asyncio

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langgraph.store.memory import InMemoryStore

embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

# Create store for tool discovery
_store = InMemoryStore(
    index={
        "embed": embeddings,
        "dims": 768,
        "fields": ["description"],
    }
)


async def initialize_tools_store():
    """Initialize and return the tool registry and store.

    Returns:
        tuple: A tuple containing the tool registry and the store.
    """
    # Lazy import to avoid circular dependency
    from app.langchain.tools.core.registry import tool_registry

    # Register both regular and always available tools
    tool_dict = tool_registry.get_tool_dictionary()

    tasks = []
    tools = {}
    for tool_data in tool_dict.values():
        tool = tool_data.tool
        tool_space = tool_data.space
        tasks.append(
            _store.aput(
                (tool_space,),
                tool.name,
                {
                    "description": f"{tool.name}: {tool.description}",
                },
            )
        )
        tools[tool.name] = tool

    # Store all tools for vector search using asyncio batch
    await asyncio.gather(
        *tasks,
    )


def get_tools_store() -> InMemoryStore:
    return _store
