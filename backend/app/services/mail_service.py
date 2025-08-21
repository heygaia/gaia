import base64
import os
import time
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

from app.config.loggers import general_logger as logger
from app.config.oauth_config import get_integration_scopes
from app.config.settings import settings
from app.utils.general_utils import transform_gmail_message
from fastapi import UploadFile
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import BatchHttpRequest


def get_gmail_service(
    refresh_token: Optional[str] = None,
    access_token: Optional[str] = None,
    user_id: Optional[str] = None,
):
    """
    Create a Gmail API service using OAuth credentials.

    Can be created either with tokens directly or by retrieving them from the token repository
    using the user_id.

    Args:
        refresh_token: OAuth refresh token
        access_token: OAuth access token
        user_id: User ID to fetch tokens from repository

    Returns:
        Google API service object for Gmail
    """
    # If user_id is provided, get tokens from repository
    if user_id and not (access_token and refresh_token):
        import asyncio

        from app.config.token_repository import token_repository

        # Get token from repository
        token = asyncio.run(token_repository.get_token(user_id, "google"))
        if token:
            # OAuth2Token behaves like a dict
            access_token = str(token.get("access_token", ""))
            refresh_token = str(token.get("refresh_token", ""))

    if not access_token:
        logger.error("No access token available to create Gmail service")
        return None

    creds = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri=settings.GOOGLE_TOKEN_URL,
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=get_integration_scopes("gmail"),
    )
    return build("gmail", "v1", credentials=creds)


def create_message(
    sender: str,
    to: List[str],
    subject: str,
    body: str,
    is_html: bool = False,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
    attachments: Optional[List[UploadFile]] = None,
):
    """Create a message for an email with optional attachments.

    Args:
        sender: Email address of the sender.
        to: Email addresses of the recipients.
        subject: The subject of the email message.
        body: The body of the email message.
        is_html: Whether the body is HTML content.
        cc: Optional. Email addresses for cc recipients.
        bcc: Optional. Email addresses for bcc recipients.
        attachments: Optional. List of files to attach.

    Returns:
        An object containing a base64url encoded email message.
    """
    # Always create a MIME message regardless of attachments
    message = MIMEMultipart("alternative" if is_html else "mixed")
    message["from"] = sender
    message["to"] = ", ".join(to)
    message["subject"] = subject

    if cc:
        message["cc"] = ", ".join(cc)
    if bcc:
        message["bcc"] = ", ".join(bcc)

    # Add body with correct content type
    mime_type = "html" if is_html else "plain"
    message.attach(MIMEText(body, mime_type))

    # Add attachments if any
    if attachments and len(attachments) > 0:
        # If we have HTML content and attachments, convert to mixed if not already
        if is_html and message.get_content_subtype() != "mixed":
            mixed_message = MIMEMultipart("mixed")
            # Copy all headers
            for header, value in message.items():
                mixed_message[header] = value
            # Attach the original HTML part
            mixed_message.attach(message)
            message = mixed_message

        # Add each attachment
        for attachment in attachments:
            # content_type = (
            #     attachment.content_type
            #     or mimetypes.guess_type(attachment.filename)[0]
            #     or "application/octet-stream"
            # )

            file_name = attachment.filename
            if not file_name:
                file_name = "attachment"

            attachment_part = MIMEApplication(
                attachment.file.read(), Name=os.path.basename(file_name)
            )

            # Add header to attachment
            attachment_part["Content-Disposition"] = (
                f'attachment; filename="{os.path.basename(file_name)}"'
            )
            message.attach(attachment_part)

            # Reset file pointer
            attachment.file.seek(0)

    # Encode the message properly as base64url
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {"raw": encoded_message}


