"""Reminder LangChain tools."""

import json
from datetime import datetime
from typing import Annotated, Any, Optional, Union

from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools import tool

from app.config.loggers import reminders_logger as logger
from app.decorators import with_rate_limiting, with_doc
from app.docstrings.langchain.tools.reminder_tool_docs import (
    CREATE_REMINDER,
    DELETE_REMINDER,
    GET_REMINDER,
    LIST_USER_REMINDERS,
    SEARCH_REMINDERS,
    UPDATE_REMINDER,
)
from app.models.reminder_models import (
    AgentType,
    AIAgentReminderPayload,
    CreateReminderRequest,
    ReminderStatus,
    StaticReminderPayload,
)
from app.services.reminder_service import (
    cancel_reminder as svc_delete_reminder,
)
from app.services.reminder_service import (
    create_reminder as svc_create_reminder,
)
from app.services.reminder_service import (
    get_reminder as svc_get_reminder,
)
from app.services.reminder_service import (
    list_user_reminders as svc_list_user_reminders,
)
from app.services.reminder_service import (
    update_reminder as svc_update_reminder,
)
from app.utils.timezone import replace_timezone_info


@tool()
@with_rate_limiting("reminder_operations")
@with_doc(CREATE_REMINDER)
async def create_reminder_tool(
    config: RunnableConfig,
    payload: Annotated[
        Union[AIAgentReminderPayload, StaticReminderPayload],
        "Additional data for the reminder task",
    ],
    agent: Annotated[
        AgentType, "The agent type creating the reminder"
    ] = AgentType.STATIC,
    repeat: Annotated[Optional[str], "Cron expression for recurring reminders"] = None,
    scheduled_at: Annotated[
        Optional[str],
        "ISO 8601 formatted date/time for when the reminder should run",
    ] = None,
    max_occurrences: Annotated[
        Optional[int],
        "Maximum number of times to run the reminder. Use this when user explicitly sets a limit on how many times the reminder should run.",
    ] = None,
    stop_after: Annotated[
        Optional[str],
        "ISO 8601 formatted date/time after which no more runs. Use this when user explicitly sets a date/time after which the reminder should not run anymore.",
    ] = None,
) -> Any:
    """Create a new reminder tool function."""
    try:
        user_id = config.get("configurable", {}).get("user_id")
        if not user_id:
            return {"error": "User ID is required to create a reminder"}

        user_time_str: str = config.get("configurable", {}).get("user_time", "")
        if not user_time_str:
            return {"error": "User time is required to create a reminder"}

        if scheduled_at:
            try:
                scheduled_at = replace_timezone_info(
                    scheduled_at,
                    timezone_source=user_time_str,
                ).isoformat()
            except ValueError:
                logger.error(f"Invalid scheduled_at format: {scheduled_at}")
                return {"error": "Invalid scheduled_at format. Use ISO 8601 format."}

        if stop_after:
            try:
                stop_after = replace_timezone_info(
                    stop_after,
                    timezone_source=user_time_str,
                ).isoformat()
            except ValueError:
                logger.error(f"Invalid stop_after format {stop_after}")
                return {"error": "Invalid stop_after format. Use ISO 8601 format."}

        data: dict[str, Any] = {
            "agent": agent,
            "payload": payload,
            "repeat": repeat,
            "max_occurrences": max_occurrences,
            "stop_after": datetime.fromisoformat(stop_after) if stop_after else None,
            "scheduled_at": (
                datetime.fromisoformat(scheduled_at) if scheduled_at else None
            ),
            "base_time": datetime.fromisoformat(user_time_str),
        }

        request_model = CreateReminderRequest(**data)
        await svc_create_reminder(request_model, user_id=user_id)

        return "Reminder created successfully"

    except Exception as e:
        logger.exception("Exception occurred while creating reminder")
        return {"error": str(e)}


@tool(parse_docstring=True)
@with_rate_limiting("reminder_operations")
@with_doc(LIST_USER_REMINDERS)
async def list_user_reminders_tool(
    config: RunnableConfig,
    status: Annotated[
        Optional[ReminderStatus],
        "Filter by reminder status (scheduled, completed, cancelled, paused)",
    ] = None,
) -> Any:
    """List user reminders tool function."""
    try:
        user_id = config.get("configurable", {}).get("user_id")
        if not user_id:
            return {"error": "User ID is required to list reminders"}

        reminders = await svc_list_user_reminders(
            user_id=user_id, status=status, limit=100, skip=0
        )
        return [r.model_dump() for r in reminders]
    except Exception as e:
        logger.exception("Exception occurred while listing reminders")
        return {"error": str(e)}


