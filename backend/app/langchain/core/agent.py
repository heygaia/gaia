import asyncio
import json
from datetime import datetime, timezone
from typing import List

from app.config.loggers import llm_logger as logger
from app.langchain.core.graph_manager import GraphManager
from app.langchain.core.messages import construct_langchain_messages
from app.langchain.prompts.proactive_agent_prompt import (
    PROACTIVE_MAIL_AGENT_MESSAGE_PROMPT,
    PROACTIVE_MAIL_AGENT_SYSTEM_PROMPT,
)
from app.langchain.templates.mail_templates import MAIL_RECEIVED_USER_MESSAGE_TEMPLATE
from app.langchain.tools.core.categories import get_tool_category
from app.models.message_models import MessageRequestWithHistory
from app.models.workflow_models import WorkflowProcessingAgentResult
from app.utils.memory_utils import store_user_message_memory
from langchain_core.messages import (
    AIMessageChunk,
    AnyMessage,
)
from langchain_core.output_parsers import PydanticOutputParser
from langsmith import traceable
from pytz import timezone as timezone_pytz


@traceable
async def call_agent(
    request: MessageRequestWithHistory,
    conversation_id,
    user,
    timezone_name: str,
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
                user_timezone_name=timezone_name,
            ),
            GraphManager.get_graph(),
        )

        # Start memory storage in background - fire and forget
        asyncio.create_task(store_memory())

        initial_state = {
            "query": request.message,
            "messages": history,
            "force_web_search": request.search_web,
            "force_deep_research": request.deep_research,
            "current_datetime": datetime.now(timezone.utc).isoformat(),
            "mem0_user_id": user_id,
            "conversation_id": conversation_id,
            "selected_tool": request.selectedTool,  # Add selectedTool to agent state
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
                    "user_time": datetime.now(tz=timezone_pytz(timezone_name)),
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
            "status": "success",
        }

        logger.info(
            f"Email processing completed for user {user_id}. Tool data collected: {len(tool_data)}"
        )

        return processing_results
    except Exception as e:
        logger.error(f"Error in email processing for user {user_id}: {str(e)}")
        raise e


@traceable
async def call_workflow_agent(
    instruction: str,
    user_id: str,
    workflow_id: str,
    access_token: str | None = None,
    refresh_token: str | None = None,
    old_messages: List[AnyMessage] = [],
) -> WorkflowProcessingAgentResult:
    """
    Process workflow instruction with AI agent using the new workflow processing graph.

    Args:
        instruction: The workflow instruction to process
        user_id: User ID for context
        workflow_id: The workflow ID for context
        access_token: User's access token for API calls (maintained for compatibility)
        refresh_token: User's refresh token (maintained for compatibility)
        old_messages: Previous conversation messages for context

    Returns:
        WorkflowProcessingAgentResult: Structured result with title, body, and message
    """
    logger.info(
        f"Starting workflow processing for user {user_id} with new workflow graph"
    )

    try:
        # Import the new workflow processing graph
        from app.langchain.core.graph_builder.build_workflow_processing_graph import (
            build_workflow_processing_graph,
        )

        # Build the workflow processing graph
        async with build_workflow_processing_graph() as graph:
            logger.info(
                f"Workflow processing graph built successfully for user {user_id}"
            )

            # Convert old messages to the format expected by the new graph
            formatted_messages = []
            for msg in old_messages:
                formatted_messages.append(msg)  # Keep original message objects

            # Create initial state for the new workflow processing graph
            initial_state = {
                "input": instruction,
                "plan": [],  # Will be generated by the planning step
                "past_steps": [],
                "response": "",
                "metadata": {
                    "workflow_id": workflow_id,
                    "user_id": user_id,
                    "conversation_history": formatted_messages,
                },
            }

            # Execute the workflow using the new plan-execute graph
            result = await graph.ainvoke(
                initial_state,
                config={
                    "configurable": {
                        "thread_id": f"workflow_{workflow_id}",
                        "user_id": user_id,
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "workflow_id": workflow_id,
                        "initiator": "backend",
                    },
                    "recursion_limit": 9,  # Lower limit for workflow processing
                    "metadata": {
                        "user_id": user_id,
                        "processing_type": "workflow",
                    },
                },
            )

            logger.info(
                f"Workflow processing completed successfully for user {user_id}"
            )

            # Extract the final response from the workflow execution result
            final_response = result.get("response", "")
            if not final_response:
                # If no response in the result, try to extract from past_steps
                past_steps = result.get("past_steps", [])
                if past_steps and len(past_steps) > 0:
                    # Get the result from the last executed step
                    last_step = past_steps[-1]
                    if isinstance(last_step, dict) and "result" in last_step:
                        final_response = last_step["result"]
                    else:
                        final_response = str(last_step)

            if not final_response:
                logger.error(
                    f"No response generated from workflow processing for user {user_id}"
                )
                raise ValueError(
                    f"No response generated from workflow processing for user {user_id}"
                )

            # Create a structured result in the expected format
            # The new workflow graph doesn't use the old prompt format,
            # so we need to generate appropriate title, body, and message

            # For backward compatibility, create a simple notification format
            # In the future, the workflow graph could be enhanced to return structured results
            workflow_result = WorkflowProcessingAgentResult(
                title="Workflow Completed",
                body="Your workflow task has been completed successfully.",
                message=final_response,
            )

            logger.info(
                f"Successfully processed workflow for user {user_id}: {workflow_result.title}"
            )
            return workflow_result

    except Exception as e:
        logger.error(f"Error in workflow processing for user {user_id}: {str(e)}")
        raise e


workflow_agent_result_parser = PydanticOutputParser(
    pydantic_object=WorkflowProcessingAgentResult
)
