"""Utility functions for voice agent operations."""

import json
from typing import Optional

from livekit.agents.llm import ChatContext


def extract_metadata(metadata: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """
    Extract agentToken and conversationId from participant metadata JSON.
    
    Args:
        metadata: JSON string containing participant metadata
        
    Returns:
        Tuple of (agent_token, conversation_id), both can be None if not found
        
    Examples:
        >>> extract_metadata('{"agentToken": "abc123", "conversationId": "conv456"}')
        ('abc123', 'conv456')
        >>> extract_metadata('{}')
        (None, None)
        >>> extract_metadata(None)
        (None, None)
    """
    if not metadata:
        return None, None
    
    try:
        data = json.loads(metadata)
        agent_token = data.get("agentToken")
        conversation_id = data.get("conversationId")
        
        # Ensure values are valid strings
        agent_token = agent_token if isinstance(agent_token, str) and agent_token else None
        conversation_id = conversation_id if isinstance(conversation_id, str) and conversation_id else None
        
        return agent_token, conversation_id
    except (json.JSONDecodeError, TypeError):
        return None, None


def extract_latest_user_text(chat_context: ChatContext) -> str:
    """
    Extract the latest user text from ChatContext.
    
    This function searches through the chat context items in reverse order
    to find the most recent user message and extracts its text content.
    
    Args:
        chat_context: LiveKit ChatContext containing conversation history
        
    Returns:
        String containing the latest user message text, empty string if none found
        
    Examples:
        >>> # Assuming chat_context has user messages
        >>> text = extract_latest_user_text(chat_context)
        >>> print(text)  # "Hello, how are you?"
    """
    for item in reversed(chat_context.items):
        # Get the role from the item
        role = getattr(item, "role", item.__class__.__name__.lower())
        
        if role == "user":
            # Extract content from the item
            content = getattr(item, "content", [getattr(item, "output", "")])
            text_parts = []
            
            # Process each content part
            for content_part in content:
                if hasattr(content_part, "model_dump"):
                    # Handle structured content
                    data = content_part.model_dump()
                    if isinstance(data, dict):
                        text_parts.append(data.get("text", ""))
                else:
                    # Handle simple string content
                    text_parts.append(str(content_part))
            
            # Join all parts and return if non-empty
            result = " ".join(part for part in text_parts if part)
            if result:
                return result
    
    return ""


def should_flush_buffer(buffer_content: str, min_chunk_length: int = 15,
                       natural_boundary_min_length: int = 40,
                       max_buffer_length: int = 120) -> bool:
    """
    Determine if the text buffer should be flushed based on content and length.
    
    This function implements an intelligent flushing strategy that considers:
    - Natural sentence boundaries (., !, ?)
    - Buffer length limits
    - Minimum chunk sizes for quality
    
    Args:
        buffer_content: Current content in the buffer
        min_chunk_length: Minimum length for any chunk to be flushed
        natural_boundary_min_length: Minimum length before flushing at sentence boundaries
        max_buffer_length: Maximum buffer length before forced flush
        
    Returns:
        True if buffer should be flushed, False otherwise
        
    Examples:
        >>> should_flush_buffer("This is a complete sentence.")
        True
        >>> should_flush_buffer("This is")
        False
        >>> should_flush_buffer("A" * 130)  # Very long buffer
        True
    """
    if len(buffer_content) < min_chunk_length:
        return False
    
    # Check for natural sentence boundaries
    if (any(buffer_content.endswith(punct) for punct in [".", "!", "?"])
            and len(buffer_content) >= natural_boundary_min_length):
        return True

    # Force flush if buffer is getting too long
    return len(buffer_content) >= max_buffer_length


def normalize_content_to_string(content) -> str:
    """
    Normalize various content types to a string representation.
    
    This utility function handles different content formats that might be
    received from the streaming API and converts them to strings.
    
    Args:
        content: Content of various types (str, list, tuple, set, etc.)
        
    Returns:
        String representation of the content
        
    Examples:
        >>> normalize_content_to_string("hello")
        'hello'
        >>> normalize_content_to_string(["hello", "world"])
        'helloworld'
        >>> normalize_content_to_string(123)
        '123'
    """
    if isinstance(content, str):
        return content
    elif isinstance(content, (list, tuple, set)):
        return "".join(str(item) for item in content)
    else:
        return str(content)