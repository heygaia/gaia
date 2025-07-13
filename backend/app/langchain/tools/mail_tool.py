from typing import Annotated, Any, Dict, List, Optional

from app.config.loggers import chat_logger as logger
from app.docstrings.langchain.tools.mail_tool_docs import (
    APPLY_LABELS_TO_EMAILS,
    ARCHIVE_EMAILS,
    COMPOSE_EMAIL,
    CREATE_GMAIL_LABEL,
    DELETE_GMAIL_LABEL,
    GET_EMAIL_THREAD,
    GET_GMAIL_CONTACTS,
    LIST_GMAIL_LABELS,
    LIST_GMAIL_MESSAGES,
    REMOVE_LABELS_FROM_EMAILS,
    SEARCH_GMAIL_MESSAGES,
    STAR_EMAILS,
    UNSTAR_EMAILS,
    UPDATE_GMAIL_LABEL,
)
from app.docstrings.utils import with_doc
from app.langchain.templates.mail_templates import (
    COMPOSE_EMAIL_TEMPLATE,
    process_get_thread_response,
    process_list_labels_response,
    process_list_messages_response,
    process_search_messages_response,
)
from app.middleware.langchain_rate_limiter import with_rate_limiting
from app.services.contact_service import get_gmail_contacts
from app.services.mail_service import (
    apply_labels,
    archive_messages,
    create_label,
    delete_label,
    fetch_detailed_messages,
    fetch_thread,
    get_gmail_service,
    remove_labels,
    search_messages,
    star_messages,
    unstar_messages,
    update_label,
)
from app.utils.general_utils import transform_gmail_message
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.config import get_stream_writer


def get_auth_from_config(config: RunnableConfig) -> Dict[str, str]:
    """Extract access and refresh tokens from the config."""
    if not config:
        logger.error("Gmail tool called without config")
        return {"access_token": "", "refresh_token": ""}

    configurable = config.get("configurable", {})
    return {
        "access_token": configurable.get("access_token", ""),
        "refresh_token": configurable.get("refresh_token", ""),
    }


@tool
@with_doc(LIST_GMAIL_LABELS)
async def list_gmail_labels(config: RunnableConfig) -> Dict[str, Any]:
    try:
        logger.info("Gmail Tool: Listing Gmail labels")
        auth = get_auth_from_config(config)

        if not auth["access_token"] or not auth["refresh_token"]:
            return {"error": "Authentication credentials not provided", "labels": []}

        service = get_gmail_service(
            access_token=auth["access_token"], refresh_token=auth["refresh_token"]
        )

        results = service.users().labels().list(userId="me").execute()

        # Process results to minimize data
        return process_list_labels_response({"labels": results.get("labels", [])})
    except Exception as e:
        error_msg = f"Error listing Gmail labels: {str(e)}"
        logger.error(error_msg)
        # Return minimal error response
        return {"error": error_msg, "labels": []}


@tool
@with_doc(LIST_GMAIL_MESSAGES)
async def fetch_gmail_messages(
    config: RunnableConfig,
    max_results: Annotated[
        int, "Maximum number of messages to fetch (default: 20)"
    ] = 20,
    page_token: Annotated[
        Optional[str], "Token for pagination, if fetching subsequent pages"
    ] = None,
) -> Dict[str, Any]:
    try:
        logger.info(
            f"Gmail Tool: Listing inbox messages (max: {max_results}, token: {page_token})"
        )
        auth = get_auth_from_config(config)

        if not auth["access_token"] or not auth["refresh_token"]:
            return {
                "error": "Authentication credentials not provided",
                "messages": [],
                "nextPageToken": None,
            }

        service = get_gmail_service(
            access_token=auth["access_token"], refresh_token=auth["refresh_token"]
        )

        # Prepare params for message list
        params = {"userId": "me", "labelIds": ["INBOX"], "maxResults": max_results}
        if page_token:
            params["pageToken"] = page_token

        # Fetch message list
        results = service.users().messages().list(**params).execute()
        messages = results.get("messages", [])

        # Use batching to fetch full details for each message
        detailed_messages = fetch_detailed_messages(service, messages)

        # Transform messages to standard format first, then process to minimize
        transformed_messages = [
            transform_gmail_message(msg) for msg in detailed_messages
        ]

        # Process to minimize data for LLM
        return process_list_messages_response(
            {
                "messages": transformed_messages,
                "nextPageToken": results.get("nextPageToken"),
            }
        )
    except Exception as e:
        error_msg = f"Error listing Gmail messages: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg, "messages": [], "nextPageToken": None}


