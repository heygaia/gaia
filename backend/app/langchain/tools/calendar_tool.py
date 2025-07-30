import json
import pprint
from typing import Any, Dict, List, Optional, Union

import httpx
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools import tool
from langgraph.config import get_stream_writer

from app.config.loggers import chat_logger as logger
from app.docstrings.langchain.tools.calendar_tool_docs import (
    CALENDAR_EVENT,
    # DELETE_CALENDAR_EVENT,
    EDIT_CALENDAR_EVENT,
    FETCH_CALENDAR_EVENTS,
    FETCH_CALENDAR_LIST,
    SEARCH_CALENDAR_EVENTS,
    VIEW_CALENDAR_EVENT,
)
from app.decorators import with_doc, with_rate_limiting, require_integration
from app.langchain.templates.calendar_template import (
    CALENDAR_LIST_TEMPLATE,
    CALENDAR_PROMPT_TEMPLATE,
)
from app.models.calendar_models import EventCreateRequest
from app.services.calendar_service import (
    get_calendar_events,
    list_calendars,
    search_calendar_events_native,
)


@tool(parse_docstring=True)
@with_rate_limiting("calendar_management")
@with_doc(CALENDAR_EVENT)
@require_integration("calendar")
async def create_calendar_event(
    event_data: Union[
        List[Union[EventCreateRequest, Dict[str, Any]]],
        EventCreateRequest,
        Dict[str, Any],
    ],
    config: RunnableConfig,
) -> str:
    try:
        logger.info("===== CALENDAR EVENT TOOL CALLED =====")
        logger.info("Processing calendar event with data:")
        logger.info(pprint.pformat(event_data, indent=2, width=100))

        # Normalize input to always work with a list of EventCreateRequest objects
        event_list: List[EventCreateRequest] = []

        if isinstance(event_data, EventCreateRequest):
            # Single event object - convert to list
            event_list = [event_data]
            logger.info("Received single event object, converting to list")
        elif isinstance(event_data, list):
            # Process list - ensure all items are EventCreateRequest objects
            for item in event_data:
                if isinstance(item, EventCreateRequest):
                    event_list.append(item)
                elif isinstance(item, dict):
                    # Convert dict to EventCreateRequest
                    try:
                        event_obj = EventCreateRequest(**item)
                        event_list.append(event_obj)
                    except Exception as e:
                        logger.error(
                            f"Failed to convert dict to EventCreateRequest: {e}"
                        )
                        continue
                else:
                    logger.error(f"Invalid item type in list: {type(item)}")
                    continue
            logger.info(f"Processed list with {len(event_list)} valid events")
        elif isinstance(event_data, dict):
            # Single dict - convert to EventCreateRequest
            try:
                event_obj = EventCreateRequest(**event_data)
                event_list = [event_obj]
                logger.info("Converted single dict to EventCreateRequest")
            except Exception as e:
                logger.error(f"Failed to convert dict to EventCreateRequest: {e}")
                return json.dumps(
                    {
                        "error": f"Invalid event data format: {e}",
                        "calendar_options": [],
                        "prompt": str(CALENDAR_PROMPT_TEMPLATE.invoke({})),
                    }
                )
        else:
            # Invalid type
            logger.error(f"Invalid event data type: {type(event_data)}")
            return json.dumps(
                {
                    "error": "Calendar event data must be an EventCreateRequest object, dict, or list of such objects",
                    "calendar_options": [],
                    "prompt": str(CALENDAR_PROMPT_TEMPLATE.invoke({})),
                }
            )

        # Validate non-empty
        if not event_list:
            logger.error("Empty event list provided")
            return json.dumps(
                {
                    "error": "At least one calendar event must be provided",
                    "calendar_options": [],
                    "prompt": str(CALENDAR_PROMPT_TEMPLATE.invoke({})),
                }
            )

        calendar_options = []
        validation_errors = []

        logger.info(f"Processing {len(event_list)} calendar events")

        # Process each event with validation
        for event in event_list:
            try:
                # Validate event fields based on whether it's an all-day event
                if event.is_all_day:
                    # For all-day events, start and end are optional
                    # They'll be handled in the service with defaults if missing
                    pass
                else:
                    # For time-specific events, both start and end are required
                    if not event.start or not event.end:
                        raise ValueError(
                            "Start and end times are required for time-specific events"
                        )

                # Add the validated event as a proper dict with all required fields
                event_dict = {
                    "summary": event.summary,
                    "description": event.description or "",
                    "is_all_day": event.is_all_day,
                    "timezone": event.timezone or "UTC",
                }

                # Add optional fields only if they exist
                if event.start:
                    event_dict["start"] = event.start
                if event.end:
                    event_dict["end"] = event.end
                if event.calendar_id:
                    event_dict["calendar_id"] = event.calendar_id
                if event.calendar_name:
                    event_dict["calendar_name"] = event.calendar_name
                if event.calendar_color:
                    event_dict["calendar_color"] = event.calendar_color

                calendar_options.append(event_dict)
                logger.info(f"Added calendar event: {event.summary}")

            except Exception as e:
                error_msg = f"Error processing calendar event: {e}"
                logger.error(error_msg)
                validation_errors.append(error_msg)

        # Return validation errors if any
        if validation_errors and not calendar_options:
            logger.error(f"Calendar event validation failed: {validation_errors}")
            return json.dumps(
                {
                    "error": "Calendar event validation failed",
                    "details": validation_errors,
                    "calendar_options": [],
                    "prompt": str(CALENDAR_PROMPT_TEMPLATE.invoke({})),
                }
            )

        configurable = config.get("configurable", {})
        if not configurable:
            logger.error("Missing 'configurable' section in config")
            return json.dumps(
                {
                    "error": "Configuration data is missing",
                    "calendar_options": [],
                    "prompt": str(CALENDAR_PROMPT_TEMPLATE.invoke({})),
                }
            )

        # # If initiated by backend then create notification
        # if configurable.get("initiator") == "backend":
        #     user_id = configurable.get("user_id")
        #     if not user_id:
        #         logger.error("Missing user_id in configuration")
        #         return json.dumps(
        #             {
        #                 "error": "User ID is required to create calendar notification",
        #                 "calendar_options": [],
        #                 "prompt": str(CALENDAR_PROMPT_TEMPLATE.invoke({})),
        #             }
        #         )

        #     # Create a notification for the user
        #     notifications = (
        #         AIProactiveNotificationSource.create_calendar_event_notification(
        #             user_id=user_id,
        #             notification_data=event_list,
        #         )
        #     )
        #     await asyncio.gather(
        #         *[
        #             notification_service.create_notification(notification)
        #             for notification in notifications
        #         ]
        #     )

        #     return "Calendar notification created successfully."

        # Return the successfully processed events
        writer = get_stream_writer()

        # Send calendar options to frontend via writer
        writer({"calendar_options": calendar_options, "intent": "calendar"})

        logger.info("Calendar event processing successful")
        logger.info(f"Sent {len(calendar_options)} calendar options to frontend")
        return "Calendar options sent to frontend"

    except Exception as e:
        error_msg = f"Error processing calendar event: {e}"
        logger.error(error_msg)
        return json.dumps(
            {
                "error": "Unable to process calendar event",
                "details": str(e),
                "calendar_options": [],
                "prompt": str(CALENDAR_PROMPT_TEMPLATE.invoke({})),
            }
        )


