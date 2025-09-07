import asyncio
import json
from datetime import datetime, timezone
from typing import Optional

from app.config.loggers import llm_logger as logger
from app.langchain.core.graph_manager import GraphManager
from app.langchain.core.messages import construct_langchain_messages
from app.langchain.prompts.proactive_agent_prompt import (
    PROACTIVE_MAIL_AGENT_MESSAGE_PROMPT,
    PROACTIVE_MAIL_AGENT_SYSTEM_PROMPT,
)
from app.langchain.templates.mail_templates import MAIL_RECEIVED_USER_MESSAGE_TEMPLATE
from app.langchain.tools.core.registry import tool_registry
from app.models.message_models import MessageRequestWithHistory
from app.models.models_models import ModelConfig
from app.utils.memory_utils import store_user_message_memory
from langchain_core.messages import (
    AIMessageChunk,
)
from langsmith import traceable


@traceable(run_type="llm", name="Call Agent")
async def call_agent(
    request: MessageRequestWithHistory,
    conversation_id,
    user,
    user_time: datetime,
    user_model_config: Optional[ModelConfig] = None,
):
    user_id = user.get("user_id")
    messages = request.messages
    complete_message = ""

    async def store_memory():
        """Store memory in background."""
        try:
            if user_id and request.message:
                await store_user_message_memory(
                    user_id, request.message, conversation_id
                )
        except Exception as e:
            logger.error(f"Error in background memory storage: {e}")

    try:
        # First gather: Setup operations that can run in parallel
        history_task = construct_langchain_messages(
            messages=messages,
            files_data=request.fileData,
            currently_uploaded_file_ids=request.fileIds,
            user_id=user_id,
            query=request.message,
            user_name=user.get("name"),
            selected_tool=request.selectedTool,
        )
        graph_task = GraphManager.get_graph()

        history, graph = await asyncio.gather(history_task, graph_task)

        # Start memory storage in background - fire and forget
        asyncio.create_task(store_memory())

        initial_state = {
            "query": request.message,
            "messages": history,
            "current_datetime": datetime.now(timezone.utc).isoformat(),
            "mem0_user_id": user_id,
            "conversation_id": conversation_id,
            "selected_tool": request.selectedTool,
            "selected_workflow": request.selectedWorkflow,
        }

        # Begin streaming the AI output
        config = {
            "configurable": {
                "thread_id": conversation_id,
                "user_id": user_id,
                "email": user.get("email"),
                "user_time": user_time.isoformat(),
                "model_configurations": {
                    "model_name": (
                        user_model_config.provider_model_name
                        if user_model_config
                        else None
                    ),
                    "provider": user_model_config.inference_provider.value
                    if user_model_config
                    else None,
                    "max_tokens": (
                        user_model_config.max_tokens if user_model_config else None
                    ),
                },
            },
            "recursion_limit": 25,
            "metadata": {"user_id": user_id},
        }

        async for event in graph.astream(
            initial_state,
            stream_mode=["messages", "custom"],
            config=config,
            subgraphs=True,
        ):
            # Handle subgraph events - when subgraphs=True, events are tuples with 3 elements
            ns, stream_mode, payload = event
            is_main_agent = len(ns) == 0

            if stream_mode == "messages":
                chunk, metadata = payload
                if chunk is None:
                    continue

                # If we remove this check, all tool outputs will be yielded
                if isinstance(chunk, AIMessageChunk):
                    content = str(chunk.content)
                    tool_calls = chunk.tool_calls

                    if tool_calls:
                        for tool_call in tool_calls:
                            logger.info(f"{tool_call=}")
                            tool_name_raw = tool_call.get("name")
                            if tool_name_raw:
                                tool_name = tool_name_raw.replace("_", " ").title()
                                tool_category = tool_registry.get_category_of_tool(
                                    tool_name_raw
                                )
                                progress_data = {
                                    "progress": {
                                        "message": f"Executing {tool_name}...",
                                        "tool_name": tool_name_raw,
                                        "tool_category": tool_category,
                                    }
                                }
                                yield f"data: {json.dumps(progress_data)}\n\n"

                    # Only yield content from the main agent to avoid duplication
                    if content and is_main_agent:
                        yield f"data: {json.dumps({'response': content})}\n\n"
                        complete_message += content

            elif stream_mode == "custom":
                yield f"data: {json.dumps(payload)}\n\n"

        # After streaming, yield complete message in order to store in db
        yield f"nostream: {json.dumps({'complete_message': complete_message})}"

        yield "data: [DONE]\n\n"

    except Exception as e:
        logger.error(f"Error when calling agent: {e}")
        error_dict = {
            "error": f"Error when calling agent: {e}",
        }
        yield f"data: {json.dumps(error_dict)}\n\n"
        yield "data: [DONE]\n\n"