@tool
@with_doc(SEARCH_GMAIL_MESSAGES)
async def search_gmail_messages(
    config: RunnableConfig,
    query: Annotated[Optional[str], "Free text search query"] = None,
    sender: Annotated[Optional[str], "Filter by sender email"] = None,
    recipient: Annotated[Optional[str], "Filter by recipient email"] = None,
    subject: Annotated[Optional[str], "Filter by subject"] = None,
    has_attachment: Annotated[
        Optional[bool], "Filter for messages with attachments"
    ] = None,
    attachment_type: Annotated[
        Optional[str], "Filter by attachment type (e.g., pdf, doc)"
    ] = None,
    date_from: Annotated[
        Optional[str], "Filter messages after this date (YYYY/MM/DD)"
    ] = None,
    date_to: Annotated[
        Optional[str], "Filter messages before this date (YYYY/MM/DD)"
    ] = None,
    label: Annotated[Optional[str], "Filter by label"] = None,
    is_read: Annotated[Optional[bool], "Filter by read/unread status"] = None,
    max_results: Annotated[
        int, "Maximum number of results to return (default: 20)"
    ] = 20,
    page_token: Annotated[Optional[str], "Token for pagination"] = None,
) -> Dict[str, Any]:
    try:
        logger.info(
            f"Gmail Tool: Searching messages with criteria: query={query}, sender={sender}, etc."
        )
        auth = get_auth_from_config(config)

        if not auth["access_token"] or not auth["refresh_token"]:
            return {
                "error": "Authentication credentials not provided",
                "messages": [],
                "nextPageToken": None,
            }

        service = get_gmail_service(
            access_token=auth["access_token"], refresh_token=auth["refresh_token"]
        )

        # Build Gmail query string from parameters
        query_parts = []

        if query:
            query_parts.append(f"{query}")
        if sender:
            query_parts.append(f"from:{sender}")
        if recipient:
            query_parts.append(f"to:{recipient}")
        if subject:
            query_parts.append(f"subject:{subject}")
        if has_attachment is not None:
            query_parts.append(
                "has:attachment" if has_attachment else "-has:attachment"
            )
        if attachment_type:
            query_parts.append(f"filename:{attachment_type}")
        if date_from:
            query_parts.append(f"after:{date_from}")
        if date_to:
            query_parts.append(f"before:{date_to}")
        if label:
            query_parts.append(f"label:{label}")
        if is_read is not None:
            query_parts.append("is:read" if is_read else "is:unread")

        # Combine all query parts
        gmail_query = " ".join(query_parts)

        search_results = search_messages(
            service=service,
            query=gmail_query,
            max_results=max_results,
            page_token=page_token,
        )

        # Process to minimize the search results data
        return process_search_messages_response(search_results)
    except Exception as e:
        error_msg = f"Error searching Gmail messages: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg, "messages": [], "nextPageToken": None}


