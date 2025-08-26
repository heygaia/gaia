from datetime import datetime, timezone
from typing import List, Optional

from app.config.loggers import llm_logger as logger
from app.langchain.templates.agent_template import AGENT_PROMPT_TEMPLATE
from app.langchain.prompts.workflow_prompts import WORKFLOW_EXECUTION_PROMPT
from app.models.message_models import FileData, MessageDict, SelectedWorkflowData
from app.services.memory_service import memory_service
from app.services.onboarding_service import get_user_preferences_for_agent
from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage


async def construct_langchain_messages(
    messages: List[MessageDict],
    files_data: List[FileData] | None = None,
    currently_uploaded_file_ids: Optional[List[str]] = [],
    user_id: Optional[str] = None,
    user_name: Optional[str] = None,
    query: Optional[str] = None,
    selected_tool: Optional[str] = None,
    selected_workflow: Optional[SelectedWorkflowData] = None,
) -> List[AnyMessage]:
    """
    Convert raw dict messages to LangChain message objects with current datetime.
    Only processes system prompt and current human message since LangChain checkpointer handles history.

    Args:
        messages: List of message dictionaries containing role and content
        files_data: Optional list of file data objects
        currently_uploaded_file_ids: Optional list of currently uploaded file IDs
        user_id: Optional user ID for retrieving relevant memories
        query: Optional query string for memory search (usually the latest user message)
        selected_tool: Optional tool selected via slash commands
        selected_workflow: Optional workflow selected for execution

    Returns:
        List of LangChain message objects (SystemMessage + HumanMessage only)
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

    # Determine human message content
    human_message_content = ""

    # Check if we have a current human message
    if messages and messages[-1].get("role") == "user":
        # User has provided a message
        human_message_content = messages[-1].get("content", "").strip()

    # Handle tool selection
    if selected_tool:
        tool_display_name = selected_tool.replace("_", " ").title()

        if human_message_content:
            # User has content + tool selected
            human_message_content += f"\n\n**TOOL SELECTION:** The user has specifically selected the '{tool_display_name}' tool and wants you to execute it to handle their request above. You must use the {selected_tool} tool to process their request. Do not suggest alternatives - the user has already chosen this specific tool for their task."
        else:
            # No user content, just tool selection
            human_message_content = f"**TOOL EXECUTION REQUEST:** The user has selected the '{tool_display_name}' tool and wants you to execute it immediately. Use the {selected_tool} tool now. This is a direct tool execution request with no additional context needed. If you don't have tool context, use retrieve_tools to get tool information. Ignore older tools requests and focus on the current tool selection. You must use the {selected_tool} tool to process their request. If requested tool is not available then use `retrieve_tools` to get the relevant tool information."

    # Handle workflow execution
    if selected_workflow:
        # Format workflow steps for execution
        workflow_steps = []
        tool_names = []
        for i, step in enumerate(selected_workflow.steps, 1):
            step_text = f"{i}. **{step['title']}** (Tool: {step['tool_name']})\n   Description: {step['description']}"
            workflow_steps.append(step_text)
            tool_names.append(step["tool_name"])

        workflow_steps_text = "\n".join(workflow_steps)
        tool_names_text = ", ".join(tool_names)

        # Create workflow execution prompt
        workflow_execution_message = WORKFLOW_EXECUTION_PROMPT.format(
            workflow_title=selected_workflow.title,
            workflow_description=selected_workflow.description,
            workflow_steps=workflow_steps_text,
            tool_names=tool_names_text,
            user_message=human_message_content
            or f"Execute workflow: {selected_workflow.title}",
        )

        # Replace the human message with the workflow execution prompt
        human_message_content = workflow_execution_message

    # If no human message then return error (but workflow execution should always have content now)
    if not human_message_content:
        raise ValueError("No human message or selected tool")

    # Add file information if files are uploaded
    if currently_uploaded_file_ids:
        human_message_content += f"\n\n{current_files_str}"

    # Add the human message
    chain_msgs.append(HumanMessage(content=human_message_content))

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

    content = "\n".join(
        f"- Name: {file.filename} Id: {file.fileId}" for file in files_data
    )

    content += "\n\nYou can use these files in your conversation. If you need to refer to them, use the file IDs provided."
    content += "\nYou must use query_files to retrieve file content or metadata."

    return content
