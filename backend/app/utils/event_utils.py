"""
Service for creating and managing email summary workflows.
"""

from datetime import datetime
from typing import Optional

from pytz import timezone as pytz_timezone

from app.config.loggers import general_logger as logger
from app.langchain.prompts.mail_prompts import SUMMARIZE_PREVIOUS_DAY_EMAILS
from app.models.workflow_models import CreateWorkflowRequest, WorkflowPayload
from app.services.workflow_service import create_workflow


async def create_email_summary_workflow(
    user_id: str, user_timezone: str = "UTC"
) -> Optional[str]:
    """
    Create a daily email summary workflow for a user.

    Args:
        user_id: The user's ID
        user_timezone: The user's timezone (default: UTC)

    Returns:
        The ID of the created workflows, or None if creation failed
    """
    try:
        # Get timezone-aware datetime
        user_tz = pytz_timezone(user_timezone)

        # Create payload
        payload = WorkflowPayload(
            instructions=SUMMARIZE_PREVIOUS_DAY_EMAILS,
            context=f"""
            This workflow executes daily to summarize the user's emails from the previous day.
            Workflow will run at 9:00 AM in the user's timezone.
            User's timezone is {user_tz.tzname} with offset {user_tz.utcoffset(datetime.now()).total_seconds() / 3600} hours.
            """,
        )

        # Define cron expression for daily execution at 9:00 AM
        cron_expr = "0 9 * * *"  # Daily at 9:00 AM

        # Create workflow request
        workflow_request = CreateWorkflowRequest(
            scheduled_at=None,
            repeat=cron_expr,
            payload=payload,
            stop_after=None,
            max_occurrences=None,
            conversation_id=None,
            base_time=datetime.now(user_tz),
        )

        # Create the workflow
        workflow_id = await create_workflow(
            workflow_data=workflow_request, user_id=user_id
        )

        logger.info(f"Created email summary workflow {workflow_id} for user {user_id}")
        return workflow_id

    except Exception as e:
        logger.error(
            f"Failed to create email summary workflow for user {user_id}: {str(e)}"
        )
        raise e