@tool
@with_rate_limiting("mail_actions")
@with_doc(COMPOSE_EMAIL)
async def compose_email(
    config: RunnableConfig,
    body: Annotated[str, "Body content of the email"],
    subject: Annotated[str, "Subject line for the email"],
    recipient_query: Annotated[
        Optional[str],
        "Name or partial information about the recipient to search for their email address. Leave empty if no recipient information is provided.",
    ] = None,
) -> Dict[str, Any] | str:
    try:
        writer = get_stream_writer()
        resolved_emails = []

        # If recipient_query is provided, try to resolve contact emails
        if recipient_query and recipient_query.strip():
            writer({"progress": f"Searching contacts for '{recipient_query}'..."})
            try:
                auth = get_auth_from_config(config)

                if not auth["access_token"] or not auth["refresh_token"]:
                    logger.warning(
                        "Missing authentication credentials for contact resolution"
                    )
                else:
                    service = get_gmail_service(
                        access_token=auth["access_token"],
                        refresh_token=auth["refresh_token"],
                    )

                    # Use the service function directly instead of calling the tool
                    contacts_result = get_gmail_contacts(
                        service=service,
                        query=recipient_query,
                    )

                    if contacts_result.get("success") and contacts_result.get(
                        "contacts"
                    ):
                        resolved_emails = [
                            contact["email"] for contact in contacts_result["contacts"]
                        ]
                        writer(
                            {
                                "progress": f"Found {len(resolved_emails)} contact(s) for '{recipient_query}'"
                            }
                        )
                    else:
                        writer(
                            {"progress": f"No contacts found for '{recipient_query}'"}
                        )
                    logger.info(f"Resolved emails: {resolved_emails}")
            except Exception as contact_error:
                logger.warning(
                    f"Failed to resolve contacts for '{recipient_query}': {contact_error}"
                )
                writer({"progress": f"Contact search failed for '{recipient_query}'"})
                # Continue with empty resolved_emails if contact resolution fails

        # Check if initiated by backend
        # configurable = config.get("configurable", {})
        # if configurable.get("initiator") == "backend":
        #     user_id = configurable.get("user_id")
        #     if not user_id:
        #         logger.error(
        #             "Missing user_id in configuration for backend-initiated email composition"
        #         )
        #         return {
        #             "error": "User ID is required to create email composition notification"
        #         }

        #     # Create a notification for the user
        #     notification = (
        #         AIProactiveNotificationSource.create_mail_composition_notification(
        #             user_id=user_id,
        #             email_data=email_data,
        #         )
        #     )
        #     await notification_service.create_notification(notification)

        #     return "Email composition notification created successfully. Please check your frontend for the draft."

        # Regular frontend flow
        # Progress update for drafting
        writer({"progress": "Drafting email..."})
        writer(
            {
                "email_compose_data": {
                    "to": resolved_emails if resolved_emails else [],
                    "subject": subject,
                    "body": body,
                }
            }
        )

        # Generate summary of the composed email
        return COMPOSE_EMAIL_TEMPLATE.format(subject=subject, body=body)

    except Exception as e:
        error_msg = f"Error composing email: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}


@tool
@with_doc(STAR_EMAILS)
async def star_emails(
    message_ids: Annotated[List[str], "List of Gmail message IDs to star"],
    config: RunnableConfig,
) -> Dict[str, Any]:
    try:
        auth = get_auth_from_config(config)

        if not auth["access_token"] or not auth["refresh_token"]:
            return {
                "success": False,
                "error": "Authentication credentials not provided",
            }

        service = get_gmail_service(
            access_token=auth["access_token"], refresh_token=auth["refresh_token"]
        )

        result = star_messages(service, message_ids)

        return {"success": True, "message_ids": message_ids, "result": result}
    except Exception as e:
        error_msg = f"Error starring emails: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}


@tool
@with_doc(UNSTAR_EMAILS)
async def unstar_emails(
    message_ids: Annotated[List[str], "List of Gmail message IDs to unstar"],
    config: RunnableConfig,
) -> Dict[str, Any]:
    try:
        auth = get_auth_from_config(config)

        if not auth["access_token"] or not auth["refresh_token"]:
            return {
                "success": False,
                "error": "Authentication credentials not provided",
            }

        service = get_gmail_service(
            access_token=auth["access_token"], refresh_token=auth["refresh_token"]
        )

        result = unstar_messages(service, message_ids)

        return {"success": True, "message_ids": message_ids, "result": result}
    except Exception as e:
        error_msg = f"Error unstarring emails: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}


