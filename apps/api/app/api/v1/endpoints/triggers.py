"""
Triggers API endpoints for workflow automation.

Provides endpoints for fetching available trigger schemas
that can be used in workflow configuration.
"""

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.v1.dependencies.oauth_dependencies import get_current_user
from app.constants.general import MAX_PAGE_NUMBER
from app.models.trigger_config import TriggerOptionsResponse, WorkflowTriggerResponse
from app.models.user_models import AuthenticatedUser
from app.services.triggers import get_handler_by_name
from app.services.workflow.trigger_service import TriggerService
from shared.py.wide_events import log

router = APIRouter(prefix="/triggers")


@router.get("/schema")
async def get_trigger_schemas(
    _: AuthenticatedUser = Depends(get_current_user),
) -> list[WorkflowTriggerResponse]:
    """
    Get all available workflow trigger schemas.

    Returns a list of trigger configurations that can be used when creating
    or editing workflows, including their config schemas for dynamic UI generation.
    """
    log.set(operation="list_trigger_schemas")
    triggers = await TriggerService.get_all_workflow_triggers()
    log.set(result_count=len(triggers))
    log.set(outcome="success")
    return triggers


@router.get("/options")
async def get_trigger_options(
    integration_id: str,
    trigger_slug: str,
    field_name: str = "",
    parent_values: str = "",
    page: int = Query(
        1, ge=1, le=MAX_PAGE_NUMBER, description="Page number (starting from 1), for paged handlers"
    ),
    search: str = Query("", description="Filter options by label substring"),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> TriggerOptionsResponse:
    """
    Get dynamic options for a trigger configuration field.

    Args:
        integration_id: The integration ID (e.g., 'slack', 'trello')
        trigger_slug: The trigger slug (e.g., 'slack_new_message')
        field_name: The config field name (e.g., 'channel_id'), optional
        parent_values: Comma-separated parent IDs for cascading options (e.g., 'workspace1,workspace2')
        page: Page of options to return; handlers that do not page ignore it
        search: Substring to filter options by; handlers that do not search ignore it
    """
    log.set(
        operation="get_trigger_options",
        trigger_type=trigger_slug,
        integration_name=integration_id,
    )
    handler = get_handler_by_name(trigger_slug)
    if not handler:
        raise HTTPException(status_code=404, detail="Handler not found for trigger")

    # Parse parent values
    parent_ids = (
        [v.strip() for v in parent_values.split(",") if v.strip()] if parent_values else None
    )

    options = await handler.get_config_options(
        trigger_slug,
        field_name,
        current_user["user_id"],
        integration_id,
        parent_ids,
        page=page,
        search=search,
    )

    log.set(result_count=len(options))
    log.set(outcome="success")
    return TriggerOptionsResponse(options=list(options))
