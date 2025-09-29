"""Custom LLM implementation for voice agent integration."""

import asyncio
import json
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Optional

import aiohttp
from livekit import rtc
from livekit.agents.llm import LLM, ChatChunk, ChatContext, ChoiceDelta

from .config import config
from .utils import (
    extract_latest_user_text,
    normalize_content_to_string,
    should_flush_buffer,
)


class CustomLLM(LLM):
    """
    Custom LLM implementation that streams responses from the Gaia backend.
    
    This class integrates with the Gaia backend API to provide streaming
    chat functionality with real-time TTS integration for voice agents.
    
    Attributes:
        base_url: Base URL for the backend API
        agent_token: Authentication token for the agent
        conversation_id: ID of the current conversation
        request_timeout_s: Timeout for HTTP requests
        room: LiveKit room instance for communication
    """
    
    def __init__(self, base_url: str, request_timeout_s: Optional[float] = None, room: Optional[rtc.Room] = None):
        """
        Initialize the CustomLLM with backend configuration.
        
        Args:
            base_url: Base URL for the backend API
            request_timeout_s: Request timeout in seconds (defaults to config value)
            room: LiveKit room instance for sending messages
        """
        super().__init__()
        self.base_url = base_url
        self.agent_token: Optional[str] = None
        self.conversation_id: Optional[str] = None
        self.request_timeout_s = request_timeout_s or config.request_timeout
        self.room = room

    def set_agent_token(self, token: Optional[str]) -> None:
        """
        Set the authentication token for the agent.
        
        Args:
            token: Agent authentication token
        """
        self.agent_token = token

    async def set_conversation_id(self, conversation_id: Optional[str]) -> None:
        """
        Set the conversation ID and notify the room if connected.
        
        This method updates the conversation ID and sends it to the room
        participants for synchronization.
        
        Args:
            conversation_id: ID of the conversation
        """
        self.conversation_id = conversation_id
        
        if self.room and self.room.local_participant and conversation_id:
            try:
                await self.room.local_participant.send_text(
                    conversation_id, topic="conversation-id"
                )
            except Exception as e:
                print(f"Failed to send conversation ID: {e}")

    @asynccontextmanager
    async def chat(self, chat_ctx: ChatContext, **kwargs):
        """
        Stream chat responses from the backend API.
        
        This method handles the streaming communication with the backend,
        processing Server-Sent Events and yielding chat chunks for TTS.
        
        Args:
            chat_ctx: Current chat context with conversation history
            **kwargs: Additional chat parameters
            
        Yields:
            AsyncGenerator that produces ChatChunk objects for TTS streaming
        """
        async def generate_chunks() -> AsyncGenerator[ChatChunk, None]:
            """Generate chat chunks from the streaming backend response."""
            user_message = extract_latest_user_text(chat_ctx)
            
            # Configure request headers and payload
            headers = self._build_request_headers()
            payload = self._build_request_payload(user_message)
            
            timeout = aiohttp.ClientTimeout(total=self.request_timeout_s)
            
            async with (
                aiohttp.ClientSession(timeout=timeout) as session,
                session.post(
                    f"{self.base_url}/api/v1/chat-stream",
                    headers=headers,
                    json=payload,
                ) as response
            ):
                    response.raise_for_status()
                    
                    text_buffer: list[str] = []
                    
                    async for raw_data in response.content:
                        if not raw_data:
                            continue
                            
                        line = raw_data.decode("utf-8", errors="ignore").strip()
                        if not line or not line.startswith("data:"):
                            continue

                        # Parse the streaming data
                        parsed_data = self._parse_stream_line(line)
                        if not parsed_data:
                            continue
                            
                        # Handle different types of streaming data
                        if parsed_data == "[DONE]":
                            # Process final buffer contents
                            async for chunk in self._flush_final_buffer(text_buffer):
                                yield chunk
                            break
                            
                        try:
                            payload_data = json.loads(parsed_data)
                        except json.JSONDecodeError:
                            continue
                        
                        # Handle conversation ID updates
                        conv_id = payload_data.get("conversation_id")
                        if isinstance(conv_id, str) and conv_id:
                            await self.set_conversation_id(conv_id)
                            continue
                        
                        # Process response content
                        response_content = payload_data.get("response", "")
                        if not response_content:
                            continue
                        
                        # Add content to buffer and check for flush conditions
                        async for chunk in self._process_response_content(response_content, text_buffer):
                            yield chunk

        yield generate_chunks()

    def _build_request_headers(self) -> dict[str, str]:
        """
        Build HTTP headers for the backend request.
        
        Returns:
            Dictionary containing request headers
        """
        headers = {"x-timezone": "UTC"}
        if self.agent_token:
            headers["Authorization"] = f"Bearer {self.agent_token}"
        return headers

    def _build_request_payload(self, user_message: str) -> dict:
        """
        Build the request payload for the backend API.
        
        Args:
            user_message: Latest user message text
            
        Returns:
            Dictionary containing the request payload
        """
        payload = {
            "message": user_message,
            "messages": [{"role": "user", "content": user_message}],
        }
        if self.conversation_id:
            payload["conversation_id"] = self.conversation_id
        return payload

    def _parse_stream_line(self, line: str) -> Optional[str]:
        """
        Parse a line from the Server-Sent Events stream.
        
        Args:
            line: Raw line from the SSE stream
            
        Returns:
            Parsed data content or None if invalid
        """
        if not line.startswith("data:"):
            return None
        return line[5:].strip()

    async def _process_response_content(self, content, text_buffer: list[str]) -> AsyncGenerator[ChatChunk, None]:
        """
        Process response content and manage text buffering.
        
        Args:
            content: Response content from the backend
            text_buffer: Current text buffer for accumulating content
            
        Yields:
            ChatChunk objects when buffer should be flushed
        """
        # Normalize content to string and add to buffer
        normalized_content = normalize_content_to_string(content)
        text_buffer.append(normalized_content)
        
        # Check if we should flush the buffer
        joined_buffer = "".join(text_buffer)
        if should_flush_buffer(
            joined_buffer,
            config.min_chunk_length,
            config.natural_boundary_min_length,
            config.max_buffer_length
        ):
            output_text = joined_buffer.strip()
            text_buffer.clear()
            
            if len(output_text) >= config.min_chunk_length:
                yield ChatChunk(id="custom", delta=ChoiceDelta(content=output_text))
                # Small delay to allow TTS processing
                await asyncio.sleep(0.1)

    async def _flush_final_buffer(self, text_buffer: list[str]) -> AsyncGenerator[ChatChunk, None]:
        """
        Flush any remaining content in the buffer at the end of streaming.
        
        Args:
            text_buffer: Current text buffer contents
            
        Yields:
            Final ChatChunk if buffer contains content
        """
        if text_buffer:
            final_content = "".join(text_buffer).strip()
            if len(final_content) >= 1:
                yield ChatChunk(id="custom", delta=ChoiceDelta(content=final_content))