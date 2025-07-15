from datetime import datetime, timezone
from typing import List, Optional

import pytz
from app.config.loggers import llm_logger as logger
from app.langchain.templates.agent_template import AGENT_PROMPT_TEMPLATE
from app.models.message_models import FileData, MessageDict
from app.services.memory_service import memory_service
from app.services.onboarding_service import get_user_preferences_for_agent
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage


async def construct_langchain_messages(
    messages: List[MessageDict],
    user_timezone_name: str,
    files_data: List[FileData] | None = None,
    currently_uploaded_file_ids: Optional[List[str]] = [],
    user_id: Optional[str] = None,
    user_name: Optional[str] = None,
    query: Optional[str] = None,
    selected_tool: Optional[str] = None,
) -> List[AnyMessage]:
    """
    Convert raw dict messages to LangChain message objects with current datetime.

    Args:
        messages: List of message dictionaries containing role and content
        files_data: Optional list of file data objects
        currently_uploaded_file_ids: Optional list of currently uploaded file IDs
        user_id: Optional user ID for retrieving relevant memories
        query: Optional query string for memory search (usually the latest user message)
        selected_tool: Optional tool selected via slash commands

    Returns:
        List of LangChain message objects
    """
    # Format current time for the system prompt
    formatted_time = datetime.now(timezone.utc).strftime("%A, %B %d, %Y, %H:%M:%S UTC")

    # Format the list of files if any
    current_files_str = _format_files_list(files_data, currently_uploaded_file_ids)

    # Get user preferences for the agent if user_id is provided
    user_preferences_str = ""
    if user_id:
        user_preferences_str = await get_user_preferences_for_agent(user_id) or ""
        if user_preferences_str:
            user_preferences_str = f"\n{user_preferences_str}\n"

    # Create the system prompt with the current time and user preferences
    system_prompt = AGENT_PROMPT_TEMPLATE.format(
        current_datetime=formatted_time,
        user_name=user_name,
        user_preferences=user_preferences_str,
    )

    chain_msgs: List[AnyMessage] = [SystemMessage(content=system_prompt)]

    # Add relevant memories from memory service if user_id and query are provided
    if user_id and query:
        try:
            # Search for relevant memories
            memory_results = await memory_service.search_memories(
                query=query, user_id=user_id, limit=5
            )

            # If we have memories, add them as a system message
            if (
                memory_results
                and hasattr(memory_results, "memories")
                and memory_results.memories
            ):
                memory_content = "Based on our previous conversations:\n"
                for mem in memory_results.memories:
                    memory_content += f"- {mem.content}\n"

                # Add memory as a system message
                memory_message = SystemMessage(content=memory_content.strip())
                chain_msgs.append(memory_message)

                logger.info(f"Added {len(memory_results.memories)} memories to context")
        except Exception as e:
            logger.error(f"Error retrieving memories: {e}")

    # Handle case where no conversation messages exist but a tool is selected
    if not messages and selected_tool:
        # Format tool name for better readability
        tool_display_name = selected_tool.replace("_", " ").title()
        content = f"Use the {tool_display_name} tool."

        # Add file information if files are uploaded
        if currently_uploaded_file_ids:
            content += f"\n\n{current_files_str}"

        chain_msgs.append(HumanMessage(content=content))
    else:
        # Convert each message to the appropriate LangChain message type
        for index, msg in enumerate(messages):
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "user":
                # If the message is last and the role is "user", append additional context
                if index == len(messages) - 1:
                    # Add file information if files are uploaded
                    if currently_uploaded_file_ids:
                        content += f"\n\n{current_files_str}"

                    # Add tool selection information if a tool is selected
                    if selected_tool:
                        # Format tool name for better readability
                        tool_display_name = selected_tool.replace("_", " ").title()
                        if content.strip():  # If there's existing content
                            content += f"\n\nPlease use the {tool_display_name} tool to handle this request."
                        else:  # If the message is empty
                            content = f"Use the {tool_display_name} tool."

                    # Add system's time and user time
                    system_time = datetime.now(timezone.utc)
                    user_time = datetime.now(pytz.timezone(user_timezone_name))

                    content += f"\n\nSystem Time: {system_time.isoformat()}"
                    content += f"\nUser Time: {user_time.isoformat()}"

                chain_msgs.append(HumanMessage(content=content))
            elif role in ("assistant", "bot"):
                chain_msgs.append(AIMessage(content=content))

    return chain_msgs


def _format_files_list(
    files_data: Optional[List[FileData]], file_ids: Optional[List[str]] = None
) -> str:
    """Format list of files into a readable string.

    Args:
        files_data: List of FileData objects containing file information.
        file_ids: Optional list of file IDs to filter the files. If None, all files are included.
        If empty, returns "No files uploaded."
    Returns:
        str: Formatted string of file names and IDs.
    """
    if not files_data:
        return "No files uploaded."

    if file_ids is None:
        return "\n".join(
            f"- Name: {file.filename} Id: {file.fileId}" for file in files_data
        )

    if not file_ids:
        return "No files uploaded."

    # Filter files based on file_ids
    files_data = list(filter(lambda x: x.fileId in file_ids, files_data))
    if not files_data:
        return "No files uploaded."

    return "\n".join(
        f"- Name: {file.filename} Id: {file.fileId}" for file in files_data
    )
