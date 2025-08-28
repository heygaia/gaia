"""
Sub-agent prompts module.

This module contains specialized system prompts for different provider sub-agents.
"""

from .provider_prompts import (
    GMAIL_AGENT_SYSTEM_PROMPT,
    NOTION_AGENT_SYSTEM_PROMPT,
    TWITTER_AGENT_SYSTEM_PROMPT,
    LINKEDIN_AGENT_SYSTEM_PROMPT,
)

__all__ = [
    "GMAIL_AGENT_SYSTEM_PROMPT",
    "NOTION_AGENT_SYSTEM_PROMPT", 
    "TWITTER_AGENT_SYSTEM_PROMPT",
    "LINKEDIN_AGENT_SYSTEM_PROMPT",
]