@tool
@with_rate_limiting("calendar_management")
@with_doc(FETCH_CALENDAR_LIST)
@require_integration("calendar")
async def fetch_calendar_list(
    config: RunnableConfig,
) -> str | dict:
    try:
        if not config:
            logger.error("Missing configuration data")
            return "Unable to access calendar configuration. Please try again."

        access_token = config.get("configurable", {}).get("access_token")

        if not access_token:
            logger.error("Missing access token in config")
            return "Unable to access your calendar. Please ensure you're logged in with calendar permissions."

        calendars = await list_calendars(access_token=access_token, short=True)
        if calendars is None:
            logger.error("Unable to fetch calendars - no data returned")
            return "Unable to fetch your calendars. Please ensure your calendar is connected."

        logger.info(f"Fetched {len(calendars)} calendars")

        # Build array of {name, id, description} for all calendars
        calendar_list_fetch_data = []
        if calendars and isinstance(calendars, list):
            for calendar in calendars:
                if isinstance(calendar, dict):
                    calendar_list_fetch_data.append(
                        {
                            "name": calendar.get("summary", "Unknown Calendar"),
                            "id": calendar.get("id", ""),
                            "description": calendar.get("description", ""),
                            "backgroundColor": calendar.get("backgroundColor"),
                        }
                    )

        writer = get_stream_writer()
        writer({"calendar_list_fetch_data": calendar_list_fetch_data})

        formatted_response = CALENDAR_LIST_TEMPLATE.format(
            calendars=json.dumps(calendars)
        )

        return formatted_response
    except Exception as e:
        error_msg = f"Error fetching calendars: {str(e)}"
        logger.error(error_msg)
        return f"Error fetching calendars: {str(e)}"