@traceable
async def call_agent_silent(
    request: MessageRequestWithHistory,
    conversation_id,
    user,
    user_time: datetime,
    access_token=None,
    refresh_token=None,
) -> tuple[str, dict]:
    """
    Execute agent in silent mode for background processing.
    Returns (complete_message, tool_data) without streaming.

    This reuses the same graph execution logic as call_agent() but captures
    tool data without yielding stream chunks.
    """
    from app.services.chat_service import extract_tool_data

    user_id = user.get("user_id")
    messages = request.messages
    complete_message = ""
    tool_data = {}

    async def store_memory():
        """Store memory in background."""
        try:
            if user_id and request.message:
                await store_user_message_memory(
                    user_id, request.message, conversation_id
                )
        except Exception as e:
            logger.error(f"Error in background memory storage: {e}")

    try:
        # Setup operations that can run in parallel
        history = await construct_langchain_messages(
            messages=messages,
            files_data=request.fileData,
            currently_uploaded_file_ids=request.fileIds,
            user_id=user_id,
            query=request.message,
            user_name=user.get("name"),
            selected_tool=request.selectedTool,
            selected_workflow=request.selectedWorkflow,
        )

        # Use the default graph (same as normal chat)
        graph = await GraphManager.get_graph()

        # Start memory storage in background
        asyncio.create_task(store_memory())

        initial_state = {
            "query": request.message,
            "messages": history,
            "current_datetime": datetime.now(timezone.utc).isoformat(),
            "mem0_user_id": user_id,
            "conversation_id": conversation_id,
            "selected_tool": request.selectedTool,
            "selected_workflow": request.selectedWorkflow,
        }

        # Execute graph and capture tool data silently
        async for event in graph.astream(
            initial_state,
            stream_mode=["messages", "custom"],
            config={
                "configurable": {
                    "thread_id": conversation_id,
                    "user_id": user_id,
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "email": user.get("email"),
                    "user_time": user_time.isoformat(),
                },
                "recursion_limit": 25,
                "metadata": {"user_id": user_id},
            },
        ):
            stream_mode, payload = event

            if stream_mode == "messages":
                chunk, metadata = payload
                if chunk is None:
                    continue

                if isinstance(chunk, AIMessageChunk):
                    content = str(chunk.content)
                    if content:
                        complete_message += content

            elif stream_mode == "custom":
                # Extract tool data from custom stream events
                try:
                    new_data = extract_tool_data(json.dumps(payload))
                    if new_data:
                        tool_data.update(new_data)
                except Exception as e:
                    logger.error(f"Error extracting tool data in silent mode: {e}")

        return complete_message, tool_data

    except Exception as e:
        logger.error(f"Error in call_agent_silent: {e}")
        return f"❌ Error executing workflow: {str(e)}", {}


