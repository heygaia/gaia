import asyncio
import base64
from datetime import datetime, timezone
from html import unescape
from typing import Any, Optional

from app.db.mongodb.collections import mail_collection
from app.langchain.core.agent import call_mail_processing_agent
from app.models.chat_models import (
    MessageModel,
    UpdateMessagesRequest,
)
from app.models.notification.notification_models import NotificationSourceEnum
from app.services.conversation_service import (
    get_or_create_system_conversation,
    update_messages,
)
from app.services.email_importance_service import process_email_comprehensive_analysis
from app.utils.notification.sources import AIProactiveNotificationSource
from app.utils.session_logger.email_session_logger import EmailProcessingSession
from bs4 import BeautifulSoup

# ============================================================================
# Main Processing
# ============================================================================


async def process_composio_email(
    user_id: str, email_data: dict, session: EmailProcessingSession
):
    """
    Process a single email from Composio webhook data.

    Args:
        user_id (str): The user ID
        email_data (dict): The email data from Composio webhook
        session (EmailProcessingSession): Email processing session for logging

    Returns:
        dict: Processing result
    """
    try:
        session.log_milestone("Composio email processing started", {"user_id": user_id})

        if not user_id or not email_data:
            error_msg = "User ID or email data is missing"
            session.log_error(
                "VALIDATION_ERROR",
                error_msg,
                {
                    "user_id_provided": bool(user_id),
                    "email_data_provided": bool(email_data),
                },
            )
            return {
                "error": error_msg,
                "status": "failed",
            }

        # Extract email details from Composio data
        content = email_data.get("message_text", "")
        subject = email_data.get("subject", "")
        sender = email_data.get("sender", "")
        message_id = email_data.get("message_id", "")

        session.log_milestone(
            "Email data extracted",
            {
                "message_id": message_id,
                "subject": subject,
                "sender": sender,
                "has_content": bool(content),
            },
        )

        # Convert Composio data to Gmail message format for processing
        gmail_message = _convert_composio_to_gmail_format(email_data)

        # Process the email using the existing _process_email function
        result = await _process_email(
            message=gmail_message,
            user_id=user_id,
            session=session,
        )

        session.log_milestone(
            "Composio email processing completed",
            {
                "status": result.get("status", "unknown"),
                "message_id": message_id,
            },
        )

        return result

    except Exception as e:
        error_msg = f"Error processing Composio email: {e}"
        session.log_error(
            "UNEXPECTED_ERROR", error_msg, {"exception_type": type(e).__name__}
        )
        return {"error": str(e), "status": "failed"}


def _convert_composio_to_gmail_format(email_data: dict) -> dict:
    """
    Convert Composio email data to Gmail API message format for compatibility
    with existing processing functions.

    Args:
        email_data (dict): Email data from Composio webhook

    Returns:
        dict: Gmail API compatible message format
    """
    # Extract data
    payload_data = email_data.get("payload", {})
    headers = payload_data.get("headers", [])

    # Create Gmail-compatible headers list
    gmail_headers = []

    # Add standard headers from Composio data
    if email_data.get("subject"):
        gmail_headers.append({"name": "Subject", "value": email_data["subject"]})
    if email_data.get("sender"):
        gmail_headers.append({"name": "From", "value": email_data["sender"]})
    if email_data.get("message_timestamp"):
        gmail_headers.append({"name": "Date", "value": email_data["message_timestamp"]})

    # Add any additional headers from payload
    if isinstance(headers, list):
        gmail_headers.extend(headers)

    # Create Gmail-compatible message structure
    gmail_message = {
        "id": email_data.get("message_id", ""),
        "threadId": email_data.get("thread_id", ""),
        "labelIds": email_data.get("label_ids", []),
        "payload": {
            "mimeType": payload_data.get("mimeType", "text/plain"),
            "headers": gmail_headers,
            "body": {"data": email_data.get("message_text", "")},
            "parts": payload_data.get("parts", []),
        },
    }

    return gmail_message


