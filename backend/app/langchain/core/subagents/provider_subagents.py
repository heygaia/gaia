"""
Provider-specific sub-agent implementations.

This module contains the factory methods for creating specialized sub-agent graphs
for different providers (Gmail, Notion, Twitter, LinkedIn, etc.) with full tool
registry and retrieval capabilities.

Now supports both legacy subagent architecture and new plan-and-execute subgraphs.
"""

from typing import Any

from app.config.loggers import langchain_logger as logger
from app.langchain.prompts.subagent_prompts import (
    LINKEDIN_AGENT_SYSTEM_PROMPT,
    NOTION_AGENT_SYSTEM_PROMPT,
    TWITTER_AGENT_SYSTEM_PROMPT,
)
from langchain_core.language_models import LanguageModelLike

from .base_subagent import SubAgentFactory


class ProviderSubAgents:
    """Factory for creating and managing provider-specific sub-agent graphs."""

    @staticmethod
    def create_gmail_agent(llm: LanguageModelLike):
        """
        Create a clean Gmail agent with simple plan-and-execute flow.

        Args:
            llm: Language model to use

        Returns:
            Compiled Gmail agent
        """
        logger.info("Creating clean Gmail plan-and-execute subgraph")

        # Import the Gmail subgraph here to avoid circular imports
        from app.langchain.core.subgraphs.gmail_subgraph import create_gmail_subgraph

        gmail_agent = create_gmail_subgraph(llm=llm)

        logger.info("Gmail subgraph created successfully")
        return gmail_agent

    @staticmethod
    def create_notion_agent(llm: LanguageModelLike):
        """
        Create a specialized Notion agent graph using tool registry filtering.

        Args:
            llm: Language model to use
            user_id: Optional user ID for tool context

        Returns:
            Compiled Notion sub-agent graph
        """
        logger.info("Creating Notion sub-agent graph using general tool space")

        # Create the Notion agent graph using entire tool registry with space filtering
        notion_agent = SubAgentFactory.create_provider_subagent(
            provider="notion",
            llm=llm,
            tool_space="notion",
            name="notion_agent",
            prompt=NOTION_AGENT_SYSTEM_PROMPT,
        )

        return notion_agent

    @staticmethod
    def create_twitter_agent(llm: LanguageModelLike):
        """
        Create a specialized Twitter agent graph using tool registry filtering.

        Args:
            llm: Language model to use
            user_id: Optional user ID for tool context

        Returns:
            Compiled Twitter sub-agent graph
        """
        logger.info("Creating Twitter sub-agent graph using general tool space")

        # Create the Twitter agent graph using entire tool registry with space filtering
        twitter_agent = SubAgentFactory.create_provider_subagent(
            provider="twitter",
            llm=llm,
            tool_space="twitter",
            name="twitter_agent",
            prompt=TWITTER_AGENT_SYSTEM_PROMPT,
        )

        return twitter_agent

    @staticmethod
    def create_linkedin_agent(llm: LanguageModelLike):
        """
        Create a specialized LinkedIn agent graph using tool registry filtering.

        Args:
            llm: Language model to use
            user_id: Optional user ID for tool context

        Returns:
            Compiled LinkedIn sub-agent graph
        """
        logger.info("Creating LinkedIn sub-agent graph using general tool space")

        # Create the LinkedIn agent graph using entire tool registry with space filtering
        linkedin_agent = SubAgentFactory.create_provider_subagent(
            provider="linkedin",
            llm=llm,
            tool_space="linkedin",
            name="linkedin_agent",
            prompt=LINKEDIN_AGENT_SYSTEM_PROMPT,
        )

        return linkedin_agent

    @staticmethod
    def get_all_subagents(llm: LanguageModelLike) -> dict[str, Any]:
        """
        Create all provider-specific sub-agent graphs.

        Args:
            llm: Language model to use

        Returns:
            Dictionary of compiled sub-agent graphs
        """
        return {
            "gmail_agent": ProviderSubAgents.create_gmail_agent(llm),
            "notion_agent": ProviderSubAgents.create_notion_agent(llm),
            "twitter_agent": ProviderSubAgents.create_twitter_agent(llm),
            "linkedin_agent": ProviderSubAgents.create_linkedin_agent(llm),
        }
