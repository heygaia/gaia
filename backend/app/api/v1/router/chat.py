from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies.oauth_dependencies import (
    get_current_user,
    get_user_timezone,
)
from app.middleware.tiered_rate_limiter import tiered_rate_limit
from app.models.message_models import MessageRequestWithHistory
from app.services.chat_service import chat_stream

router = APIRouter()


@router.post("/chat-stream")
@tiered_rate_limit("chat_messages")
async def chat_stream_endpoint(
    body: MessageRequestWithHistory,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
    timezone_name: str = Depends(get_user_timezone),
) -> StreamingResponse:
    """
    Stream chat messages in real time.
    """

    return StreamingResponse(
        chat_stream(
            body=body,
            user=user,
            background_tasks=background_tasks,
            timezone_name=timezone_name,
        ),
        media_type="text/event-stream",
    )