# Define get_reminder_tool
@tool(parse_docstring=True)
@with_rate_limiting("reminder_operations")
@with_doc(GET_REMINDER)
async def get_reminder_tool(
    config: RunnableConfig,
    reminder_id: Annotated[str, "The unique identifier of the reminder"],
) -> Any:
    """Get full details of a specific reminder by ID"""
    try:
        user_id = config.get("configurable", {}).get("user_id")
        if not user_id:
            return {"error": "User ID is required to get reminder"}

        reminder = await svc_get_reminder(reminder_id, user_id)
        if reminder:
            return reminder.model_dump()
        else:
            return {"error": "Reminder not found"}
    except Exception as e:
        logger.exception("Exception occurred while getting reminder")
        return {"error": str(e)}


# Define delete_reminder_tool
@tool(parse_docstring=True)
@with_rate_limiting("reminder_operations")
@with_doc(DELETE_REMINDER)
async def delete_reminder_tool(
    config: RunnableConfig,
    reminder_id: Annotated[str, "The unique identifier of the reminder to cancel"],
) -> Any:
    """Cancel a scheduled reminder by ID"""
    try:
        user_id = config.get("configurable", {}).get("user_id")
        if not user_id:
            logger.error("Missing user_id in config")
            return {"error": "User ID is required to delete reminder"}

        success = await svc_delete_reminder(reminder_id, user_id)
        if success:
            return {"status": "cancelled"}
        else:
            return {"error": "Failed to cancel reminder"}
    except Exception as e:
        logger.exception("Exception occurred while deleting reminder")
        return {"error": str(e)}


# Define update_reminder_tool
@tool(parse_docstring=True)
@with_rate_limiting("reminder_operations")
@with_doc(UPDATE_REMINDER)
async def update_reminder_tool(
    config: RunnableConfig,
    reminder_id: Annotated[str, "The unique identifier of the reminder to update"],
    repeat: Annotated[
        Optional[str], "Cron expression for recurring reminders (optional)"
    ] = None,
    max_occurrences: Annotated[
        Optional[int], "Maximum number of times to run the reminder (optional)"
    ] = None,
    stop_after: Annotated[
        Optional[str],
        "ISO 8601 formatted date/time after which no more runs (optional)",
    ] = None,
    payload: Annotated[
        Optional[dict], "Additional data for the reminder task (optional)"
    ] = None,
) -> Any:
    """Update attributes of an existing reminder"""
    try:
        user_id = config.get("configurable", {}).get("user_id")
        if not user_id:
            return {"error": "User ID is required to update reminder"}

        update_data: dict[str, Any] = {}
        if repeat is not None:
            update_data["repeat"] = repeat
        if max_occurrences is not None:
            update_data["max_occurrences"] = max_occurrences
        if stop_after:
            update_data["stop_after"] = datetime.fromisoformat(stop_after)
        if payload is not None:
            update_data["payload"] = payload

        success = await svc_update_reminder(reminder_id, update_data, user_id)
        if success:
            return {"status": "updated"}
        else:
            logger.error("Failed to update reminder")
            return {"error": "Failed to update reminder"}
    except Exception as e:
        logger.exception("Exception occurred while updating reminder")
        return {"error": str(e)}


# Define search_reminders_tool
@tool(parse_docstring=True)
@with_rate_limiting("reminder_operations")
@with_doc(SEARCH_REMINDERS)
async def search_reminders_tool(
    config: RunnableConfig,
    query: Annotated[str, "Search keyword(s) to match against reminders"],
) -> Any:
    """Search reminders by keyword or content"""
    try:
        user_id = config.get("configurable", {}).get("user_id")
        if not user_id:
            logger.error("Missing user_id in config")
            return {"error": "User ID is required to search reminders"}

        reminders = await svc_list_user_reminders(user_id=user_id, limit=100, skip=0)

        results = []
        for r in reminders:
            rd = r.model_dump()
            if query.lower() in json.dumps(rd).lower():
                results.append(rd)

        return results
    except Exception as e:
        logger.exception("Exception occurred while searching reminders")
        return {"error": str(e)}


tools = [
    create_reminder_tool,
    list_user_reminders_tool,
    get_reminder_tool,
    delete_reminder_tool,
    update_reminder_tool,
    search_reminders_tool,
]
