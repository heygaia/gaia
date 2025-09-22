"""
Token tracking callback handler for LangChain/LangGraph.

Tracks token usage during LLM interactions and stores metadata for messages.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.config.loggers import llm_logger as logger
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.outputs import LLMResult


class TokenTrackingCallback(AsyncCallbackHandler):
    """Callback handler to track token usage during LLM interactions."""

    def __init__(
        self,
        user_id: str,
        conversation_id: str,
        feature_key: str = "chat",
    ):
        """Initialize token tracking callback."""
        self.user_id = user_id
        self.conversation_id = conversation_id
        self.feature_key = feature_key
        self.total_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.llm_calls = []
        self.current_call_tokens = {}

    async def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Called when LLM starts running."""
        self.current_call_tokens[run_id] = {
            "start_time": datetime.now(timezone.utc).isoformat(),
            "model": serialized.get("name", "unknown"),
        }

    async def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        """Called when LLM finishes running."""
        try:
            if response.llm_output and "token_usage" in response.llm_output:
                token_usage = response.llm_output["token_usage"]
                
                prompt_tokens = token_usage.get("prompt_tokens", 0)
                completion_tokens = token_usage.get("completion_tokens", 0)
                total_tokens = token_usage.get("total_tokens", prompt_tokens + completion_tokens)
                
                # Update cumulative counts
                self.prompt_tokens += prompt_tokens
                self.completion_tokens += completion_tokens
                self.total_tokens += total_tokens
                
                # Store call details
                if run_id in self.current_call_tokens:
                    call_data = self.current_call_tokens[run_id]
                    call_data.update({
                        "end_time": datetime.now(timezone.utc).isoformat(),
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": total_tokens,
                    })
                    self.llm_calls.append(call_data)
                
                logger.info(
                    f"Token usage tracked - User: {self.user_id}, "
                    f"Conversation: {self.conversation_id}, "
                    f"Tokens: {total_tokens} (prompt: {prompt_tokens}, completion: {completion_tokens})"
                )
                
        except Exception as e:
            logger.error(f"Error tracking token usage: {e}")

    async def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        """Called when LLM errors."""
        if run_id in self.current_call_tokens:
            del self.current_call_tokens[run_id]

    def get_token_metadata(self) -> Dict[str, Any]:
        """Get token usage metadata to add to message."""
        if self.total_tokens == 0:
            return {}
            
        return {
            "token_usage": {
                "total_tokens": self.total_tokens,
                "prompt_tokens": self.prompt_tokens,
                "completion_tokens": self.completion_tokens,
                "llm_calls": len(self.llm_calls),
                "feature_key": self.feature_key,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        }