@tool(parse_docstring=True)
@with_rate_limiting("calendar_management")
@with_doc(FETCH_CALENDAR_EVENTS)
@require_integration("calendar")
async def fetch_calendar_events(
    user_id: str,
    config: RunnableConfig,
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
    selected_calendars: Optional[List[str]] = None,
) -> str:
    try:
        if not config:
            logger.error("Missing configuration data")
            return "Unable to access calendar configuration. Please try again."

        access_token = config.get("configurable", {}).get("access_token")
        refresh_token = config.get("configurable", {}).get("refresh_token")

        if not access_token:
            logger.error("Missing access token in config")
            return "Unable to access your calendar. Please ensure you're logged in with calendar permissions."

        logger.info(f"Fetching calendar events for user {user_id}")

        events_data = await get_calendar_events(
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            selected_calendars=selected_calendars,
            time_min=time_min,
            time_max=time_max,
        )

        events = events_data.get("events", [])
        logger.info(f"Fetched {len(events)} events")

        # Build array of {summary, start_time, calendar_name} for all events
        calendar_fetch_data = []
        for event in events:
            start_time = ""
            if event.get("start"):
                start_obj = event["start"]
                if start_obj.get("dateTime"):
                    start_time = start_obj["dateTime"]
                elif start_obj.get("date"):
                    start_time = start_obj["date"]

            calendar_fetch_data.append(
                {
                    "summary": event.get("summary", "No Title"),
                    "start_time": start_time,
                    "calendar_name": event.get("calendarTitle", ""),
                }
            )

        writer = get_stream_writer()
        writer({"calendar_fetch_data": calendar_fetch_data})

        return json.dumps(
            {
                "events": events,
                "total_events": len(events),
                "selected_calendars": events_data.get("selectedCalendars", []),
                "next_page_token": events_data.get("nextPageToken"),
            }
        )

    except Exception as e:
        error_msg = f"Error fetching calendar events: {str(e)}"
        logger.error(error_msg)
        return error_msg


