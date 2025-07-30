from typing import List, Optional
from fastapi import HTTPException
from langchain_core.messages import HumanMessage, SystemMessage, AnyMessage
from langsmith import traceable
from uuid_extensions import uuid7str

from app.langchain.prompts.convo_prompts import CONVERSATION_DESCRIPTION_GENERATOR
from app.langchain.core.state import State
from app.models.message_models import MessageDict
from app.langchain.llm.chatbot import chatbot

# from uuid_extensions import uuid7, uuid7str
from app.services.conversation_service import (
    ConversationModel,
    create_conversation_service,
)


@traceable(name="Create Conversation")
async def create_conversation(
    last_message: MessageDict | None, user: dict, selectedTool: Optional[str] | None
) -> dict:
    uuid_value = uuid7str()

    # If last_message is None or doesn't have content, use a fallback prompt
    user_message = (
        last_message.get("content")
        if last_message and "content" in last_message
        else "New conversation started"
    )

    response = await do_prompt_no_stream(
        prompt=CONVERSATION_DESCRIPTION_GENERATOR.format(
            user_message=user_message, selectedTool=selectedTool
        ),
    )

    # Validate LLM response
    if not isinstance(response, dict) or "response" not in response:
        raise HTTPException(status_code=500, detail="Invalid response from LLM")

    description = response.get("response", "New Chat").replace('"', "").strip()

    conversation = ConversationModel(
        conversation_id=str(uuid_value), description=description
    )

    await create_conversation_service(conversation, user)

    return {
        "conversation_id": conversation.conversation_id,
        "conversation_description": conversation.description,
    }


async def do_prompt_no_stream(
    prompt: str,
    system_prompt: str | None = None,
    use_tools: bool = False,
) -> dict:
    messages: List[AnyMessage] = (
        [SystemMessage(content=system_prompt)] if system_prompt else []
    )
    messages.append(HumanMessage(content=prompt))

    state = State(messages=messages)

    response = await chatbot(state)

    # Extract the AI's response content
    ai_message = response["messages"][0]

    return {"response": ai_message.content}