async def _process_email(
    message: dict,
    user_id: str,
    session: EmailProcessingSession,
):
    """Process individual email message with user context."""
    # Extract relevant information from the message
    content = extract_string_content(message)
    subject = extract_subject(message)
    sender = extract_sender(message)
    date = extract_date(message)
    labels = extract_labels(message)
    message_id = message.get("id", "")

    session.log_message_processing(message_id, subject, sender)

    # Create email metadata
    email_metadata = {
        "subject": subject,
        "sender": sender,
        "date": date,
        "labels": labels,
        "message_id": message_id,
    }

    try:
        # Process email with Gemini for comprehensive analysis (importance + semantic labels in one call)
        analysis_result = await process_email_comprehensive_analysis(
            subject=subject, sender=sender, date=date, content=content
        )

        # Log the comprehensive analysis result
        if analysis_result:
            session.log_milestone(
                f"Email comprehensive analysis completed for {message_id}",
                {
                    "is_important": analysis_result.is_important,
                    "importance_level": analysis_result.importance_level,
                    "has_summary": bool(analysis_result.summary),
                    "labels_count": len(analysis_result.semantic_labels),
                },
            )

            # Store the analysis result in the email metadata for later use
            email_metadata["comprehensive_analysis"] = {
                "is_important": analysis_result.is_important,
                "importance_level": analysis_result.importance_level,
                "summary": analysis_result.summary,
                "semantic_labels": analysis_result.semantic_labels,
                "analyzed_at": datetime.now(timezone.utc).isoformat(),
            }
        else:
            session.log_error(
                "COMPREHENSIVE_ANALYSIS_FAILED",
                f"Failed to analyze email for {message_id}",
                {"message_id": message_id},
            )

        # Store email analysis in database
        if analysis_result:
            try:
                email_doc = {
                    "user_id": user_id,
                    "message_id": message_id,
                    "subject": subject,
                    "sender": sender,
                    "date": date,
                    "labels": labels,
                    "analyzed_at": datetime.now(timezone.utc),
                    "content_preview": (content[:500] if content else ""),
                    "is_important": analysis_result.is_important,
                    "importance_level": analysis_result.importance_level,
                    "summary": analysis_result.summary,
                    "semantic_labels": analysis_result.semantic_labels,
                }

                # Upsert email document (update if exists, insert if not)
                await mail_collection.update_one(
                    {"user_id": user_id, "message_id": message_id},
                    {"$set": email_doc},
                    upsert=True,
                )

                session.log_milestone(
                    f"Email comprehensive analysis stored in database for {message_id}",
                    {
                        "user_id": user_id,
                        "message_id": message_id,
                        "is_important": analysis_result.is_important,
                        "importance_level": analysis_result.importance_level,
                        "semantic_labels_count": len(analysis_result.semantic_labels),
                    },
                )
            except Exception as db_error:
                session.log_error(
                    "DATABASE_STORAGE_ERROR",
                    f"Failed to store email analysis in database: {db_error}",
                    {"message_id": message_id, "user_id": user_id},
                )

        # Only call the mail processing agent for important emails
        result = None
        if analysis_result and analysis_result.is_important:
            session.log_milestone(
                f"Email {message_id} is important - calling mail processing agent",
                {
                    "importance_level": analysis_result.importance_level,
                    "message_id": message_id,
                },
            )

            result = await call_mail_processing_agent(
                email_content=content,
                user_id=user_id,
                email_metadata=email_metadata,
            )
        else:
            session.log_milestone(
                f"Email {message_id} is not important - skipping mail processing agent",
                {
                    "is_important": (
                        analysis_result.is_important if analysis_result else False
                    ),
                    "message_id": message_id,
                },
            )

            # Create a simple result for non-important emails
            result = {
                "status": "skipped",
                "message": "Email not important - skipped agent processing",
                "message_id": message_id,
                "is_important": False,
            }

        user_message_id = conversation_id = None

        # Handle conversation creation only for important emails that have conversation data
        if result.get("conversation_data"):
            try:
                conversation_data = await _create_email_processing_conversation(
                    conversation_data=result["conversation_data"],
                    user_id=user_id,
                    session=session,
                )

                if conversation_data:
                    user_message_id, conversation_id = conversation_data

                session.log_milestone(
                    f"Email processing conversation created/updated for message {message_id}"
                )
            except Exception as conv_error:
                session.log_error(
                    "CONVERSATION_CREATION_ERROR",
                    f"Failed to create conversation for message {message_id}: {conv_error}",
                    {"message_id": message_id, "user_id": user_id},
                )

        # Create Notification only for important emails
        if (
            user_message_id
            and conversation_id
            and analysis_result
            and analysis_result.is_important
        ):
            await AIProactiveNotificationSource.create_proactive_notification(
                user_id=user_id,
                conversation_id=conversation_id,
                message_id=user_message_id,
                title=f"Important Mail: {subject}",
                body=f"Your important email '{subject}' has been processed. {analysis_result.summary[:100]}{'...' if len(analysis_result.summary) > 100 else ''}",
                source=NotificationSourceEnum.EMAIL_TRIGGER,
                send=True,
            )

            session.log_milestone(
                "Notification created for important email processing",
                {
                    "user_id": user_id,
                    "message_id": user_message_id,
                    "importance_level": analysis_result.importance_level,
                },
            )
        else:
            session.log_milestone(
                f"No notification created for email {message_id}",
                {
                    "is_important": (
                        analysis_result.is_important if analysis_result else False
                    ),
                    "has_conversation": bool(user_message_id and conversation_id),
                },
            )

        session.log_message_result(message_id, result)
        return result

    except Exception as e:
        error_result = {"status": "error", "error": str(e), "message_id": message_id}
        session.log_message_result(message_id, error_result)
        return error_result


