"""Docstrings for memory-related tools."""

ADD_MEMORY = """
Store a new memory with associated metadata.

This tool stores important information for later retrieval. Use it to remember
user preferences, key facts, or conversation history that may be relevant in future
interactions.

Args:
    content: The memory content to store
    metadata: Optional metadata to associate with the memory
    config: Runtime configuration containing user context

Returns:
    Confirmation message with the memory ID
"""

SEARCH_MEMORY = """
Search stored memories using natural language queries.

This tool enables retrieval of previously stored memories that are semantically
similar to the query. Use it to recall relevant information from past interactions.

Args:
    query: The search query text
    limit: Maximum number of results to return
    config: Runtime configuration containing user context

Returns:
    Formatted string with search results
"""

GET_ALL_MEMORY = """
Retrieve all memories matching specified criteria, with pagination.

This tool returns all stored memories for the user, organized by pages.
Use it to browse through the knowledge base when you need a comprehensive view.

Args:
    page: Page number to retrieve (starting from 1)
    page_size: Number of results per page
    config: Runtime configuration containing user context

Returns:
    Formatted string with paginated memory results
"""