@tool
@with_doc(ARCHIVE_EMAILS)
async def archive_emails(
    message_ids: Annotated[List[str], "List of Gmail message IDs to archive"],
    config: RunnableConfig,
) -> Dict[str, Any]:
    try:
        logger.info(f"Gmail Tool: Archiving {len(message_ids)} emails")
        auth = get_auth_from_config(config)

        if not auth["access_token"] or not auth["refresh_token"]:
            return {
                "success": False,
                "error": "Authentication credentials not provided",
            }

        service = get_gmail_service(
            access_token=auth["access_token"], refresh_token=auth["refresh_token"]
        )

        result = archive_messages(service, message_ids)

        return {"success": True, "message_ids": message_ids, "result": result}
    except Exception as e:
        error_msg = f"Error archiving emails: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}


@tool
@with_doc(GET_EMAIL_THREAD)
async def get_email_thread(
    thread_id: Annotated[str, "The Gmail thread ID to fetch"],
    config: RunnableConfig,
) -> Dict[str, Any]:
    try:
        logger.info(f"Gmail Tool: Getting email thread {thread_id}")
        auth = get_auth_from_config(config)

        if not auth["access_token"] or not auth["refresh_token"]:
            return {"error": "Authentication credentials not provided"}

        service = get_gmail_service(
            access_token=auth["access_token"], refresh_token=auth["refresh_token"]
        )

        thread = fetch_thread(service, thread_id)

        # Process to minimize data for LLM
        return process_get_thread_response(thread)
    except Exception as e:
        error_msg = f"Error fetching email thread: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}


@tool
@with_doc(CREATE_GMAIL_LABEL)
async def create_gmail_label(
    config: RunnableConfig,
    name: Annotated[str, "Name for the new label"],
    label_list_visibility: Annotated[
        Optional[str],
        "Whether the label appears in the label list (labelShow, labelHide, labelShowIfUnread)",
    ] = "labelShow",
    message_list_visibility: Annotated[
        Optional[str], "Whether the label appears in the message list (show, hide)"
    ] = "show",
    background_color: Annotated[
        Optional[str], "Background color hex code (e.g., #f5f5f5)"
    ] = None,
    text_color: Annotated[Optional[str], "Text color hex code (e.g., #000000)"] = None,
) -> Dict[str, Any]:
    try:
        auth = get_auth_from_config(config)

        if not auth["access_token"] or not auth["refresh_token"]:
            return {
                "success": False,
                "error": "Authentication credentials not provided",
            }

        service = get_gmail_service(
            access_token=auth["access_token"], refresh_token=auth["refresh_token"]
        )

        label = create_label(
            service,
            name=name,
            label_list_visibility=label_list_visibility or "labelShow",
            message_list_visibility=message_list_visibility or "show",
            background_color=background_color,
            text_color=text_color,
        )

        return {"success": True, "label": label}
    except Exception as e:
        error_msg = f"Error creating Gmail label: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}


@tool
@with_doc(UPDATE_GMAIL_LABEL)
async def update_gmail_label(
    config: RunnableConfig,
    label_id: Annotated[str, "ID of the label to update"],
    name: Annotated[Optional[str], "New name for the label"] = None,
    label_list_visibility: Annotated[
        Optional[str],
        "Whether the label appears in the label list (labelShow, labelHide, labelShowIfUnread)",
    ] = None,
    message_list_visibility: Annotated[
        Optional[str], "Whether the label appears in the message list (show, hide)"
    ] = None,
    background_color: Annotated[
        Optional[str], "Background color hex code (e.g., #f5f5f5)"
    ] = None,
    text_color: Annotated[Optional[str], "Text color hex code (e.g., #000000)"] = None,
) -> Dict[str, Any]:
    try:
        logger.info(f"Gmail Tool: Updating label '{label_id}'")
        auth = get_auth_from_config(config)

        if not auth["access_token"] or not auth["refresh_token"]:
            return {
                "success": False,
                "error": "Authentication credentials not provided",
            }

        service = get_gmail_service(
            access_token=auth["access_token"], refresh_token=auth["refresh_token"]
        )

        label = update_label(
            service,
            label_id=label_id,
            name=name,
            label_list_visibility=label_list_visibility,
            message_list_visibility=message_list_visibility,
            background_color=background_color,
            text_color=text_color,
        )

        return {"success": True, "label": label}
    except Exception as e:
        error_msg = f"Error updating Gmail label: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}


