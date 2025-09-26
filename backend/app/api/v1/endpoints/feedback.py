from fastapi import APIRouter
from app.models.general_models import FeedbackFormData
from app.services.feedback_service import submit_feedback

router = APIRouter()


@router.post("/feedback")
async def submit_feedback_form(form_data: FeedbackFormData):
    return await submit_feedback(form_data)