@tool(parse_docstring=True)
@with_doc(SEARCH_CALENDAR_EVENTS)
@with_rate_limiting("calendar_management")
@require_integration("calendar")
async def search_calendar_events(
    query: str,
    user_id: str,
    config: RunnableConfig,
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
) -> str:
    try:
        if not config:
            logger.error("Missing configuration data")
            return "Unable to access calendar configuration. Please try again."

        access_token = config.get("configurable", {}).get("access_token")
        refresh_token = config.get("configurable", {}).get("refresh_token")

        if not access_token:
            logger.error("Missing access token in config")
            return "Unable to access your calendar. Please ensure you're logged in with calendar permissions."

        logger.info(f"Searching calendar events for query: {query}")

        # Send progress update
        writer = get_stream_writer()
        writer({"progress": f"Searching calendar events for '{query}'..."})

        # Use the new search function with Google Calendar API's native search
        search_results = await search_calendar_events_native(
            query=query,
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            time_min=time_min,
            time_max=time_max,
        )

        logger.info(
            f"Found {len(search_results.get('matching_events', []))} matching events for query: {query}"
        )

        # Build array of {summary, start_time, calendar_name} for search results
        calendar_search_data = []
        for event in search_results.get("matching_events", []):
            start_time = ""
            if event.get("start"):
                start_obj = event["start"]
                if start_obj.get("dateTime"):
                    start_time = start_obj["dateTime"]
                elif start_obj.get("date"):
                    start_time = start_obj["date"]

            calendar_search_data.append(
                {
                    "summary": event.get("summary", "No Title"),
                    "start_time": start_time,
                    "calendar_name": event.get("calendarTitle", ""),
                }
            )

        # Send search results to frontend via writer using grouped structure
        writer(
            {
                "calendar_data": {"calendar_search_results": search_results},
                "calendar_fetch_data": calendar_search_data,
            }
        )

        return "Calendar search results sent to frontend"

    except Exception as e:
        error_msg = f"Error searching calendar events: {str(e)}"
        logger.error(error_msg)
        return error_msg


