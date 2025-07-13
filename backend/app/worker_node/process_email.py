import asyncio
import base64
from datetime import datetime, timezone
from html import unescape
from typing import Any, Optional

from app.db.mongodb.collections import mail_collection, users_collection
from app.db.redis import get_cache, set_cache
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
from app.services.mail_service import (
    get_gmail_service,
    process_email_comprehensive_analysis,
)
from app.services.user_service import get_user_by_email, get_user_by_id
from app.utils.notification.sources import AIProactiveNotificationSource
from app.utils.oauth_utils import get_tokens_by_user_id
from app.utils.session_logger.email_session_logger import EmailProcessingSession
from bs4 import BeautifulSoup
from bson import ObjectId

# ============================================================================
# Main Processing
# ============================================================================


async def process_emails(history_id: int, email: str, session: EmailProcessingSession):
    """
    Process emails for a user identified by email address.
    This function gets the user info and delegates to process_emails_by_user_id.
    """
    try:
        session.log_milestone("Input validation started")

        if not email or not history_id:
            error_msg = "Email address or history ID is missing"
            session.log_error(
                "VALIDATION_ERROR",
                error_msg,
                {
                    "email_provided": bool(email),
                    "history_id_provided": bool(history_id),
                },
            )
            return {
                "error": error_msg,
                "status": "failed",
            }

        session.log_milestone("User lookup started", {"email": email})

        # Get user information by email
        user = await get_user_by_email(email)
        if not user:
            error_msg = "User not found"
            session.log_error("USER_NOT_FOUND", error_msg, {"email": email})
            return {"error": error_msg, "status": "failed"}

        # Extract user_id from user document
        user_id = str(user.get("_id"))
        if not user_id:
            error_msg = f"No user_id found for email: {email}"
            session.log_error("USER_ID_MISSING", error_msg)
            return {"error": "User ID not found", "status": "failed"}

        session.set_user_id(user_id)
        session.log_milestone(
            "User resolved successfully",
            {"user_id": user_id, "user_name": user.get("name", "Unknown")},
        )

        # Delegate to user_id based processing
        return await process_emails_by_user_id(history_id, user_id, email, session)

    except Exception as e:
        error_msg = f"Error processing email: {e}"
        session.log_error(
            "UNEXPECTED_ERROR", error_msg, {"exception_type": type(e).__name__}
        )
        return {"error": str(e), "status": "failed"}


