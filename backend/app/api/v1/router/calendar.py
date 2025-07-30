from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.decorators import tiered_rate_limit
from app.models.calendar_models import (
    EventCreateRequest,
    EventDeleteRequest,
    EventUpdateRequest,
    CalendarPreferencesUpdateRequest,
)
from app.services.calendar_service import (
    delete_calendar_event,
    update_calendar_event,
)
from app.api.v1.dependencies.google_scope_dependencies import require_google_integration
from app.services import calendar_service

router = APIRouter()


@router.get("/calendar/list", summary="Get Calendar List")
async def get_calendar_list(
    current_user: dict = Depends(require_google_integration("calendar")),
):
    """
    Retrieve the list of calendars for the authenticated user.

    Returns:
        A list of calendars for the user.

    Raises:
        HTTPException: If an error occurs during calendar retrieval.
    """
    try:
        # Using the valid access token from the dependency. The refresh token is handled in the dependency.
        return await calendar_service.list_calendars(current_user["access_token"], None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calendar/events", summary="Get Events from Selected Calendars")
async def get_events(
    page_token: Optional[str] = None,
    selected_calendars: Optional[List[str]] = Query(None),
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
    current_user: dict = Depends(require_google_integration("calendar")),
):
    """
    Retrieve events from the user's selected calendars. If no calendars are provided,
    the primary calendar or stored user preferences are used. Supports pagination via
    the page_token parameter.

    Returns:
        A list of events from the selected calendars.

    Raises:
        HTTPException: If event retrieval fails.
    """
    try:
        return await calendar_service.get_calendar_events(
            user_id=current_user["user_id"],
            access_token=current_user["access_token"],
            refresh_token=None,  # Already handled by the dependency
            page_token=page_token,
            selected_calendars=selected_calendars,
            time_min=time_min,
            time_max=time_max,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calendar/{calendar_id}/events", summary="Get Events by Calendar ID")
async def get_events_by_calendar(
    calendar_id: str,
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
    page_token: Optional[str] = None,
    current_user: dict = Depends(require_google_integration("calendar")),
):
    """
    Fetch events for a specific calendar identified by its ID.

    Args:
        calendar_id (str): The unique calendar identifier.
        time_min (Optional[str]): Lower bound of event start time.
        time_max (Optional[str]): Upper bound of event end time.
        page_token (Optional[str]): Pagination token for fetching further events.

    Returns:
        A list of events for the specified calendar.

    Raises:
        HTTPException: If the event retrieval process encounters an error.
    """
    try:
        return await calendar_service.get_calendar_events_by_id(
            calendar_id=calendar_id,
            access_token=current_user["access_token"],
            refresh_token=None,  # Already handled
            page_token=page_token,
            time_min=time_min,
            time_max=time_max,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calendar/event", summary="Create a Calendar Event")
@tiered_rate_limit("calendar_management")
async def create_event(
    event: EventCreateRequest,
    current_user: dict = Depends(require_google_integration("calendar")),
):
    """
    Create a new calendar event. This endpoint accepts non-canonical timezone names
    which are normalized in the service.

    Args:
        event (EventCreateRequest): The event creation request details.

    Returns:
        The details of the created event.

    Raises:
        HTTPException: If event creation fails.
    """
    try:
        return await calendar_service.create_calendar_event(
            event, current_user["access_token"], None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calendar/all/events", summary="Get Events from All Calendars")
async def get_all_events(
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
    current_user: dict = Depends(require_google_integration("calendar")),
):
    """
    Retrieve events from every calendar associated with the user concurrently.

    Returns:
        A comprehensive list of events from all calendars.

    Raises:
        HTTPException: If event retrieval fails.
    """
    try:
        return await calendar_service.get_all_calendar_events(
            current_user["access_token"], None, time_min, time_max
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calendar/preferences", summary="Get User Calendar Preferences")
async def get_calendar_preferences(
    current_user: dict = Depends(require_google_integration("calendar")),
):
    """
    Retrieve the user's selected calendar preferences from the database.

    Returns:
        A dictionary with the user's selected calendar IDs.

    Raises:
        HTTPException: If the user is not authenticated or preferences are not found.
    """
    try:
        return await calendar_service.get_user_calendar_preferences(
            current_user["user_id"]
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/calendar/preferences", summary="Update User Calendar Preferences")
@tiered_rate_limit("calendar_management")
async def update_calendar_preferences(
    preferences: CalendarPreferencesUpdateRequest,
    current_user: dict = Depends(require_google_integration("calendar")),
):
    """
    Update the user's selected calendar preferences in the database.

    Args:
        preferences (CalendarPreferencesUpdateRequest): The selected calendar IDs to update.

    Returns:
        A message indicating the result of the update operation.

    Raises:
        HTTPException: If the user is not authenticated.
    """
    try:
        return await calendar_service.update_user_calendar_preferences(
            current_user["user_id"], preferences.selected_calendars
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/calendar/event", summary="Delete a Calendar Event")
@tiered_rate_limit("calendar_management")
async def delete_event(
    event: EventDeleteRequest,
    current_user: dict = Depends(require_google_integration("calendar")),
):
    """
    Delete a calendar event. This endpoint requires the event ID and optionally the calendar ID.

    Args:
        event (EventDeleteRequest): The event deletion request details.

    Returns:
        A confirmation message indicating successful deletion.

    Raises:
        HTTPException: If event deletion fails.
    """
    try:
        return await delete_calendar_event(event, current_user["access_token"], None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/calendar/event", summary="Update a Calendar Event")
@tiered_rate_limit("calendar_management")
async def update_event(
    event: EventUpdateRequest,
    current_user: dict = Depends(require_google_integration("calendar")),
):
    """
    Update a calendar event. This endpoint allows partial updates of event fields.
    Only provided fields will be updated, preserving existing values for omitted fields.

    Args:
        event (EventUpdateRequest): The event update request details.

    Returns:
        The details of the updated event.

    Raises:
        HTTPException: If event update fails.
    """
    try:
        return await update_calendar_event(event, current_user["access_token"], None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
