import asyncio
import json
from datetime import datetime, timezone
from typing import List

from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    AnyMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_core.output_parsers import PydanticOutputParser
from langsmith import traceable

from app.config.loggers import llm_logger as logger
from app.langchain.core.graph_manager import GraphManager
from app.langchain.core.messages import construct_langchain_messages
from app.langchain.tools.core.categories import get_tool_category
from app.langchain.prompts.proactive_agent_prompt import (
    PROACTIVE_MAIL_AGENT_MESSAGE_PROMPT,
    PROACTIVE_MAIL_AGENT_SYSTEM_PROMPT,
    PROACTIVE_REMINDER_AGENT_MESSAGE_PROMPT,
    PROACTIVE_REMINDER_AGENT_SYSTEM_PROMPT,
)
from app.langchain.templates.mail_templates import MAIL_RECEIVED_USER_MESSAGE_TEMPLATE
from app.models.message_models import MessageRequestWithHistory
from app.models.reminder_models import ReminderProcessingAgentResult
from app.utils.memory_utils import store_user_message_memory


@traceable(run_type="llm", name="Call Agent")
async def call_agent(
    request: MessageRequestWithHistory,
    conversation_id,
    user,
    user_time: datetime,
    access_token=None,
    refresh_token=None,
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
        history, graph = await asyncio.gather(
            construct_langchain_messages(
                messages,
                files_data=request.fileData,
                currently_uploaded_file_ids=request.fileIds,
                user_id=user_id,
                query=request.message,
                user_name=user.get("name"),
                selected_tool=request.selectedTool,
            ),
            GraphManager.get_graph(),
        )

        # Start memory storage in background - fire and forget
        asyncio.create_task(store_memory())

        initial_state = {
            "query": request.message,
            "messages": history,
            "current_datetime": datetime.now(timezone.utc).isoformat(),
            "mem0_user_id": user_id,
            "conversation_id": conversation_id,
            "selected_tool": request.selectedTool,
        }

        # Begin streaming the AI output
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
                "recursion_limit": 15,
                "metadata": {"user_id": user_id},
            },
        ):
            stream_mode, payload = event

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
                                tool_category = get_tool_category(tool_name_raw)
                                progress_data = {
                                    "progress": {
                                        "message": f"Executing {tool_name}...",
                                        "tool_name": tool_name_raw,
                                        "tool_category": tool_category,
                                    }
                                }
                                yield f"data: {json.dumps(progress_data)}\n\n"

                    if content:
                        yield f"data: {json.dumps({'response': content})}\n\n"
                        complete_message += content

            elif stream_mode == "custom":
                yield f"data: {json.dumps(payload)}\n\n"

        # After streaming, yield complete message in order to store in db
        yield f"nostream: {json.dumps({'complete_message': complete_message})}"

        yield "data: [DONE]\n\n"

    except Exception as e:
        logger.error(f"Error when calling agent: {e}")
        yield "data: {'error': 'Error when calling agent:  {e}'}\n\n"
        yield "data: [DONE]\n\n"


@traceable
async def call_mail_processing_agent(
    email_content: str,
    user_id: str,
    email_metadata: dict | None = None,
    access_token: str | None = None,
    refresh_token: str | None = None,
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
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "initiator": "backend",  # This will be used to identify either to send notification or stream to the user
                },
                "recursion_limit": 15,  # Lower limit for email processing
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


@traceable
async def call_reminder_agent(
    instruction: str,
    user_id: str,
    reminder_id: str,
    access_token: str | None = None,
    refresh_token: str | None = None,
    old_messages: List[AnyMessage] = [],
) -> ReminderProcessingAgentResult:
    """
    Process reminder instruction with AI agent to process a reminder.

    Args:
        instruction: The reminder instruction to process
        user_id: User ID for context
        access_token: User's access token for API calls
        refresh_token: User's refresh token

    Returns:
        None: This function is designed to run as a background task
    """
    logger.info(f"Starting reminder processing for user {user_id}")

    messages = [
        SystemMessage(
            content=PROACTIVE_REMINDER_AGENT_SYSTEM_PROMPT,
        ),
        *old_messages,
        HumanMessage(
            content=PROACTIVE_REMINDER_AGENT_MESSAGE_PROMPT.format(
                reminder_request=instruction,
                format_instructions=reminder_agent_result_parser.get_format_instructions(),
            )
        ),
    ]

    logger.info(f"Processing reminder for user {user_id}")

    initial_state = {
        "messages": messages,
        "current_datetime": datetime.now(timezone.utc).isoformat(),
        "mem0_user_id": user_id,
    }

    try:
        # Get the reminder processing graph
        graph = await GraphManager.get_graph("reminder_processing")

        if not graph:
            logger.error(f"No graph found for reminder processing for user {user_id}")
            raise ValueError(f"Graph not found for reminder processing: {user_id}")

        logger.info(
            f"Graph for reminder processing retrieved successfully for user {user_id}"
        )

        # Just invoke the graph directly - no streaming needed
        result = await graph.ainvoke(
            initial_state,
            config={
                "configurable": {
                    "thread_id": f"reminder_{reminder_id}",
                    "user_id": user_id,
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "reminder_id": reminder_id,
                    "initiator": "backend",
                },
                "recursion_limit": 9,  # Lower limit for reminder processing
                "metadata": {
                    "user_id": user_id,
                    "processing_type": "reminder",
                },
            },
        )

        if not result:
            logger.warning(
                f"No result returned from reminder processing for user {user_id}"
            )
            raise ValueError(
                f"No result returned from reminder processing for user {user_id}"
            )

        # Extract the AI response from the messages
        ai_response = None
        if "messages" in result:
            last_message = result["messages"][-1]
            if isinstance(last_message, AIMessage):
                ai_response = last_message.content

        if not ai_response:
            logger.error(f"No AI response found in result for user {user_id}")
            raise ValueError(f"No AI response found in result for user {user_id}")

        logger.info(f"AI response content: {ai_response}")

        # Parse the AI response using the parser
        try:
            parsed_result = reminder_agent_result_parser.parse(ai_response)  # type: ignore
            logger.info(f"Successfully parsed reminder result: {parsed_result}")

            return parsed_result
        except Exception as parse_error:
            logger.error(f"Failed to parse AI response with parser: {parse_error}")
            raise ValueError(
                f"Failed to parse AI response for reminder {reminder_id} for user {user_id}: {parse_error}"
            )
    except Exception as e:
        logger.error(f"Error in reminder processing for user {user_id}: {str(e)}")
        # Handle the error as needed, e.g., log it, notify the user, etc.
        raise e


reminder_agent_result_parser = PydanticOutputParser(
    pydantic_object=ReminderProcessingAgentResult
)