async def _process_email(
    message: dict,
    user_id: str,
    access_token: str,
    refresh_token: str,
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
                access_token=access_token,
                refresh_token=refresh_token,
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


async def process_emails_by_user_id(
    history_id: int, user_id: str, email: str, session: EmailProcessingSession
):
    """
    Process emails for a user identified by user ID.
    """
    try:
        session.log_milestone(
            "Email processing started", {"user_id": user_id, "history_id": history_id}
        )

        if not user_id or not history_id:
            error_msg = "User ID or history ID is missing"
            session.log_error(
                "VALIDATION_ERROR",
                error_msg,
                {
                    "user_id_provided": bool(user_id),
                    "history_id_provided": bool(history_id),
                },
            )
            return {
                "error": error_msg,
                "status": "failed",
            }

        if not email:
            error_msg = f"No email found for user_id: {user_id}"
            session.log_error("EMAIL_MISSING", error_msg)
            return {"error": "User email not found", "status": "failed"}

        session.log_milestone("History ID lookup started")
        previous_history_id = await _get_history_id_by_user_id(user_id, session)
        if not previous_history_id:
            error_msg = f"Previous History ID not found for user: {user_id}"
            session.log_error("HISTORY_ID_NOT_FOUND", error_msg)
            return {"error": "History not found", "status": "failed"}

        session.log_milestone(
            "Previous history ID retrieved",
            {"previous_history_id": previous_history_id},
        )

        session.log_milestone("Token validation started")
        access_token, refresh_token, tokens_valid = await get_tokens_by_user_id(user_id)
        if not tokens_valid:
            session.log_error("TOKEN_VALIDATION_FAILED", "Authentication failed")
            return {"error": "Authentication failed", "status": "failed"}

        session.log_milestone("Tokens validated successfully")

        session.log_milestone("Gmail service initialization started")
        service = get_gmail_service(
            access_token=access_token,
            refresh_token=refresh_token,
        )

        session.log_milestone("Fetching message history from Gmail API")
        messages = await _fetch_messages_by_history(
            history_id=previous_history_id, service=service, session=session
        )
        history = messages.get("history", [])
        if not history:
            session.log_milestone("No new messages found", {"history_count": 0})
            return {
                "status": "success",
                "message": "No new messages found",
                "history_count": 0,
            }

        added_messages = []
        for item in history:
            if "messagesAdded" in item:
                added_messages.extend(item["messagesAdded"])

        session.log_milestone(
            "Messages identified for processing",
            {"new_messages_count": len(added_messages), "history_items": len(history)},
        )

        session.log_milestone("Fetching full message content")
        full_messages = await fetch_all_messages(
            service=service,
            user_id="me",
            message_ids=[msg["message"]["id"] for msg in added_messages],
            session=session,
        )

        session.log_milestone(
            "Full messages retrieved",
            {
                "full_messages_count": len(full_messages),
                "valid_messages": len(
                    [msg for msg in full_messages if msg is not None]
                ),
            },
        )

        # Process the messages with user context in batches
        session.log_milestone("Batch processing started")
        processing_results = await _process_emails_batch(
            full_messages, user_id, access_token, refresh_token, session
        )

        session.log_milestone(
            "Message processing completed",
            {
                "processed_count": len(processing_results),
                "successful_count": len(
                    [r for r in processing_results if r.get("status") != "error"]
                ),
                "error_count": len(
                    [r for r in processing_results if r.get("status") == "error"]
                ),
            },
        )

        # Update the history ID after processing
        session.log_milestone("Updating history ID")
        await _update_history_id_by_user_id(user_id, history_id, session)

        final_result = {
            "status": "success",
            "message": "Email history processed successfully",
            "user_id": user_id,
            "history_count": len(messages.get("history", [])),
            "processed_messages": len(processing_results),
            "processing_results": processing_results,
        }

        session.log_milestone(
            "Processing completed successfully",
            {"final_status": "success", "total_processed": len(processing_results)},
        )

        return final_result

    except Exception as e:
        error_msg = f"Error processing email for user {user_id}: {e}"
        session.log_error(
            "PROCESSING_ERROR",
            error_msg,
            {"user_id": user_id, "exception_type": type(e).__name__},
        )
        return {"error": str(e), "status": "failed", "user_id": user_id}


async def _process_emails_batch(
    messages: list[dict | None],
    user_id: str,
    access_token: str,
    refresh_token: str,
    session: EmailProcessingSession,
    batch_size: int = 5,
) -> list[dict]:
    """
    Process emails in batches using asyncio.gather for concurrent processing.

    Args:
        messages: List of email messages to process
        user_id: The user ID
        access_token: OAuth access token
        refresh_token: OAuth refresh token
        session: Email processing session for logging
        batch_size: Number of emails to process concurrently in each batch

    Returns:
        list[dict]: List of processing results
    """
    processing_results = []

    # Filter out None messages
    valid_messages = [msg for msg in messages if msg is not None]

    total_batches = (len(valid_messages) + batch_size - 1) // batch_size
    session.log_milestone(
        "Batch processing configuration",
        {
            "total_messages": len(valid_messages),
            "batch_size": batch_size,
            "total_batches": total_batches,
        },
    )

    # Process messages in batches
    for i in range(0, len(valid_messages), batch_size):
        batch = valid_messages[i : i + batch_size]
        batch_number = i // batch_size + 1

        session.log_batch_processing(batch_number, len(batch), total_batches)

        # Create tasks for concurrent processing within the batch
        tasks = [
            _process_email(message, user_id, access_token, refresh_token, session)
            for message in batch
        ]

        # Execute batch concurrently
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle results and exceptions
        for j, result in enumerate(batch_results):
            if isinstance(result, Exception):
                error_msg = f"Error processing message in batch {batch_number}, position {j}: {result}"
                session.log_error(
                    "MESSAGE_PROCESSING_ERROR",
                    error_msg,
                    {
                        "batch_number": batch_number,
                        "position_in_batch": j,
                        "message_id": batch[j].get("id", "unknown"),
                        "exception_type": type(result).__name__,
                    },
                )
                processing_results.append(
                    {
                        "status": "error",
                        "error": str(result),
                        "message_id": batch[j].get("id", "unknown"),
                    }
                )
            else:
                # result is not an exception, so it should be a valid result
                if isinstance(result, dict):
                    processing_results.append(result)
                else:
                    # Handle unexpected result type
                    processing_results.append(
                        {
                            "status": "error",
                            "error": f"Unexpected result type: {type(result)}",
                            "message_id": batch[j].get("id", "unknown"),
                        }
                    )
                session.increment_processed_messages()

    session.log_milestone(
        "Batch processing completed",
        {
            "total_processed": len(processing_results),
            "successful": len(
                [r for r in processing_results if r.get("status") != "error"]
            ),
            "errors": len(
                [r for r in processing_results if r.get("status") == "error"]
            ),
        },
    )

    return processing_results


# ============================================================================
# Email Extraction Utilities
# ============================================================================


def extract_string_content(message: dict) -> str:
    """
    Extracts the string content from a Gmail message.
    Extracted content can be plain text or HTML, depending on the message format.
    If the message is in HTML format, it will be converted to plain text.
    Args:
        message (dict): The Gmail message object.
    Returns:
        str: The extracted string content.
    """

    payload = message.get("payload", {})
    mime_type = payload.get("mimeType", "")

    content = ""

    if mime_type == "text/plain":
        # If the message is already in plain text or HTML format, extract directly
        data = payload.get("body", {}).get("data", "")
        if data:
            decoded_bytes = base64.urlsafe_b64decode(data)
            content += decoded_bytes.decode("utf-8").strip()
    elif mime_type == "text/html":
        # If the message is in HTML format, decode and extract text
        data = payload.get("body", {}).get("data", "")
        if data:
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


def extract_date(message: dict) -> datetime:
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
            date_string = header.get("value", "")
            date_object = datetime.strptime(date_string, "%a, %d %b %Y %H:%M:%S %z")
            return date_object if date_string else datetime.now(timezone.utc)
    return datetime.now(timezone.utc)


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


# ============================================================================
# History ID Management
# ============================================================================


async def _get_history_id_by_user_id(
    user_id: str, session: EmailProcessingSession
) -> int | None:
    """
    Retrieve and validate the history ID from cache or database by user ID.

    Args:
        user_id: The user's ID
        session: Email processing session for logging

    Returns:
        int: History ID or None if not found
    """
    try:
        cache_key = f"gmail_history_id:{user_id}"

        # Try to get history ID from cache first
        cached_history_id = await get_cache(cache_key)
        if cached_history_id:
            session.log_milestone(
                "History ID found in cache",
                {"cache_key": cache_key, "history_id": int(cached_history_id)},
            )
            return int(cached_history_id)

        # If not in cache, get from database
        session.log_milestone("History ID not in cache, checking database")
        user = await get_user_by_id(user_id)
        if not user:
            session.log_error(
                "USER_NOT_FOUND_IN_DB", f"No user found with ID: {user_id}"
            )
            return None

        db_history_id = user.get("gmail_history_id")
        if not db_history_id:
            session.log_error(
                "HISTORY_ID_NOT_IN_DB", f"No history ID found for user: {user_id}"
            )
            return None

        session.log_milestone(
            "History ID found in database", {"history_id": int(db_history_id)}
        )
        return int(db_history_id)

    except (ValueError, TypeError) as e:
        session.log_error(
            "HISTORY_ID_CONVERSION_ERROR", f"Invalid history ID for user {user_id}: {e}"
        )
        return None


async def _update_history_id_by_user_id(
    user_id: str, history_id: int, session: EmailProcessingSession
) -> None:
    """
    Update the history ID in both database and cache by user ID.

    Args:
        user_id: The user's ID
        history_id: The history ID to update
        session: Email processing session for logging
    """

    cache_key = f"gmail_history_id:{user_id}"

    try:
        object_id = ObjectId(user_id)
        result = await users_collection.update_one(
            {"_id": object_id},
            {"$set": {"gmail_history_id": history_id}},
        )

        if result.modified_count > 0:
            # Update in cache
            await set_cache(cache_key, history_id)
            session.log_milestone(
                "History ID updated successfully",
                {
                    "user_id": user_id,
                    "new_history_id": history_id,
                    "cache_updated": True,
                },
            )
        else:
            session.log_error(
                "HISTORY_UPDATE_FAILED", f"No user updated for user_id: {user_id}"
            )

    except Exception as e:
        session.log_error(
            "HISTORY_UPDATE_ERROR", f"Error updating history ID for user {user_id}: {e}"
        )


async def _fetch_messages_by_history(
    history_id: int, service: Any, session: EmailProcessingSession
) -> dict:
    """
    Fetch messages from Gmail API using the history ID.

    Args:
        history_id: The history ID to use for fetching messages
        service: The Gmail API service instance
        session: Email processing session for logging

    Returns:
        dict: The messages response from Gmail API
    """
    session.log_milestone(
        "Gmail API history call started", {"start_history_id": history_id}
    )

    result = await asyncio.to_thread(
        lambda: service.users()
        .history()
        .list(
            userId="me",
            startHistoryId=history_id,
            historyTypes=["messageAdded"],
        )
        .execute()
    )

    session.log_milestone(
        "Gmail API history call completed",
        {"history_items_returned": len(result.get("history", []))},
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