def send_email(
    service: Any,
    sender: str,
    to_list: List[str],
    subject: str,
    body: str,
    is_html: bool = False,
    cc_list: Optional[List[str]] = None,
    bcc_list: Optional[List[str]] = None,
    attachments: Optional[List[UploadFile]] = None,
) -> Dict[str, Any]:
    """
    Send an email using Gmail.

    Args:
        service: Authenticated Gmail API service instance
        sender: Email address of the sender
        to_list: Email addresses of recipients
        subject: Email subject
        body: Email body content
        is_html: Whether the body is HTML content
        cc_list: Optional list of CC recipients
        bcc_list: Optional list of BCC recipients
        attachments: Optional list of files to attach

    Returns:
        Sent message data from the Gmail API
    """
    message = create_message(
        sender=sender,
        to=to_list,
        subject=subject,
        body=body,
        is_html=is_html,
        cc=cc_list,
        bcc=bcc_list,
        attachments=attachments,
    )
    sent_message = service.users().messages().send(userId="me", body=message).execute()
    return sent_message


def fetch_detailed_messages(service, messages, batch_size=20, delay=2):
    """
    Fetch detailed Gmail messages using batch requests while handling rate limits.

    :param service: Authenticated Gmail API service instance
    :param messages: List of message metadata (each containing 'id')
    :param batch_size: Number of messages per batch (default: 20)
    :param delay: Time in seconds to wait between batch executions
    :return: List of detailed message objects
    """
    detailed_messages = []

    def callback(request_id, response, exception):
        if exception:
            print(f"Error in request {request_id}: {exception}")
        else:
            detailed_messages.append(response)

    total_messages = len(messages)
    for i in range(0, total_messages, batch_size):
        batch = BatchHttpRequest(
            callback=callback, batch_uri="https://www.googleapis.com/batch/gmail/v1"
        )

        for msg in messages[i : i + batch_size]:
            req = (
                service.users().messages().get(userId="me", id=msg["id"], format="full")
            )
            batch.add(req)

        retries = 3
        for attempt in range(retries):
            try:
                batch.execute()
                break
            except HttpError as e:
                if e.resp.status == 429:
                    wait_time = (2**attempt) * delay
                    print(f"Rate limit hit. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"Unexpected error: {e}")
                    break

        time.sleep(delay)

    return detailed_messages


def modify_message_labels(
    service,
    message_ids: List[str],
    add_labels: Optional[List[str]] = None,
    remove_labels: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Modify the labels of Gmail messages.

    Args:
        service: Gmail API service instance
        message_ids: List of message IDs to modify
        add_labels: Labels to add to the messages
        remove_labels: Labels to remove from the messages

    Returns:
        List of modified messages
    """
    if not add_labels and not remove_labels:
        return []

    add_labels = add_labels or []
    remove_labels = remove_labels or []

    batch = service.new_batch_http_request()

    def callback(request_id, response, exception):
        if exception:
            print(f"Error modifying message {request_id}: {exception}")

    for message_id in message_ids:
        batch.add(
            service.users()
            .messages()
            .modify(
                userId="me",
                id=message_id,
                body={"addLabelIds": add_labels, "removeLabelIds": remove_labels},
            ),
            callback=callback,
            request_id=message_id,
        )

    batch.execute()

    # Return the updated messages
    results = []
    for message_id in message_ids:
        try:
            message = (
                service.users().messages().get(userId="me", id=message_id).execute()
            )
            results.append(message)
        except HttpError as error:
            print(f"Error getting message {message_id}: {error}")

    return results


def mark_messages_as_read(service, message_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Mark Gmail messages as read by removing the UNREAD label.

    Args:
        service: Gmail API service instance
        message_ids: List of message IDs to mark as read

    Returns:
        List of modified messages
    """
    return modify_message_labels(service, message_ids, remove_labels=["UNREAD"])


def mark_messages_as_unread(service, message_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Mark Gmail messages as unread by adding the UNREAD label.

    Args:
        service: Gmail API service instance
        message_ids: List of message IDs to mark as unread

    Returns:
        List of modified messages
    """
    return modify_message_labels(service, message_ids, add_labels=["UNREAD"])


def star_messages(service, message_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Star Gmail messages by adding the STARRED label.

    Args:
        service: Gmail API service instance
        message_ids: List of message IDs to star

    Returns:
        List of modified messages
    """
    logger.info(f"Starring {len(message_ids)} messages")
    return modify_message_labels(service, message_ids, add_labels=["STARRED"])


def unstar_messages(service, message_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Unstar Gmail messages by removing the STARRED label.

    Args:
        service: Gmail API service instance
        message_ids: List of message IDs to unstar

    Returns:
        List of modified messages
    """
    logger.info(f"Unstarring {len(message_ids)} messages")
    return modify_message_labels(service, message_ids, remove_labels=["STARRED"])


def trash_messages(service, message_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Move Gmail messages to trash.

    Args:
        service: Gmail API service instance
        message_ids: List of message IDs to trash

    Returns:
        List of modified messages
    """
    logger.info(f"Moving {len(message_ids)} messages to trash")
    batch = service.new_batch_http_request()
    results = []

    def callback(request_id, response, exception):
        if exception:
            logger.error(f"Error trashing message {request_id}: {exception}")
        elif response:
            results.append(response)

    for message_id in message_ids:
        batch.add(
            service.users().messages().trash(userId="me", id=message_id),
            callback=callback,
            request_id=message_id,
        )

    batch.execute()
    return results


def untrash_messages(service, message_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Restore Gmail messages from trash.

    Args:
        service: Gmail API service instance
        message_ids: List of message IDs to restore from trash

    Returns:
        List of modified messages
    """
    logger.info(f"Restoring {len(message_ids)} messages from trash")
    batch = service.new_batch_http_request()
    results = []

    def callback(request_id, response, exception):
        if exception:
            logger.error(f"Error untrashing message {request_id}: {exception}")
        elif response:
            results.append(response)

    for message_id in message_ids:
        batch.add(
            service.users().messages().untrash(userId="me", id=message_id),
            callback=callback,
            request_id=message_id,
        )

    batch.execute()
    return results


def archive_messages(service, message_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Archive Gmail messages by removing the INBOX label.

    Args:
        service: Gmail API service instance
        message_ids: List of message IDs to archive

    Returns:
        List of modified messages
    """
    logger.info(f"Archiving {len(message_ids)} messages")
    return modify_message_labels(service, message_ids, remove_labels=["INBOX"])


def move_to_inbox(service, message_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Move Gmail messages to inbox by adding the INBOX label.

    Args:
        service: Gmail API service instance
        message_ids: List of message IDs to move to inbox

    Returns:
        List of modified messages
    """
    logger.info(f"Moving {len(message_ids)} messages to inbox")
    return modify_message_labels(service, message_ids, add_labels=["INBOX"])


def fetch_thread(service, thread_id: str) -> Dict[str, Any]:
    """
    Fetch a complete email thread with all messages.

    Args:
        service: Gmail API service instance
        thread_id: ID of the thread to fetch

    Returns:
        Thread data including all messages
    """
    logger.info(f"Fetching thread with ID: {thread_id}")
    try:
        # Get thread with all its messages in a single API call
        thread = (
            service.users()
            .threads()
            .get(userId="me", id=thread_id, format="full")
            .execute()
        )

        # Transform messages in the thread for easier frontend processing
        if "messages" in thread:
            thread["messages"] = [
                transform_gmail_message(msg) for msg in thread["messages"]
            ]

            # Sort messages by date (oldest first)
            thread["messages"].sort(key=lambda msg: int(msg.get("internalDate", 0)))

        return thread
    except HttpError as error:
        logger.error(f"Error fetching thread {thread_id}: {error}")
        raise


def search_messages(
    service,
    query: Optional[str] = None,
    max_results: int = 20,
    page_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Search Gmail messages using the Gmail API's advanced search syntax.

    Args:
        service: Gmail API service instance
        query: Search query in Gmail's search syntax
        max_results: Maximum number of results to return
        page_token: Token for pagination

    Returns:
        Dict containing messages and next page token
    """
    logger.info(f"Searching messages with query: {query}")
    try:
        params = {
            "userId": "me",
            "q": query or "",
            "maxResults": max_results,
        }
        if page_token:
            params["pageToken"] = page_token

        # Fetch message list
        results = service.users().messages().list(**params).execute()
        messages = results.get("messages", [])

        # Use batching to fetch full details for each message
        detailed_messages = fetch_detailed_messages(service, messages)

        return {
            "messages": [transform_gmail_message(msg) for msg in detailed_messages],
            "nextPageToken": results.get("nextPageToken"),
        }
    except HttpError as error:
        logger.error(f"Error searching messages: {error}")
        raise


def create_label(
    service,
    name: str,
    label_list_visibility: str = "labelShow",
    message_list_visibility: str = "show",
    background_color: Optional[str] = None,
    text_color: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a new Gmail label.

    Args:
        service: Gmail API service instance
        name: Name of the label
        label_list_visibility: Whether the label appears in the label list
        message_list_visibility: Whether the label appears in the message list
        background_color: Background color of the label (hex code)
        text_color: Text color of the label (hex code)

    Returns:
        Created label data
    """
    logger.info(f"Creating new label: {name}")
    try:
        label_data = {
            "name": name,
            "labelListVisibility": label_list_visibility,
            "messageListVisibility": message_list_visibility,
            "color": {
                "backgroundColor": background_color,
                "textColor": text_color,
            },
        }

        return service.users().labels().create(userId="me", body=label_data).execute()
    except HttpError as error:
        logger.error(f"Error creating label {name}: {error}")
        raise


def update_label(
    service,
    label_id: str,
    name: Optional[str] = None,
    label_list_visibility: Optional[str] = None,
    message_list_visibility: Optional[str] = None,
    background_color: Optional[str] = None,
    text_color: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Update an existing Gmail label.

    Args:
        service: Gmail API service instance
        label_id: ID of the label to update
        name: New name for the label
        label_list_visibility: Whether the label appears in the label list
        message_list_visibility: Whether the label appears in the message list
        background_color: Background color of the label (hex code)
        text_color: Text color of the label (hex code)

    Returns:
        Updated label data
    """
    logger.info(f"Updating label {label_id}")
    try:
        # First get the current label data
        current_label = service.users().labels().get(userId="me", id=label_id).execute()

        # Update with new values if provided
        if name:
            current_label["name"] = name
        if label_list_visibility:
            current_label["labelListVisibility"] = label_list_visibility
        if message_list_visibility:
            current_label["messageListVisibility"] = message_list_visibility

        # Update color information if provided
        if background_color or text_color:
            color_data = {}
            if "color" in current_label:
                color_data = current_label["color"]
            if background_color:
                color_data["backgroundColor"] = background_color
            if text_color:
                color_data["textColor"] = text_color
            current_label["color"] = color_data

        return (
            service.users()
            .labels()
            .update(userId="me", id=label_id, body=current_label)
            .execute()
        )
    except HttpError as error:
        logger.error(f"Error updating label {label_id}: {error}")
        raise


def delete_label(service, label_id: str) -> bool:
    """
    Delete a Gmail label.

    Args:
        service: Gmail API service instance
        label_id: ID of the label to delete

    Returns:
        True if successful
    """
    logger.info(f"Deleting label {label_id}")
    try:
        service.users().labels().delete(userId="me", id=label_id).execute()
        return True
    except HttpError as error:
        logger.error(f"Error deleting label {label_id}: {error}")
        raise


def apply_labels(
    service, message_ids: List[str], label_ids: List[str]
) -> List[Dict[str, Any]]:
    """
    Apply one or more labels to specified messages.

    Args:
        service: Gmail API service instance
        message_ids: List of message IDs
        label_ids: List of label IDs to apply

    Returns:
        List of modified messages
    """
    logger.info(f"Applying labels {label_ids} to {len(message_ids)} messages")
    return modify_message_labels(service, message_ids, add_labels=label_ids)


def remove_labels(
    service, message_ids: List[str], label_ids: List[str]
) -> List[Dict[str, Any]]:
    """
    Remove one or more labels from specified messages.

    Args:
        service: Gmail API service instance
        message_ids: List of message IDs
        label_ids: List of label IDs to remove

    Returns:
        List of modified messages
    """
    logger.info(f"Removing labels {label_ids} from {len(message_ids)} messages")
    return modify_message_labels(service, message_ids, remove_labels=label_ids)


def create_draft(
    service,
    sender: str,
    to_list: List[str],
    subject: str,
    body: str,
    is_html: bool = False,
    cc_list: Optional[List[str]] = None,
    bcc_list: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Create a new Gmail draft.

    Args:
        service: Gmail API service instance
        sender: Email address of the sender
        to_list: Email addresses of recipients
        subject: Email subject
        body: Email body
        is_html: Whether the body is HTML content
        cc_list: Email addresses for CC
        bcc_list: Email addresses for BCC

    Returns:
        Created draft data
    """
    logger.info(f"Creating draft email to {to_list} with subject: {subject}")
    try:
        message = create_message(
            sender=sender,
            to=to_list,
            subject=subject,
            body=body,
            is_html=is_html,
            cc=cc_list,
            bcc=bcc_list,
            attachments=None,
        )

        draft = {"message": message}
        return service.users().drafts().create(userId="me", body=draft).execute()
    except HttpError as error:
        logger.error(f"Error creating draft: {error}")
        raise


def list_drafts(
    service, max_results: int = 20, page_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    List Gmail draft messages.

    Args:
        service: Gmail API service instance
        max_results: Maximum number of drafts to return
        page_token: Token for pagination

    Returns:
        Dict containing drafts and next page token
    """
    logger.info(f"Listing drafts, max_results={max_results}")
    try:
        params = {"userId": "me", "maxResults": max_results}
        if page_token:
            params["pageToken"] = page_token

        results = service.users().drafts().list(**params).execute()
        drafts = results.get("drafts", [])

        # If we have drafts, get full details for each one
        detailed_drafts = []
        for draft in drafts:
            try:
                draft_data = (
                    service.users()
                    .drafts()
                    .get(userId="me", id=draft["id"], format="full")
                    .execute()
                )

                # Transform the message data
                if "message" in draft_data:
                    draft_data["message"] = transform_gmail_message(
                        draft_data["message"]
                    )

                detailed_drafts.append(draft_data)
            except HttpError as error:
                logger.error(f"Error fetching draft {draft['id']}: {error}")

        return {
            "drafts": detailed_drafts,
            "nextPageToken": results.get("nextPageToken"),
        }
    except HttpError as error:
        logger.error(f"Error listing drafts: {error}")
        raise


def get_draft(service, draft_id: str) -> Dict[str, Any]:
    """
    Get a specific Gmail draft.

    Args:
        service: Gmail API service instance
        draft_id: ID of the draft to retrieve

    Returns:
        Draft data with message details
    """
    logger.info(f"Fetching draft {draft_id}")
    try:
        draft = (
            service.users()
            .drafts()
            .get(userId="me", id=draft_id, format="full")
            .execute()
        )

        # Transform the message data
        if "message" in draft:
            draft["message"] = transform_gmail_message(draft["message"])

        return draft
    except HttpError as error:
        logger.error(f"Error fetching draft {draft_id}: {error}")
        raise


def update_draft(
    service,
    draft_id: str,
    sender: str,
    to_list: List[str],
    subject: str,
    body: str,
    is_html: bool = False,
    cc_list: Optional[List[str]] = None,
    bcc_list: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Update an existing Gmail draft.

    Args:
        service: Gmail API service instance
        draft_id: ID of the draft to update
        sender: Email address of the sender
        to_list: Email addresses of recipients
        subject: Email subject
        body: Email body
        is_html: Whether the body is HTML content
        cc_list: Email addresses for CC
        bcc_list: Email addresses for BCC

    Returns:
        Updated draft data
    """
    logger.info(f"Updating draft {draft_id}")
    try:
        message = create_message(
            sender=sender,
            to=to_list,
            subject=subject,
            body=body,
            is_html=is_html,
            cc=cc_list,
            bcc=bcc_list,
            attachments=None,
        )

        draft = {"id": draft_id, "message": message}
        return (
            service.users()
            .drafts()
            .update(userId="me", id=draft_id, body=draft)
            .execute()
        )
    except HttpError as error:
        logger.error(f"Error updating draft {draft_id}: {error}")
        raise


def delete_draft(service, draft_id: str) -> bool:
    """
    Delete a Gmail draft.

    Args:
        service: Gmail API service instance
        draft_id: ID of the draft to delete

    Returns:
        True if successful
    """
    logger.info(f"Deleting draft {draft_id}")
    try:
        service.users().drafts().delete(userId="me", id=draft_id).execute()
        return True
    except HttpError as error:
        logger.error(f"Error deleting draft {draft_id}: {error}")
        raise


def send_draft(service, draft_id: str) -> Dict[str, Any]:
    """
    Send an existing Gmail draft.

    Args:
        service: Gmail API service instance
        draft_id: ID of the draft to send

    Returns:
        Sent message data
    """
    logger.info(f"Sending draft {draft_id}")
    try:
        return (
            service.users().drafts().send(userId="me", body={"id": draft_id}).execute()
        )
    except HttpError as error:
        logger.error(f"Error sending draft {draft_id}: {error}")
        raise


def get_contact_list(service, max_results=100):
    """
    Extract a list of unique contacts (email addresses and names) from the user's Gmail history.

    Args:
        service: Authenticated Gmail API service instance
        max_results: Maximum number of messages to analyze (default: 100)

    Returns:
        List of unique contacts with their email addresses and names
    """
    try:
        # Get messages from inbox, sent, and all mail to maximize contact discovery
        query = "in:inbox OR in:sent OR in:all"

        # First, get message IDs
        results = (
            service.users()
            .messages()
            .list(userId="me", q=query, maxResults=max_results)
            .execute()
        )

        messages = results.get("messages", [])

        # Use a dictionary to track unique contacts
        contacts = {}

        # Process each message to extract contacts
        for msg_data in messages:
            msg_id = msg_data.get("id")
            msg = (
                service.users()
                .messages()
                .get(userId="me", id=msg_id, format="full")
                .execute()
            )

            # Extract headers
            headers = {
                h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])
            }

            # Extract email addresses from From, To, Cc, and Reply-To fields
            for field in ["From", "To", "Cc", "Reply-To"]:
                if field in headers and headers[field]:
                    # Split multiple addresses in a single field
                    addresses = headers[field].split(",")

                    for address in addresses:
                        address = address.strip()
                        if not address:
                            continue

                        # Parse name and email from address string
                        name = ""
                        email = address

                        # Handle format: "Name <email@example.com>"
                        if "<" in address and ">" in address:
                            name = address.split("<")[0].strip()
                            email = address.split("<")[1].split(">")[0].strip()

                        # Only add if it's a valid email address
                        if "@" in email and "." in email:
                            # Add to contacts dict, using email as key to ensure uniqueness
                            contacts[email] = {"name": name, "email": email}

        # Convert dictionary to list for return
        contact_list = list(contacts.values())

        # Sort contacts alphabetically by name, then email
        contact_list.sort(key=lambda x: (x["name"] if x["name"] else x["email"]))

        return contact_list

    except Exception as e:
        print(f"Error getting contact list: {str(e)}")
        return []