@traceable
async def call_mail_processing_agent(
    email_content: str,
    user_id: str,
    email_metadata: dict | None = None,
):
    """
    Process incoming email with AI agent to take appropriate actions.

    Args:
        email_content: The email content to process
        user_id: User ID for context
        email_metadata: Additional email metadata (sender, subject, etc.)
        access_token: User's access token for API calls
        refresh_token: User's refresh token

    Returns:
        dict: Processing results with actions taken
    """
    logger.info(
        f"Starting email processing for user {user_id} with email content length: {len(email_content)}"
    )

    email_metadata = email_metadata or {}

    # Construct the message with system prompt and email content
    messages = [
        {"role": "system", "content": PROACTIVE_MAIL_AGENT_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": PROACTIVE_MAIL_AGENT_MESSAGE_PROMPT.format(
                email_content=email_content,
                subject=email_metadata.get("subject", "No Subject"),
                sender=email_metadata.get("sender", "Unknown Sender"),
                date=email_metadata.get("date", "Unknown Date"),
            ),
        },
    ]

    logger.info(
        f"Processing email for user {user_id} with subject: {email_metadata.get('subject', 'No Subject')}"
    )

    # Generate a unique processing ID for this email
    processing_id = f"email_processing_{user_id}_{int(datetime.now().timestamp())}"

    initial_state = {
        "input": email_content,  # Use 'input' instead of 'messages' for EmailPlanExecute state
        "messages": messages,
        "current_datetime": datetime.now(timezone.utc).isoformat(),
        "mem0_user_id": user_id,
        "email_metadata": email_metadata,
        "processing_id": processing_id,
    }

    complete_message = ""
    tool_data = {}
    try:
        # Get the email processing graph
        graph = await GraphManager.get_graph("mail_processing")

        if not graph:
            logger.error(f"No graph found for email processing for user {user_id}")
            raise ValueError(f"Graph not found for email processing: {user_id}")

        logger.info(
            f"Graph for email processing retrieved successfully for user {user_id}"
        )

        # Stream the graph execution to collect both message and tool data
        async for event in graph.astream(
            initial_state,
            stream_mode=["messages", "custom"],
            config={
                "configurable": {
                    "thread_id": processing_id,
                    "user_id": user_id,
                    "initiator": "backend",  # This will be used to identify either to send notification or stream to the user
                },
                "recursion_limit": 25,  # Increased limit for complex email processing
                "metadata": {
                    "user_id": user_id,
                    "processing_type": "email",
                    "email_subject": email_metadata.get("subject", ""),
                },
            },
        ):
            stream_mode, payload = event
            if stream_mode == "messages":
                chunk, metadata = payload
                if chunk is None:
                    continue

                # Collect AI message content
                if isinstance(chunk, AIMessageChunk):
                    content = str(chunk.content)
                    if content:
                        complete_message += content

            elif stream_mode == "custom":
                # Extract tool data from custom stream events
                from app.services.chat_service import extract_tool_data

                try:
                    new_data = extract_tool_data(json.dumps(payload))
                    if new_data:
                        tool_data.update(new_data)
                except Exception as e:
                    logger.error(
                        f"Error extracting tool data during email processing: {e}"
                    )

        # Prepare results with conversation data for process_email to handle
        processing_results = {
            "conversation_data": {
                "conversation_id": user_id,  # Use user_id as conversation_id
                "user_message_content": MAIL_RECEIVED_USER_MESSAGE_TEMPLATE.format(
                    subject=email_metadata.get("subject", "No Subject"),
                    sender=email_metadata.get("sender", "Unknown Sender"),
                    snippet=email_content.strip()[:200]
                    + ("..." if len(email_content.strip()) > 200 else ""),
                ),
                "bot_message_content": complete_message,
                "tool_data": tool_data,
            },
        }

        logger.info(
            f"Email processing completed for user {user_id}. Tool data collected: {len(tool_data)}"
        )

        return processing_results
    except Exception as e:
        logger.error(f"Error in email processing for user {user_id}: {str(e)}")
        raise e