# ============================================================================
# Email Extraction Utilities
# ============================================================================


def extract_string_content(message: dict) -> str:
    """
    Extracts the string content from a Gmail message or Composio email data.
    Extracted content can be plain text or HTML, depending on the message format.
    If the message is in HTML format, it will be converted to plain text.
    Args:
        message (dict): The Gmail message object or Composio converted message.
    Returns:
        str: The extracted string content.
    """

    payload = message.get("payload", {})
    mime_type = payload.get("mimeType", "")

    content = ""

    # Check if this is a Composio message (has message_text directly)
    if "message_text" in message:
        content = message.get("message_text", "")
        # If it's HTML, convert to plain text
        if "<" in content and ">" in content:  # Simple HTML detection
            soup = BeautifulSoup(unescape(content), "html.parser")
            content = soup.get_text()
        return content.strip()

    # Handle Gmail API format
    if mime_type == "text/plain":
        # If the message is already in plain text format, extract directly
        data = payload.get("body", {}).get("data", "")
        if data:
            # Check if data is already decoded (from Composio conversion)
            if isinstance(data, str) and not data.startswith("="):  # Not base64
                content = data
            else:
                decoded_bytes = base64.urlsafe_b64decode(data)
                content += decoded_bytes.decode("utf-8").strip()
    elif mime_type == "text/html":
        # If the message is in HTML format, decode and extract text
        data = payload.get("body", {}).get("data", "")
        if data:
            # Check if data is already decoded (from Composio conversion)
            if isinstance(data, str) and not data.startswith("="):  # Not base64
                soup = BeautifulSoup(unescape(data), "html.parser")
                content = soup.get_text()
            else:
                decoded_bytes = base64.urlsafe_b64decode(data)
                html_data = decoded_bytes.decode("utf-8")
                soup = BeautifulSoup(unescape(html_data), "html.parser")
                content += soup.get_text()
    elif mime_type.startswith("multipart/"):
        # If the message is multipart, we need to check its parts
        parts = payload.get("parts", [])

        if parts:
            content += _parse_mail_parts(parts)

    return content.strip()


