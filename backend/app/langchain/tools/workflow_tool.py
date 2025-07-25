"""Workflow LangChain tools."""

import json
from datetime import datetime
from typing import Annotated, Any, Optional

from app.config.loggers import workflow_logger as logger
from app.docstrings.langchain.tools.workflow_tool_docs import (
    CREATE_WORKFLOW,
    DELETE_WORKFLOW,
    GET_WORKFLOW,
    LIST_USER_WORKFLOWS,
    SEARCH_WORKFLOWS,
    UPDATE_WORKFLOW,
)
from app.docstrings.utils import with_doc
from app.middleware.langchain_rate_limiter import with_rate_limiting
from app.models.arq_event_models import EventStatus
from app.models.workflow_models import (
    CreateWorkflowRequest,
    WorkflowPayload,
    WorkflowPayloadLLM,
)
from app.services.workflow_service import (
    cancel_workflow as svc_delete_workflow,
)
from app.services.workflow_service import (
    create_workflow as svc_create_workflow,
)
from app.services.workflow_service import (
    get_workflow as svc_get_workflow,
)
from app.services.workflow_service import (
    list_user_workflows as svc_list_user_workflows,
)
from app.services.workflow_service import (
    update_workflow as svc_update_workflow,
)
from app.utils.timezone import replace_timezone_info
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools import tool


@tool()
@with_rate_limiting("workflow_operations")
@with_doc(CREATE_WORKFLOW)
async def create_workflow_tool(
    config: RunnableConfig,
    payload: Annotated[WorkflowPayloadLLM, "Additional data for the workflow task"],
    repeat: Annotated[Optional[str], "Cron expression for recurring workflows"] = None,
    scheduled_at: Annotated[
        Optional[str],
        "ISO 8601 formatted date/time for when the workflow should run",
    ] = None,
    max_occurrences: Annotated[
        Optional[int],
        "Maximum number of times to run the workflow. Use this when user explicitly sets a limit on how many times the workflow should run.",
    ] = None,
    stop_after: Annotated[
        Optional[str],
        "ISO 8601 formatted date/time after which no more runs. Use this when user explicitly sets a date/time after which the workflow should not run anymore.",
    ] = None,
) -> Any:
    """Create a new workflow tool function."""
    try:
        user_id = config.get("configurable", {}).get("user_id")
        if not user_id:
            return {"error": "User ID is required to create a workflow"}

        user_time: Optional[datetime] = config.get("configurable", {}).get(
            "user_time", ""
        )
        if not user_time:
            return {"error": "User time is required to create a workflow"}

        if scheduled_at:
            try:
                scheduled_at = replace_timezone_info(
                    scheduled_at,
                    timezone_source=user_time,
                ).isoformat()
            except ValueError:
                logger.error(f"Invalid scheduled_at format: {scheduled_at}")
                return {"error": "Invalid scheduled_at format. Use ISO 8601 format."}

        if stop_after:
            try:
                stop_after = replace_timezone_info(
                    stop_after,
                    timezone_source=user_time,
                ).isoformat()
            except ValueError:
                logger.error(f"Invalid stop_after format {stop_after}")
                return {"error": "Invalid stop_after format. Use ISO 8601 format."}

        data: dict[str, Any] = {
            "payload": payload,
            "repeat": repeat,
            "max_occurrences": max_occurrences,
            "stop_after": datetime.fromisoformat(stop_after) if stop_after else None,
            "scheduled_at": (
                datetime.fromisoformat(scheduled_at) if scheduled_at else None
            ),
            "base_time": user_time,
        }

        request_model = CreateWorkflowRequest(**data)
        await svc_create_workflow(request_model, user_id=user_id)

        return "Workflow created successfully"

    except Exception as e:
        logger.exception("Exception occurred while creating workflow")
        return {"error": str(e)}


@tool(parse_docstring=True)
@with_rate_limiting("workflow_operations")
@with_doc(LIST_USER_WORKFLOWS)
async def list_user_workflows_tool(
    config: RunnableConfig,
    status: Annotated[
        Optional[EventStatus],
        "Filter by workflow status (scheduled, completed, cancelled, paused)",
    ] = None,
) -> Any:
    """List user workflows tool function."""
    try:
        user_id = config.get("configurable", {}).get("user_id")
        if not user_id:
            return {"error": "User ID is required to list workflows"}

        workflows = await svc_list_user_workflows(
            user_id=user_id, status=status, limit=100, skip=0
        )
        return [w.model_dump() for w in workflows]
    except Exception as e:
        logger.exception("Exception occurred while listing workflows")
        return {"error": str(e)}


