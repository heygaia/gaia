import asyncio

from app.utils.embedding_utils import get_or_compute_embeddings
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
    all_tools = [tool_data.tool for tool_data in tool_dict.values()]

    # Store all tools for vector search with cached embeddings
    embeddings_list, tool_descriptions = await get_or_compute_embeddings(
        all_tools, embeddings
    )

    # Build tasks for batch storage with pre-computed embeddings
    tasks = []
    for i, tool_data in enumerate(tool_dict.values()):
        tool = tool_data.tool
        tool_space = tool_data.space

        # Use aput with pre-computed embeddings for proper space handling
        tasks.append(
            _store.aput(
                (tool_space,),
                tool.name,
                {
                    "description": tool_descriptions[i],
                    "embedding": embeddings_list[i],
                },
            )
        )

    # Store all tools using asyncio batch with proper space structure
    await asyncio.gather(*tasks)


def get_tools_store() -> InMemoryStore:
    return _store