def _parse_mail_parts(parts: list[dict]) -> str:
    """
    Recursively parses the parts of a Gmail message to extract text content.
    Args:
        parts (list[dict]): The list of parts in the Gmail message.
    Returns:
        str: The combined text content from all parts.
    """
    content = ""
    for part in parts:
        mime_type = part.get("mimeType", "")
        if mime_type == "text/plain":
            data = part.get("body", {}).get("data", "")
            if data:
                decoded_bytes = base64.urlsafe_b64decode(data)
                content += decoded_bytes.decode("utf-8")
        elif mime_type == "text/html":
            data = part.get("body", {}).get("data", "")
            if data:
                decoded_bytes = base64.urlsafe_b64decode(data)
                html_data = decoded_bytes.decode("utf-8")
                soup = BeautifulSoup(unescape(html_data), "html.parser")
                content += soup.get_text()
        elif "parts" in part:
            content += _parse_mail_parts(part["parts"])
    return content.strip()


def extract_subject(message: dict) -> str:
    """
    Extracts the subject from a Gmail message.
    Args:
        message (dict): The Gmail message object.
    Returns:
        str: The subject of the email.
    """
    headers = message.get("payload", {}).get("headers", [])
    for header in headers:
        if header.get("name") == "Subject":
            return header.get("value", "")
    return ""


def extract_sender(message: dict) -> str:
    """
    Extracts the sender's email address from a Gmail message.
    Args:
        message (dict): The Gmail message object.
    Returns:
        str: The sender's email address.
    """
    headers = message.get("payload", {}).get("headers", [])
    for header in headers:
        if header.get("name") == "From":
            return header.get("value", "")
    return ""


def extract_date(message: dict) -> str:
    """
    Extracts the date from a Gmail message.
    Args:
        message (dict): The Gmail message object.
    Returns:
        str: The date of the email.
    """
    headers = message.get("payload", {}).get("headers", [])
    for header in headers:
        if header.get("name") == "Date":
            return header.get("value", "")
    return ""


def extract_labels(message: dict) -> list[str]:
    """
    Extracts the labels from a Gmail message.
    Args:
        message (dict): The Gmail message object.
    Returns:
        list[str]: A list of labels associated with the email.
    """
    return message.get("labelIds", [])


def extract_attachments(message: dict) -> list[dict]:
    """
    Extracts the attachments from a Gmail message.
    Args:
        message (dict): The Gmail message object.
    Returns:
        list[dict]: A list of attachment objects.
    """
    attachments = []
    parts = message.get("payload", {}).get("parts", [])

    for part in parts:
        if part.get("filename") and part.get("body", {}).get("attachmentId"):
            attachments.append(
                {
                    "filename": part["filename"],
                    "attachmentId": part["body"]["attachmentId"],
                    "mimeType": part.get("mimeType", ""),
                    "messageId": message.get("id", ""),
                }
            )

    return attachments


# ============================================================================
# Gmail Service Utilities
# ============================================================================


async def process_attachment(attachment: dict, service: Any, user_id: str) -> dict:
    """
    Processes an attachment by fetching its content from Gmail API.

    Args:
        attachment (dict): The attachment object containing filename and attachmentId.
        service: The Gmail API service instance.
        user_id (str): The user ID for the Gmail API.

    Returns:
        dict: A dictionary containing the filename and content of the attachment.
    """
    attachment_id = attachment.get("attachmentId")
    if not attachment_id:
        return {}

    attachment_content = await asyncio.to_thread(
        lambda: service.users()
        .messages()
        .attachments()
        .get(userId=user_id, id=attachment_id, messageId=attachment.get("messageId"))
        .execute()
    )

    return {
        "filename": attachment.get("filename"),
        "data": attachment_content.get("data"),
        "mimeType": attachment.get("mimeType"),
    }


