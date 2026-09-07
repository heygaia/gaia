from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.v1.dependencies.oauth_dependencies import get_current_user
from app.models.first_steps_models import FirstStepsResponse
from app.models.user_models import AuthenticatedUser
from app.services.first_steps_service import dismiss_first_steps, get_first_steps
from shared.py.wide_events import log

router = APIRouter(prefix="/users/me/first-steps", tags=["First Steps"])


@router.get("")
async def read_first_steps(
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> FirstStepsResponse:
    """The activation checklist; every ``done`` is derived server-side."""
    log.set(user={"id": user["user_id"]}, first_steps={"operation": "read"})
    checklist = await get_first_steps(user["user_id"])
    log.set_ns(
        "first_steps",
        done=sum(step.done for step in checklist.steps),
        dismissed=checklist.dismissed,
    )
    return checklist


@router.post("/dismiss")
async def dismiss(
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> FirstStepsResponse:
    """Hide the checklist. Idempotent."""
    log.set(user={"id": user["user_id"]}, first_steps={"operation": "dismiss"})
    checklist = await dismiss_first_steps(user["user_id"])
    log.set_ns("first_steps", done=sum(step.done for step in checklist.steps), dismissed=True)
    return checklist
