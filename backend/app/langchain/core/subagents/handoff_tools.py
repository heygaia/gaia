"""
Handoff tools for supervisor agent to delegate tasks to specialized sub-agent graphs.

This module defines tools that allow the main supervisor agent to route
specific tasks to domain-specialized sub-agent graphs with full tool registry
and retrieval capabilities.

## Architecture Overview:

### Sub-Agent Graphs Structure:
Each provider sub-agent is now a full LangGraph with:
- **Tool Registry**: 40+ provider-specific tools organized by semantic similarity
- **Tool Retrieval**: Intelligent tool selection based on task requirements
- **System Prompts**: Domain-specific expertise and guidelines
- **Graph Manager Integration**: Registered in global GraphManager for routing

### Supported Providers:
1. **Gmail Agent**: Email management with 23+ Gmail tools
2. **Notion Agent**: Workspace management with 40+ Notion tools
3. **Twitter Agent**: Social media management with 40+ Twitter tools
4. **LinkedIn Agent**: Professional networking with 40+ LinkedIn tools

### Tool Retrieval Benefits:
- **Semantic Search**: Tools are selected based on task similarity
- **Efficiency**: Only relevant tools are loaded per task
- **Scalability**: Can handle 40+ tools per provider without overwhelming the agent
- **Specialization**: Each agent has deep domain expertise

### Integration with Main Graph:
- Sub-agents are registered as nodes in the main graph
- Handoff tools route specific tasks to appropriate sub-agents
- Each sub-agent operates independently with its own tool ecosystem
- Results flow back to the main conversation thread

This replaces the previous simple React agents with sophisticated graphs
that can intelligently manage large tool sets while maintaining specialization.
"""

import logging
from typing import Annotated, List, Optional

from app.langchain.prompts.subagents import (
    GMAIL_AGENT_SYSTEM_PROMPT,
    LINKEDIN_AGENT_SYSTEM_PROMPT,
    NOTION_AGENT_SYSTEM_PROMPT,
    TWITTER_AGENT_SYSTEM_PROMPT,
)
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.graph import MessagesState
from langgraph.prebuilt import InjectedState
from langgraph.types import Command, Send

logger = logging.getLogger(__name__)

def create_handoff_tool(
    *,
    tool_name: str,
    agent_name: str,
    system_prompt: str,
    description: str | None = None,
):
    description = description or f"Transfer to {agent_name}"

    @tool(tool_name, description=description)
    def handoff_tool(
        task_description: Annotated[
            str,
            "Description of what the next agent should do, including all of the relevant context.",
        ],
        state: Annotated[MessagesState, InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> Command:
        task_description_message = {"role": "user", "content": task_description}
        system_prompt_message = {"role": "system", "content": system_prompt}

        tool_message = {
            "role": "tool",
            "content": f"Successfully transferred to {agent_name}",
            "name": tool_name,
            "tool_call_id": tool_call_id,
        }
        agent_input = {
            **state,
            "messages": [system_prompt_message, task_description_message],
        }

        return Command(
            goto=[Send(agent_name, agent_input)],
            update={"messages": state["messages"] + [tool_message]},
        )

    return handoff_tool


def get_handoff_tools(enabled_providers: Optional[List[str]] = None):
    """
    Get handoff tools for enabled provider sub-agent graphs.

    Args:
        enabled_providers: List of enabled provider names
                          ('gmail', 'notion', 'twitter', 'linkedin')

    Returns:
        List of handoff tools for the enabled provider sub-agent graphs
    """
    if enabled_providers is None:
        enabled_providers = ["gmail", "notion", "twitter", "linkedin"]

    tools = []

    if "gmail" in enabled_providers:
        tools.append(
            create_handoff_tool(
                tool_name="call_gmail_agent",
                agent_name="gmail_agent",
                description="Handles Mail related operations",
                system_prompt=GMAIL_AGENT_SYSTEM_PROMPT,
            )
        )

    if "notion" in enabled_providers:
        tools.append(
            create_handoff_tool(
                tool_name="call_notion_agent",
                agent_name="notion_agent",
                description="Handles Notion related operations",
                system_prompt=NOTION_AGENT_SYSTEM_PROMPT,
            )
        )

    if "twitter" in enabled_providers:
        tools.append(
            create_handoff_tool(
                tool_name="call_twitter_agent",
                agent_name="twitter_agent",
                description="Handles Twitter related operations",
                system_prompt=TWITTER_AGENT_SYSTEM_PROMPT,
            )
        )

    if "linkedin" in enabled_providers:
        tools.append(
            create_handoff_tool(
                tool_name="call_linkedin_agent",
                agent_name="linkedin_agent",
                description="Handles LinkedIn related operations",
                system_prompt=LINKEDIN_AGENT_SYSTEM_PROMPT,
            )
        )

    logger.info(
        f"Created {len(tools)} handoff tools for providers: {enabled_providers}"
    )
    return tools
