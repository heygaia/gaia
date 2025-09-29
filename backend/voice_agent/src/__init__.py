"""
Voice Agent Package.

This package provides a modular voice agent implementation for integration
with the Gaia backend, featuring real-time voice interaction capabilities.
"""

from .config import config
from .llm import CustomLLM
from .session import VoiceAgentSession, create_voice_agent_session
from .utils import extract_latest_user_text, extract_metadata

__all__ = [
    "CustomLLM",
    "VoiceAgentSession",
    "config",
    "create_voice_agent_session",
    "extract_latest_user_text",
    "extract_metadata",
]