@tool
@with_doc(DELETE_GMAIL_LABEL)
async def delete_gmail_label(
    label_id: Annotated[str, "ID of the label to delete"],
    config: RunnableConfig,
) -> Dict[str, Any]:
    try:
        logger.info(f"Gmail Tool: Deleting label '{label_id}'")
        auth = get_auth_from_config(config)

        if not auth["access_token"] or not auth["refresh_token"]:
            return {
                "success": False,
                "error": "Authentication credentials not provided",
            }

        service = get_gmail_service(
            access_token=auth["access_token"], refresh_token=auth["refresh_token"]
        )

        result = delete_label(service, label_id)

        return {"success": result, "label_id": label_id}
    except Exception as e:
        error_msg = f"Error deleting Gmail label: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}


@tool
@with_doc(APPLY_LABELS_TO_EMAILS)
async def apply_labels_to_emails(
    message_ids: Annotated[List[str], "List of Gmail message IDs to label"],
    label_ids: Annotated[List[str], "List of label IDs to apply"],
    config: RunnableConfig,
) -> Dict[str, Any]:
    try:
        logger.info(f"Gmail Tool: Applying labels to {len(message_ids)} emails")
        auth = get_auth_from_config(config)

        if not auth["access_token"] or not auth["refresh_token"]:
            return {
                "success": False,
                "error": "Authentication credentials not provided",
            }

        service = get_gmail_service(
            access_token=auth["access_token"], refresh_token=auth["refresh_token"]
        )

        # Apply labels without storing the result
        apply_labels(service, message_ids, label_ids)

        # Return success status without the full result data
        return {
            "success": True,
            "message_ids": message_ids,
            "labels_applied": label_ids,
        }
    except Exception as e:
        error_msg = f"Error applying labels to emails: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}


@tool
@with_doc(REMOVE_LABELS_FROM_EMAILS)
async def remove_labels_from_emails(
    message_ids: Annotated[
        List[str], "List of Gmail message IDs to remove labels from"
    ],
    label_ids: Annotated[List[str], "List of label IDs to remove"],
    config: RunnableConfig,
) -> Dict[str, Any]:
    try:
        logger.info(f"Gmail Tool: Removing labels from {len(message_ids)} emails")
        auth = get_auth_from_config(config)

        if not auth["access_token"] or not auth["refresh_token"]:
            return {
                "success": False,
                "error": "Authentication credentials not provided",
            }

        service = get_gmail_service(
            access_token=auth["access_token"], refresh_token=auth["refresh_token"]
        )

        # Remove labels without storing the result
        remove_labels(service, message_ids, label_ids)

        # Return success status without the full result data
        return {
            "success": True,
            "message_ids": message_ids,
            "labels_removed": label_ids,
        }
    except Exception as e:
        error_msg = f"Error removing labels from emails: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}


@tool
@with_doc(GET_GMAIL_CONTACTS)
async def get_mail_contacts(
    config: RunnableConfig,
    query: Annotated[
        str,
        "Search query to filter contacts (e.g., email address, name, or any Gmail search query)",
    ],
    max_results: Annotated[
        int,
        "Maximum number of messages to analyze for contact extraction (default: 30)",
    ] = 30,
) -> Dict[str, Any]:
    try:
        auth = get_auth_from_config(config)

        if not auth["access_token"] or not auth["refresh_token"]:
            return {
                "success": False,
                "error": "Authentication credentials not provided",
                "contacts": [],
            }

        service = get_gmail_service(
            access_token=auth["access_token"], refresh_token=auth["refresh_token"]
        )

        # Use the service function to get contacts
        return get_gmail_contacts(service=service, query=query, max_results=max_results)

    except Exception as e:
        error_msg = f"Error getting Gmail contacts: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg, "contacts": []}


tools = [
    # list_gmail_labels,
    fetch_gmail_messages,
    search_gmail_messages,
    compose_email,
    # star_emails,
    # unstar_emails,
    # archive_emails,
    get_email_thread,
    # create_gmail_label,
    # update_gmail_label,
    # delete_gmail_label,
    # apply_labels_to_emails,
    # remove_labels_from_emails,
    get_mail_contacts,
]
