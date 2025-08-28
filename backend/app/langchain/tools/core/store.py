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
    tool_categories = tool_registry.get_all_category_objects()

    tasks = []
    tools = {}

    for category in tool_categories.values():
        category_tools = category.tools

        for tool in category_tools:
            tasks.append(
                _store.aput(
                    (category.space,),
                    tool.name,
                    {
                        "description": f"{tool.name}: {tool.tool.description}",
                    },
                )
            )
            tools[tool.name] = tool.tool

    # Store all tools for vector search using asyncio batch
    await asyncio.gather(
        *tasks,
    )


def get_tools_store() -> InMemoryStore:
    return _store