@tool(parse_docstring=True)
@with_rate_limiting("workflow_operations")
@with_doc(GET_WORKFLOW)
async def get_workflow_tool(
    config: RunnableConfig,
    workflow_id: Annotated[str, "The unique identifier of the workflow"],
) -> Any:
    """Get full details of a specific workflow by ID"""
    try:
        user_id = config.get("configurable", {}).get("user_id")
        if not user_id:
            return {"error": "User ID is required to get workflow"}

        workflow = await svc_get_workflow(workflow_id, user_id)
        if workflow:
            return workflow.model_dump()
        else:
            return {"error": "Workflow not found"}
    except Exception as e:
        logger.exception("Exception occurred while getting workflow")
        return {"error": str(e)}


@tool(parse_docstring=True)
@with_rate_limiting("workflow_operations")
@with_doc(DELETE_WORKFLOW)
async def delete_workflow_tool(
    config: RunnableConfig,
    workflow_id: Annotated[str, "The unique identifier of the workflow to cancel"],
) -> Any:
    """Cancel a scheduled workflow by ID"""
    try:
        user_id = config.get("configurable", {}).get("user_id")
        if not user_id:
            logger.error("Missing user_id in config")
            return {"error": "User ID is required to delete workflow"}

        success = await svc_delete_workflow(workflow_id, user_id)
        if success:
            return {"status": "cancelled"}
        else:
            return {"error": "Failed to cancel workflow"}
    except Exception as e:
        logger.exception("Exception occurred while deleting workflow")
        return {"error": str(e)}


@tool(parse_docstring=True)
@with_rate_limiting("workflow_operations")
@with_doc(UPDATE_WORKFLOW)
async def update_workflow_tool(
    config: RunnableConfig,
    workflow_id: Annotated[str, "The unique identifier of the workflow to update"],
    repeat: Annotated[
        Optional[str], "Cron expression for recurring workflows (optional)"
    ] = None,
    max_occurrences: Annotated[
        Optional[int], "Maximum number of times to run the workflow (optional)"
    ] = None,
    stop_after: Annotated[
        Optional[str],
        "ISO 8601 formatted date/time after which no more runs (optional)",
    ] = None,
    payload: Annotated[
        Optional[WorkflowPayload], "Additional data for the workflow task (optional)"
    ] = None,
) -> Any:
    """Update attributes of an existing workflow"""
    try:
        user_id = config.get("configurable", {}).get("user_id")
        if not user_id:
            return {"error": "User ID is required to update workflow"}

        update_data: dict[str, Any] = {}
        if repeat is not None:
            update_data["repeat"] = repeat
        if max_occurrences is not None:
            update_data["max_occurrences"] = max_occurrences
        if stop_after:
            update_data["stop_after"] = datetime.fromisoformat(stop_after)
        if payload is not None:
            update_data["payload"] = payload

        success = await svc_update_workflow(
            workflow_id, update_data, user_id, reschedule=True
        )
        if success:
            return {"status": "updated"}
        else:
            logger.error("Failed to update workflow")
            return {"error": "Failed to update workflow"}
    except Exception as e:
        logger.exception("Exception occurred while updating workflow")
        return {"error": str(e)}


@tool(parse_docstring=True)
@with_rate_limiting("workflow_operations")
@with_doc(SEARCH_WORKFLOWS)
async def search_workflows_tool(
    config: RunnableConfig,
    query: Annotated[str, "Search keyword(s) to match against workflows"],
) -> Any:
    """Search workflows by keyword or content"""
    try:
        user_id = config.get("configurable", {}).get("user_id")
        if not user_id:
            logger.error("Missing user_id in config")
            return {"error": "User ID is required to search workflows"}

        workflows = await svc_list_user_workflows(user_id=user_id, limit=100, skip=0)

        results = []
        for w in workflows:
            wd = w.model_dump()
            if query.lower() in json.dumps(wd).lower():
                results.append(wd)

        return results
    except Exception as e:
        logger.exception("Exception occurred while searching workflows")
        return {"error": str(e)}


tools = [
    create_workflow_tool,
    list_user_workflows_tool,
    get_workflow_tool,
    delete_workflow_tool,
    update_workflow_tool,
    search_workflows_tool,
]