async def fetch_message_by_id(
    service, user_id, msg_id, session: EmailProcessingSession
):
    try:
        return await asyncio.to_thread(
            lambda: service.users()
            .messages()
            .get(userId=user_id, id=msg_id, format="full")
            .execute()
        )
    except Exception as e:
        session.log_error(
            "MESSAGE_FETCH_ERROR",
            f"Failed to fetch message {msg_id}: {e}",
            {"message_id": msg_id, "exception_type": type(e).__name__},
        )
        return None


async def fetch_all_messages(
    service, user_id, message_ids, session: EmailProcessingSession
):
    """
    Fetches all messages by their IDs using the Gmail API.

    Args:
        service: The Gmail API service instance.
        user_id: The user ID for the Gmail API.
        message_ids: A list of message IDs to fetch.
        session: Email processing session for logging

    Returns:
        list: A list of full message objects.
    """
    session.log_milestone(
        "Gmail API message fetch started", {"message_count": len(message_ids)}
    )

    tasks = [
        fetch_message_by_id(service, user_id, msg_id, session) for msg_id in message_ids
    ]
    result = await asyncio.gather(*tasks)

    valid_messages = [msg for msg in result if msg is not None]
    session.log_milestone(
        "Gmail API message fetch completed",
        {
            "requested": len(message_ids),
            "successful": len(valid_messages),
            "failed": len(message_ids) - len(valid_messages),
        },
    )

    return result


async def _create_email_processing_conversation(
    conversation_data: dict, user_id: str, session: EmailProcessingSession
) -> Optional[tuple[str, str]]:
    """
    Create or update a conversation for email processing using system conversation helpers.

    Args:
        conversation_data: Dictionary containing conversation details from call_mail_processing_agent
        user_id: User ID for context
        session: Email processing session for logging

    Returns:
        Optional[tuple[str, str]]: Tuple containing user message ID and conversation ID
        or None if creation failed
    """
    try:
        system_purpose = conversation_data.get("system_purpose", "email_processing")
        description = conversation_data.get(
            "description", "Email Actions & Notifications"
        )

        # Get or create system conversation using the helper function
        conversation = await get_or_create_system_conversation(
            user_id=user_id, system_purpose=system_purpose, description=description
        )

        conversation_id = conversation["conversation_id"]

        session.log_milestone(
            "System conversation retrieved/created",
            {
                "conversation_id": conversation_id,
                "system_purpose": system_purpose,
                "description": description,
                "user_id": user_id,
            },
        )

        # Create user message with email content
        user_message = MessageModel(
            type="user",
            response=conversation_data["user_message_content"],
            date=datetime.now(timezone.utc).isoformat(),
        )

        # Create bot message with AI response and tool data
        bot_message = MessageModel(
            type="bot",
            response="",
            date=datetime.now(timezone.utc).isoformat(),
        )

        # Apply tool data fields to bot message if available
        tool_data = conversation_data.get("tool_data", {})
        if tool_data:
            for key, value in tool_data.items():
                setattr(bot_message, key, value)

        # Update conversation with both messages
        res = await update_messages(
            UpdateMessagesRequest(
                conversation_id=conversation_id,
                messages=[user_message, bot_message],
            ),
            user={"user_id": user_id},
        )
        user_message_id = res["message_ids"][0]

        session.log_milestone(
            f"Email processing conversation updated for user {user_id} with {len(tool_data)} tool outputs"
        )

        if not user_message_id or not isinstance(user_message_id, str):
            session.log_error(
                "MESSAGE_ID_ERROR",
                f"Failed to get user message_id for user {user_id}",
                {"user_id": user_id, "conversation_id": conversation_id},
            )
            return None

        return user_message_id, conversation_id

    except Exception as e:
        session.log_error(
            "CONVERSATION_UPDATE_ERROR",
            f"Error creating email processing conversation for user {user_id}: {str(e)}",
            {"user_id": user_id},
        )
        raise e
