import json
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, Optional

from fastapi import BackgroundTasks

from app.config.loggers import chat_logger as logger
from app.langchain.core.agent import call_agent
from app.models.chat_models import MessageModel, UpdateMessagesRequest
from app.models.message_models import MessageRequestWithHistory
from app.services.conversation_service import update_messages
from app.services.file_service import get_files
from app.utils.chat_utils import create_conversation


async def chat_stream(
    body: MessageRequestWithHistory,
    user: dict,
    background_tasks: BackgroundTasks,
    user_time: datetime,
) -> AsyncGenerator:
    """
    Stream chat messages in real-time.

    Returns:
        StreamingResponse: A streaming response containing the LLM's generated content
    """
    complete_message = ""
    conversation_id, init_chunk = await initialize_conversation(body, user)

    # Dictionary to collect tool outputs during streaming
    tool_data: Dict[str, Any] = {}

    if init_chunk:  # Return the conversation id and metadata if new convo
        yield init_chunk

    logger.info(
        f"User {user.get('user_id')} started a conversation with ID {conversation_id}"
    )

    # Log the user's message if messages exist
    if body.messages:
        message_content = body.messages[-1].get("content", "") if body.messages else ""
        logger.info(f"User {user.get('user_id')} sent a message: {message_content}")
    else:
        logger.info(
            f"User {user.get('user_id')} sent a request with selected tool: {body.selectedTool}"
        )

    # Stream response from the agent
    async for chunk in call_agent(
        request=body,
        user=user,
        conversation_id=conversation_id,
        access_token=user.get("access_token"),
        refresh_token=user.get("refresh_token"),
        user_time=user_time,
    ):
        # Process complete message marker
        if chunk.startswith("nostream: "):
            # So that we can return data that doesn't need to be streamed
            chunk_json = json.loads(chunk.replace("nostream: ", ""))
            complete_message = chunk_json.get("complete_message", "")
        # Process data chunk - potentially contains tool outputs
        elif chunk.startswith("data: "):
            try:
                # Extract tool data from the chunk
                new_data = extract_tool_data(chunk[6:])
                if new_data:
                    tool_data.update(new_data)
            except Exception as e:
                logger.error(f"Error extracting tool data: {e}")
            yield chunk
        # Pass through other chunks
        else:
            yield chunk

    # Save the conversation once streaming is complete
    update_conversation_messages(
        background_tasks, body, user, conversation_id, complete_message, tool_data
    )


def extract_tool_data(json_str: str) -> Dict[str, Any]:
    """
    Parse and extract structured tool output from an agent's JSON response chunk.

    This function is responsible for detecting and extracting specific tool-related data (e.g., calendar options, search results, weather data,
    image generation outputs) from a JSON string sent during streaming.

    Returns:
        Dict[str, Any]: A dictionary containing extracted structured data.

    Notes:
        - This is meant to handle tool response metadata during streaming.
        - If the JSON is malformed or does not match known tool structures, an empty dict is returned.
        - This function is tolerant to missing keys and safe for runtime use in an async stream.
    """
    try:
        data = json.loads(json_str)

        # Extract all tool keys dynamically from MessageModel
        # Exclude basic message fields and only include tool-related fields
        excluded_fields = {
            "type",
            "response",
            "date",
            "disclaimer",
            "subtype",
            "file",
            "filename",
            "filetype",
            "message_id",
            "fileIds",
            "fileData",
            "selectedTool",
            "toolCategory",
        }

        tool_keys = {
            field_name
            for field_name in MessageModel.model_fields.keys()
            if field_name not in excluded_fields
        }

        # Extract any matching tool data
        return {key: data[key] for key in tool_keys if key in data}

    except json.JSONDecodeError:
        return {}


async def initialize_conversation(
    body: MessageRequestWithHistory, user: dict
) -> tuple[str, Optional[str]]:
    """
    Initialize a conversation or use an existing one.

    Args:
        body: The request body
        user: User information

    Returns:
        Tuple of conversation ID and initialization chunk (if any)
    """
    conversation_id = body.conversation_id or None
    init_chunk = None

    if conversation_id is None:
        last_message = body.messages[-1] if body.messages else None
        selectedTool = body.selectedTool if body.selectedTool else None
        conversation = await create_conversation(
            last_message, user=user, selectedTool=selectedTool
        )
        conversation_id = conversation.get("conversation_id", "")

        init_chunk = f"""data: {
            json.dumps(
                {
                    "conversation_id": conversation_id,
                    "conversation_description": conversation.get("description"),
                }
            )
        }\n\n"""

        return conversation_id, init_chunk

    # Load files and old messages if conversation_id is provided
    uploaded_files = await get_files(
        user_id=user.get("user_id"),
        conversation_id=conversation_id,
    )

    logger.info(f"{uploaded_files=}")

    return conversation_id, init_chunk


def update_conversation_messages(
    background_tasks: BackgroundTasks,
    body: MessageRequestWithHistory,
    user: dict,
    conversation_id: str,
    complete_message: str,
    tool_data: Dict[str, Any] = {},
) -> None:
    """
    Schedule conversation update in the background.

    Args:
        background_tasks: FastAPI background task handler
        body: Request body
        user: User information
        conversation_id: ID of the conversation to update
        complete_message: Complete LLM-generated message
        tool_data: Structured tool output data to store with the message
    """
    # Create user message - handle case where messages array might be empty due to tool selection
    user_content = body.messages[-1]["content"] if body.messages else body.message
    user_message = MessageModel(
        type="user",
        response=user_content,
        date=datetime.now(timezone.utc).isoformat(),
        fileIds=body.fileIds,
        selectedTool=body.selectedTool,
        toolCategory=body.toolCategory,
    )

    # Create bot message with base properties
    bot_message = MessageModel(
        type="bot",
        response=complete_message,
        date=datetime.now(timezone.utc).isoformat(),
        fileIds=body.fileIds,
    )

    # Apply tool data fields to bot message if available
    if tool_data:
        # Use dictionary unpacking for cleaner application of fields
        for key, value in tool_data.items():
            setattr(bot_message, key, value)

    # Schedule the DB update as a background task
    background_tasks.add_task(
        update_messages,
        UpdateMessagesRequest(
            conversation_id=conversation_id,
            messages=[user_message, bot_message],
        ),
        user=user,
    )
