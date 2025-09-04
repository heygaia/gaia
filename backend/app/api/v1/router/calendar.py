from typing import List, Optional

from app.api.v1.dependencies.google_scope_dependencies import require_google_integration
from app.config.token_repository import token_repository
from app.decorators import tiered_rate_limit
from app.models.calendar_models import (
    CalendarPreferencesUpdateRequest,
    EventCreateRequest,
    EventDeleteRequest,
    EventUpdateRequest,
)
from app.services import calendar_service
from app.services.calendar_service import (
    delete_calendar_event,
    update_calendar_event,
)
from fastapi import APIRouter, Depends, HTTPException, Query

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
        # Get user_id from the authenticated user object
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found")

        # Get token from repository instead of using it directly from current_user
        token = await token_repository.get_token(
            str(user_id), "google", renew_if_expired=True
        )
        access_token = str(token.get("access_token", ""))

        return await calendar_service.list_calendars(access_token)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calendar/events", summary="Get Events from Selected Calendars")
async def get_events(
    page_token: Optional[str] = None,
    selected_calendars: Optional[List[str]] = Query(None),
    start_date: Optional[str] = None,  # YYYY-MM-DD format
    end_date: Optional[str] = None,  # YYYY-MM-DD format
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
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found")

        # Convert start_date and end_date to time_min and time_max for Google Calendar API
        time_min = None
        time_max = None

        if start_date:
            try:
                # Convert YYYY-MM-DD to start of day in UTC
                from datetime import datetime, timezone

                start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(
                    tzinfo=timezone.utc
                )
                time_min = start_dt.isoformat()
            except ValueError:
                raise HTTPException(
                    status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD"
                )

        if end_date:
            try:
                # Convert YYYY-MM-DD to end of day in UTC
                from datetime import datetime, timezone, timedelta

                end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(
                    tzinfo=timezone.utc
                )
                # Add 24 hours to include the entire end day
                end_dt = end_dt + timedelta(days=1)
                time_max = end_dt.isoformat()
            except ValueError:
                raise HTTPException(
                    status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD"
                )

        # Get token from repository
        token = await token_repository.get_token(
            str(user_id), "google", renew_if_expired=True
        )
        access_token = str(token.get("access_token", ""))

        return await calendar_service.get_calendar_events(
            user_id=user_id,
            access_token=access_token,
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
    start_date: Optional[str] = None,  # YYYY-MM-DD format
    end_date: Optional[str] = None,  # YYYY-MM-DD format
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
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found")

        # Convert start_date and end_date to time_min and time_max for Google Calendar API
        time_min = None
        time_max = None

        if start_date:
            try:
                # Convert YYYY-MM-DD to start of day in UTC
                from datetime import datetime, timezone

                start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(
                    tzinfo=timezone.utc
                )
                time_min = start_dt.isoformat()
            except ValueError:
                raise HTTPException(
                    status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD"
                )

        if end_date:
            try:
                # Convert YYYY-MM-DD to end of day in UTC
                from datetime import datetime, timezone, timedelta

                end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(
                    tzinfo=timezone.utc
                )
                # Add 24 hours to include the entire end day
                end_dt = end_dt + timedelta(days=1)
                time_max = end_dt.isoformat()
            except ValueError:
                raise HTTPException(
                    status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD"
                )

        # Get token from repository
        token = await token_repository.get_token(
            str(user_id), "google", renew_if_expired=True
        )
        access_token = str(token.get("access_token", ""))

        return await calendar_service.get_calendar_events_by_id(
            calendar_id=calendar_id,
            access_token=access_token,
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
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found")

        # Get token from repository
        token = await token_repository.get_token(
            str(user_id), "google", renew_if_expired=True
        )
        access_token = str(token.get("access_token", ""))

        return await calendar_service.create_calendar_event(
            event, access_token, user_id
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
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found")

        # Get token from repository
        token = await token_repository.get_token(
            str(user_id), "google", renew_if_expired=True
        )
        access_token = str(token.get("access_token", ""))

        return await calendar_service.get_all_calendar_events(
            access_token, user_id, time_min, time_max
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
            str(current_user.get("user_id", ""))
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
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found")

        # Get token from repository
        token = await token_repository.get_token(
            str(user_id), "google", renew_if_expired=True
        )
        access_token = str(token.get("access_token", ""))

        return await delete_calendar_event(event, access_token, user_id)
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
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found")

        # Get token from repository
        token = await token_repository.get_token(
            str(user_id), "google", renew_if_expired=True
        )
        access_token = str(token.get("access_token", ""))

        return await update_calendar_event(event, access_token, user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