@tool(parse_docstring=True)
@with_doc(VIEW_CALENDAR_EVENT)
@with_rate_limiting("calendar_management")
@require_integration("calendar")
async def view_calendar_event(
    event_id: str,
    config: RunnableConfig,
    calendar_id: str = "primary",
) -> str:
    try:
        if not config:
            logger.error("Missing configuration data")
            return "Unable to access calendar configuration. Please try again."

        access_token = config.get("configurable", {}).get("access_token")

        if not access_token:
            logger.error("Missing access token in config")
            return "Unable to access your calendar. Please ensure you're logged in with calendar permissions."

        # Fetch specific event using Google Calendar API
        url = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events/{event_id}"
        headers = {"Authorization": f"Bearer {access_token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)

        if response.status_code == 200:
            event = response.json()
            logger.info(f"Retrieved event: {event.get('summary', 'Unknown')}")

            return json.dumps(
                {
                    "event": event,
                    "event_id": event_id,
                    "calendar_id": calendar_id,
                }
            )
        else:
            error_msg = (
                f"Event not found or access denied (Status: {response.status_code})"
            )
            logger.error(error_msg)
            return error_msg

    except Exception as e:
        error_msg = f"Error viewing calendar event: {str(e)}"
        logger.error(error_msg)
        return error_msg


# @tool(parse_docstring=True)
# @with_rate_limiting("calendar_management")
# @with_doc(DELETE_CALENDAR_EVENT)
# async def delete_calendar_event(
#     query: str,
#     user_id: str,
#     config: RunnableConfig,
# ) -> str:
#     try:
#         logger.info("===== DELETE CALENDAR EVENT TOOL CALLED =====")
#         logger.info(f"Searching for event to delete with query: {query}")

#         if not config:
#             logger.error("Missing configuration data")
#             return "Unable to access calendar configuration. Please try again."

#         access_token = config.get("configurable", {}).get("access_token")
#         refresh_token = config.get("configurable", {}).get("refresh_token")

#         if not access_token:
#             logger.error("Missing access token in config")
#             return "Unable to access your calendar. Please ensure you're logged in with calendar permissions."

#         # Send progress update
#         writer = get_stream_writer()
#         writer({"progress": f"Searching for event '{query}' to delete..."})

#         # Search for events matching the query
#         search_results = await search_calendar_events_native(
#             query=query,
#             user_id=user_id,
#             access_token=access_token,
#             refresh_token=refresh_token,
#         )

#         matching_events = search_results.get("matching_events", [])

#         if not matching_events:
#             logger.info(f"No events found matching query: {query}")
#             return f"No calendar events found matching '{query}'. Please try a different search term or check your calendar."

#         # For simplicity, take the first (most relevant) match
#         # In production, you might want to implement more sophisticated matching
#         target_event = matching_events[0]

#         logger.info(f"Found event to delete: {target_event.get('summary', 'Unknown')}")

#         # Prepare deletion confirmation data
#         delete_option = {
#             "action": "delete",
#             "event_id": target_event.get("id"),
#             "calendar_id": target_event.get("calendarId", "primary"),
#             "summary": target_event.get("summary", ""),
#             "description": target_event.get("description", ""),
#             "start": target_event.get("start", {}),
#             "end": target_event.get("end", {}),
#             "original_query": query,
#         }

#         # Send deletion options to frontend via writer
#         writer({
#             "calendar_delete_options": [delete_option],
#         })

#         logger.info("Calendar event deletion options sent to frontend")
#         return f"Found event '{target_event.get('summary', 'Unknown')}' matching your search. Please confirm the deletion."

#     except Exception as e:
#         error_msg = f"Error searching for calendar event to delete: {str(e)}"
#         logger.error(error_msg)
#         return error_msg


@tool(parse_docstring=True)
@with_rate_limiting("calendar_management")
@with_doc(EDIT_CALENDAR_EVENT)
async def edit_calendar_event(
    query: str,
    user_id: str,
    config: RunnableConfig,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    is_all_day: Optional[bool] = None,
    timezone: Optional[str] = None,
) -> str:
    try:
        logger.info("===== EDIT CALENDAR EVENT TOOL CALLED =====")
        logger.info(f"Searching for event to edit with query: {query}")

        if not config:
            logger.error("Missing configuration data")
            return "Unable to access calendar configuration. Please try again."

        access_token = config.get("configurable", {}).get("access_token")
        refresh_token = config.get("configurable", {}).get("refresh_token")

        if not access_token:
            logger.error("Missing access token in config")
            return "Unable to access your calendar. Please ensure you're logged in with calendar permissions."

        # Send progress update
        writer = get_stream_writer()
        writer({"progress": f"Searching for event '{query}' to edit..."})

        # Search for events matching the query
        search_results = await search_calendar_events_native(
            query=query,
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
        )

        matching_events = search_results.get("matching_events", [])

        if not matching_events:
            logger.info(f"No events found matching query: {query}")
            return f"No calendar events found matching '{query}'. Please try a different search term or check your calendar."

        # For simplicity, take the first (most relevant) match
        target_event = matching_events[0]

        logger.info(f"Found event to edit: {target_event.get('summary', 'Unknown')}")

        # Prepare the updated event data
        edit_option = {
            "action": "edit",
            "event_id": target_event.get("id"),
            "calendar_id": target_event.get("calendarId", "primary"),
            "original_summary": target_event.get("summary", ""),
            "original_description": target_event.get("description", ""),
            "original_start": target_event.get("start", {}),
            "original_end": target_event.get("end", {}),
            "original_query": query,
        }

        # Add updated fields only if they are provided
        if summary is not None:
            edit_option["summary"] = summary
        if description is not None:
            edit_option["description"] = description
        if start is not None:
            edit_option["start"] = start
        if end is not None:
            edit_option["end"] = end
        if is_all_day is not None:
            edit_option["is_all_day"] = is_all_day
        if timezone is not None:
            edit_option["timezone"] = timezone

        # Send edit options to frontend via writer
        writer(
            {
                "calendar_edit_options": [edit_option],
            }
        )

        logger.info("Calendar event edit options sent to frontend")
        changes_summary = []
        if summary is not None:
            changes_summary.append(f"title to '{summary}'")
        if description is not None:
            changes_summary.append(f"description to '{description}'")
        if start is not None or end is not None:
            changes_summary.append("time/date")
        if is_all_day is not None:
            changes_summary.append(f"all-day status to {is_all_day}")

        changes_text = (
            ", ".join(changes_summary) if changes_summary else "the specified fields"
        )
        return f"Found event '{target_event.get('summary', 'Unknown')}' matching your search. Ready to update {changes_text}. Please confirm the changes."

    except Exception as e:
        error_msg = f"Error searching for calendar event to edit: {str(e)}"
        logger.error(error_msg)
        return error_msg


tools = [
    fetch_calendar_list,
    create_calendar_event,
    # delete_calendar_event,
    edit_calendar_event,
    fetch_calendar_events,
    search_calendar_events,
    view_calendar_event,
]
