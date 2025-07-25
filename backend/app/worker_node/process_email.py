import asyncio
import base64
from datetime import datetime, timezone
from html import unescape
from typing import Any, List, Optional, Set, Tuple

from app.config.logger.mail_processing import EmailProcessingSession
from app.db.mongodb.collections import mail_collection, users_collection
from app.db.redis import get_cache, set_cache
from app.langchain.core.agent import call_mail_processing_agent
from app.models.chat_models import (
    MessageModel,
    UpdateMessagesRequest,
)
from app.models.mail_models import EmailComprehensiveAnalysis
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
from bs4 import BeautifulSoup
from bson import ObjectId


class EmailContentExtractor:
    """Handles extraction of various email components from Gmail message objects."""

    @staticmethod
    def extract_string_content(message: dict) -> str:
        """
        Extracts the string content from a Gmail message.
        Extracted content can be plain text or HTML, depending on the message format.
        If the message is in HTML format, it will be converted to plain text.
        """
        payload = message.get("payload", {})
        mime_type = payload.get("mimeType", "")
        content = ""

        if mime_type == "text/plain":
            data = payload.get("body", {}).get("data", "")
            if data:
                decoded_bytes = base64.urlsafe_b64decode(data)
                content += decoded_bytes.decode("utf-8").strip()
        elif mime_type == "text/html":
            data = payload.get("body", {}).get("data", "")
            if data:
                decoded_bytes = base64.urlsafe_b64decode(data)
                html_content = decoded_bytes.decode("utf-8")
                # Convert HTML to plain text using BeautifulSoup
                soup = BeautifulSoup(html_content, "html.parser")
                content += soup.get_text().strip()
        elif mime_type.startswith("multipart/"):
            parts = payload.get("parts", [])
            content += EmailContentExtractor._parse_mail_parts(parts)

        return content.strip()

    @staticmethod
    def _parse_mail_parts(parts: List[dict]) -> str:
        """Recursively parses the parts of a Gmail message to extract text content."""
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
                content += EmailContentExtractor._parse_mail_parts(part["parts"])
        return content.strip()

    @staticmethod
    def extract_subject(message: dict) -> str:
        """Extracts the subject from a Gmail message."""
        headers = message.get("payload", {}).get("headers", [])
        for header in headers:
            if header.get("name") == "Subject":
                return header.get("value", "")
        return ""

    @staticmethod
    def extract_sender(message: dict) -> str:
        """Extracts the sender's email address from a Gmail message."""
        headers = message.get("payload", {}).get("headers", [])
        for header in headers:
            if header.get("name") == "From":
                return header.get("value", "")
        return ""

    @staticmethod
    def extract_date(message: dict) -> datetime:
        """Extracts the date from a Gmail message."""
        headers = message.get("payload", {}).get("headers", [])
        for header in headers:
            if header.get("name") == "Date":
                date_string = header.get("value", "")
                try:
                    date_object = datetime.strptime(
                        date_string, "%a, %d %b %Y %H:%M:%S %z"
                    )
                    return date_object if date_string else datetime.now(timezone.utc)
                except ValueError:
                    return datetime.now(timezone.utc)
        return datetime.now(timezone.utc)

    @staticmethod
    def extract_labels(message: dict) -> List[str]:
        """Extracts the labels from a Gmail message."""
        return message.get("labelIds", [])

    @staticmethod
    def extract_attachments(message: dict) -> List[dict]:
        """Extracts the attachments from a Gmail message."""
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


class HistoryIdManager:
    """Manages Gmail history IDs with proper caching and database operations."""

    def __init__(self):
        self.cache_key_prefix = "gmail_history_id:"

    async def get_stored_history_id(
        self, user_id: str, session: EmailProcessingSession
    ) -> Optional[int]:
        """Retrieve the stored history ID from cache or database."""
        try:
            cache_key = f"{self.cache_key_prefix}{user_id}"

            # Try cache first
            cached_history_id = await get_cache(cache_key)
            if cached_history_id:
                session.log_milestone(
                    "History ID found in cache",
                    {"cache_key": cache_key, "history_id": int(cached_history_id)},
                )
                return int(cached_history_id)

            # Fallback to database
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
                "HISTORY_ID_CONVERSION_ERROR",
                f"Invalid history ID for user {user_id}: {e}",
            )
            return None

    async def update_history_id(
        self, user_id: str, new_history_id: int, session: EmailProcessingSession
    ) -> bool:
        """Update history ID immediately in both database and cache."""
        cache_key = f"{self.cache_key_prefix}{user_id}"

        try:
            object_id = ObjectId(user_id)
            result = await users_collection.update_one(
                {"_id": object_id},
                {"$set": {"gmail_history_id": new_history_id}},
            )

            if result.modified_count > 0:
                # Update in cache
                await set_cache(cache_key, new_history_id)
                session.log_milestone(
                    "History ID updated immediately",
                    {
                        "user_id": user_id,
                        "new_history_id": new_history_id,
                        "cache_updated": True,
                    },
                )
                return True
            else:
                session.log_error(
                    "HISTORY_UPDATE_FAILED", f"No user updated for user_id: {user_id}"
                )
                return False

        except Exception as e:
            session.log_error(
                "HISTORY_UPDATE_ERROR",
                f"Error updating history ID for user {user_id}: {e}",
            )
            return False


class MessageTracker:
    """Tracks messages currently being processed to prevent duplicates."""

    def __init__(self):
        self._processing_messages: Set[str] = set()
        self._lock = asyncio.Lock()

    async def add_messages_to_processing(self, message_ids: List[str]) -> List[str]:
        """Add messages to processing set and return only new ones."""
        async with self._lock:
            new_messages = [
                msg_id
                for msg_id in message_ids
                if msg_id not in self._processing_messages
            ]
            self._processing_messages.update(new_messages)
            return new_messages

    async def remove_messages_from_processing(self, message_ids: List[str]) -> None:
        """Remove messages from processing set."""
        async with self._lock:
            self._processing_messages.difference_update(message_ids)

    async def get_processing_count(self) -> int:
        """Get count of currently processing messages."""
        async with self._lock:
            return len(self._processing_messages)


class GmailApiClient:
    """Handles Gmail API interactions."""

    async def fetch_messages_by_history(
        self, history_id: int, service: Any, session: EmailProcessingSession
    ) -> dict:
        """Fetch messages from Gmail API using history ID."""
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

    async def fetch_message_by_id(
        self, service: Any, user_id: str, msg_id: str, session: EmailProcessingSession
    ) -> Optional[dict]:
        """Fetch a single message by ID."""
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
        self,
        service: Any,
        user_id: str,
        message_ids: List[str],
        session: EmailProcessingSession,
    ) -> List[Optional[dict]]:
        """Fetch all messages by their IDs using the Gmail API."""
        session.log_milestone(
            "Gmail API message fetch started", {"message_count": len(message_ids)}
        )

        tasks = [
            self.fetch_message_by_id(service, user_id, msg_id, session)
            for msg_id in message_ids
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


class ConversationManager:
    """Manages email processing conversations."""

    async def create_email_processing_conversation(
        self, conversation_data: dict, user_id: str, session: EmailProcessingSession
    ) -> Tuple[str, str]:
        """Create or update a conversation for email processing."""
        try:
            system_purpose = conversation_data.get("system_purpose", "email_processing")
            description = conversation_data.get(
                "description", "Email Actions & Notifications"
            )

            # Get or create system conversation
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

            # Create user message
            user_message = MessageModel(
                type="user",
                response=conversation_data.get(
                    "user_message_content", "New email received"
                ),
                date=datetime.now(timezone.utc).isoformat(),
            )
            session.log_milestone(
                "user_message created",
                {"conversation_id": conversation_id, "user_id": user_id},
            )

            # Create bot message with response content
            bot_message_content = conversation_data.get(
                "bot_message_content", "Email processed successfully."
            )
            bot_message = MessageModel(
                type="bot",
                response=bot_message_content,
                date=datetime.now(timezone.utc).isoformat(),
            )

            # Apply tool data to bot message if available
            tool_data = conversation_data.get("tool_data", {})
            if tool_data:
                for key, value in tool_data.items():
                    # Safely set attributes on the bot message
                    if hasattr(bot_message, key):
                        setattr(bot_message, key, value)

            # Update conversation with both messages
            res = await update_messages(
                UpdateMessagesRequest(
                    conversation_id=conversation_id,
                    messages=[user_message, bot_message],
                ),
                user={"user_id": user_id},
            )

            # Get the user message ID from the response
            message_ids = res.get("message_ids", [])
            if not message_ids or len(message_ids) < 1:
                session.log_error(
                    "MESSAGE_ID_ERROR",
                    f"No message IDs returned for user {user_id}",
                    {"user_id": user_id, "conversation_id": conversation_id},
                )
                raise ValueError(f"No message IDs returned for user {user_id}")

            user_message_id = message_ids[0]
            session.log_milestone(
                f"Email processing conversation updated for user {user_id} with {len(tool_data)} tool outputs",
                {
                    "conversation_id": conversation_id,
                    "user_message_id": user_message_id,
                    "tool_data_count": len(tool_data),
                },
            )

            if not user_message_id or not isinstance(user_message_id, str):
                session.log_error(
                    "MESSAGE_ID_ERROR",
                    f"Invalid user_message_id: {user_message_id} for user {user_id}",
                    {"user_id": user_id, "conversation_id": conversation_id},
                )
                raise ValueError(
                    f"Invalid user_message_id: {user_message_id} for user {user_id}"
                )

            return user_message_id, conversation_id

        except Exception as e:
            session.log_error(
                "CONVERSATION_UPDATE_ERROR",
                f"Error creating email processing conversation for user {user_id}: {str(e)}",
                {"user_id": user_id},
            )
            raise e


class EmailProcessor:
    """Main email processing class that orchestrates the entire workflow."""

    def __init__(self):
        self.content_extractor = EmailContentExtractor()
        self.history_manager = HistoryIdManager()
        self.message_tracker = MessageTracker()
        self.gmail_client = GmailApiClient()
        self.conversation_manager = ConversationManager()

    async def process_emails_by_email_address(
        self, history_id: int, email: str, session: EmailProcessingSession
    ) -> dict:
        """Process emails for a user identified by email address."""
        try:
            session.log_milestone("Email processing started", {"email": email})

            # Basic validation
            if not email or not history_id:
                error_msg = "Email address or history ID is missing"
                session.log_error("VALIDATION_ERROR", error_msg)
                return {"error": error_msg, "status": "failed"}

            # Get user by email
            user = await get_user_by_email(email)
            if not user:
                error_msg = "User not found"
                session.log_error("USER_NOT_FOUND", error_msg, {"email": email})
                return {"error": error_msg, "status": "failed"}

            # Extract user_id
            user_id = str(user.get("_id"))
            if not user_id:
                error_msg = f"No user_id found for email: {email}"
                session.log_error("USER_ID_MISSING", error_msg)
                return {"error": "User ID not found", "status": "failed"}

            session.set_user_id(user_id)
            session.log_milestone("User resolved", {"user_id": user_id})

            # Delegate to user_id based processing
            return await self.process_emails_by_user_id(
                history_id, user_id, email, session
            )

        except Exception as e:
            error_msg = f"Error processing email: {e}"
            session.log_error("UNEXPECTED_ERROR", error_msg)
            return {"error": str(e), "status": "failed"}

    async def process_emails_by_user_id(
        self,
        new_history_id: int,
        user_id: str,
        email: str,
        session: EmailProcessingSession,
    ) -> dict:
        """Process emails for a user identified by user ID."""
        try:
            session.log_milestone(
                "Email processing started",
                {"user_id": user_id, "new_history_id": new_history_id},
            )

            # Get stored history ID
            stored_history_id = await self.history_manager.get_stored_history_id(
                user_id, session
            )
            if not stored_history_id:
                error_msg = f"Previous History ID not found for user: {user_id}"
                session.log_error("HISTORY_ID_NOT_FOUND", error_msg)
                return {"error": "History not found", "status": "failed"}

            # CRITICAL: Update history ID immediately to prevent race conditions
            session.log_milestone(
                "Updating history ID immediately to prevent race conditions"
            )
            history_updated = await self.history_manager.update_history_id(
                user_id, new_history_id, session
            )

            if not history_updated:
                session.log_error(
                    "IMMEDIATE_HISTORY_UPDATE_FAILED",
                    "Failed to update history ID immediately",
                )
                return {"error": "Failed to update history ID", "status": "failed"}

            # Get and validate tokens
            session.log_milestone("Token validation started")
            access_token, refresh_token, tokens_valid = await get_tokens_by_user_id(
                user_id
            )
            if not tokens_valid:
                session.log_error("TOKEN_VALIDATION_FAILED", "Authentication failed")
                return {"error": "Authentication failed", "status": "failed"}

            # Get Gmail service
            session.log_milestone("Gmail service initialization started")
            service = get_gmail_service(
                access_token=access_token, refresh_token=refresh_token
            )

            # Fetch messages using stored history ID
            session.log_milestone("Fetching message history from Gmail API")
            messages = await self.gmail_client.fetch_messages_by_history(
                stored_history_id, service, session
            )

            history = messages.get("history", [])
            if not history:
                session.log_milestone("No new messages found", {"history_count": 0})
                return {
                    "status": "success",
                    "message": "No new messages found",
                    "history_count": 0,
                }

            # Extract added messages
            added_messages = []
            for item in history:
                if "messagesAdded" in item:
                    added_messages.extend(item["messagesAdded"])

            message_ids = [msg["message"]["id"] for msg in added_messages]
            session.log_milestone(
                "Messages identified for processing",
                {"new_messages_count": len(message_ids), "history_items": len(history)},
            )

            # Filter out already processing messages
            new_message_ids = await self.message_tracker.add_messages_to_processing(
                message_ids
            )

            if len(new_message_ids) < len(message_ids):
                session.log_milestone(
                    "Some messages already being processed",
                    {
                        "total_messages": len(message_ids),
                        "new_messages": len(new_message_ids),
                        "already_processing": len(message_ids) - len(new_message_ids),
                    },
                )

            if not new_message_ids:
                session.log_milestone("All messages already being processed")
                return {
                    "status": "success",
                    "message": "All messages already being processed",
                    "history_count": len(history),
                }

            try:
                # Fetch full messages
                session.log_milestone("Fetching full message content")
                full_messages = await self.gmail_client.fetch_all_messages(
                    service, "me", new_message_ids, session
                )

                # Process messages
                session.log_milestone("Batch processing started")
                processing_results = await self._process_messages_in_batches(
                    full_messages, user_id, access_token, refresh_token, session
                )

                session.log_milestone(
                    "Message processing completed",
                    {
                        "processed_count": len(processing_results),
                        "successful_count": len(
                            [
                                r
                                for r in processing_results
                                if r.get("status") != "error"
                            ]
                        ),
                        "error_count": len(
                            [
                                r
                                for r in processing_results
                                if r.get("status") == "error"
                            ]
                        ),
                    },
                )

                return {
                    "status": "success",
                    "message": "Email history processed successfully",
                    "user_id": user_id,
                    "history_count": len(history),
                    "processed_messages": len(processing_results),
                    "processing_results": processing_results,
                }

            finally:
                # Always remove messages from processing tracker
                await self.message_tracker.remove_messages_from_processing(
                    new_message_ids
                )

        except Exception as e:
            error_msg = f"Error processing email for user {user_id}: {e}"
            session.log_error(
                "PROCESSING_ERROR",
                error_msg,
                {"user_id": user_id, "exception_type": type(e).__name__},
            )
            return {"error": str(e), "status": "failed", "user_id": user_id}

    async def _process_messages_in_batches(
        self,
        messages: List[Optional[dict]],
        user_id: str,
        access_token: str,
        refresh_token: str,
        session: EmailProcessingSession,
        batch_size: int = 5,
    ) -> List[dict]:
        """Process messages in batches using asyncio.gather for concurrent processing."""
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

            # Create tasks for concurrent processing
            tasks = [
                self._process_single_message(
                    message, user_id, access_token, refresh_token, session
                )
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
                    if isinstance(result, dict):
                        processing_results.append(result)
                    else:
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

    async def _process_single_message(
        self,
        message: dict,
        user_id: str,
        access_token: str,
        refresh_token: str,
        session: EmailProcessingSession,
    ) -> dict:
        """Process a single email message with user context."""
        # Extract message components
        content = self.content_extractor.extract_string_content(message)
        subject = self.content_extractor.extract_subject(message)
        sender = self.content_extractor.extract_sender(message)
        date = self.content_extractor.extract_date(message)
        labels = self.content_extractor.extract_labels(message)
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
            # Comprehensive email analysis
            analysis_result = await process_email_comprehensive_analysis(
                subject=subject, sender=sender, date=date, content=content
            )

            if analysis_result:
                session.log_milestone(
                    f"Email comprehensive analysis completed for {message_id}",
                    {
                        "importance_level": analysis_result.importance_level,
                        "has_summary": bool(analysis_result.summary),
                        "labels_count": len(analysis_result.semantic_labels),
                    },
                )

                # Update email metadata
                email_metadata["comprehensive_analysis"] = {
                    "importance_level": analysis_result.importance_level,
                    "is_important": analysis_result.is_important,
                    "summary": analysis_result.summary,
                    "semantic_labels": analysis_result.semantic_labels,
                    "analyzed_at": datetime.now(timezone.utc).isoformat(),
                }

                # Store in database
                await self._store_email_analysis_in_database(
                    user_id,
                    message_id,
                    subject,
                    sender,
                    date,
                    labels,
                    content,
                    analysis_result,
                    session,
                )
            else:
                session.log_error(
                    "COMPREHENSIVE_ANALYSIS_FAILED",
                    f"Failed to analyze email for {message_id}",
                    {"message_id": message_id},
                )

            # Process important emails with agent
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
                        "is_important": analysis_result.is_important
                        if analysis_result
                        else False,
                        "message_id": message_id,
                    },
                )

                result = {
                    "status": "skipped",
                    "message": "Email not important - skipped agent processing",
                    "message_id": message_id,
                    "is_important": False,
                }

            # Handle conversation creation and notifications
            await self._handle_conversation_and_notifications(
                result=result,
                user_id=user_id,
                subject=subject,
                analysis_result=analysis_result,
                session=session,
            )

            session.log_message_result(message_id, result)
            return result

        except Exception as e:
            error_result = {
                "status": "error",
                "error": str(e),
                "message_id": message_id,
            }
            session.log_message_result(message_id, error_result)
            session.log_error(
                "MESSAGE_PROCESSING_ERROR",
                f"Error processing message {message_id}: {e}",
                {"message_id": message_id, "exception_type": type(e).__name__},
            )
            return error_result

    async def _store_email_analysis_in_database(
        self,
        user_id: str,
        message_id: str,
        subject: str,
        sender: str,
        date: datetime,
        labels: List[str],
        content: str,
        analysis_result: Any,
        session: EmailProcessingSession,
    ):
        """Store email analysis results in the database."""
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

            await mail_collection.insert_one(email_doc)

            session.log_milestone(
                f"Email analysis stored successfully for {message_id}",
                {"message_id": message_id, "user_id": user_id},
            )
        except Exception as e:
            session.log_error(
                "DATABASE_STORAGE_ERROR",
                f"Failed to store email analysis for {message_id}: {e}",
                {"message_id": message_id, "user_id": user_id},
            )
            raise e

    async def _handle_conversation_and_notifications(
        self,
        result: dict,
        user_id: str,
        subject: str,
        analysis_result: EmailComprehensiveAnalysis,
        session: EmailProcessingSession,
    ):
        """Handle conversation creation and notifications based on processing result."""
        try:
            # Only handle important emails that were successfully processed
            if (
                result.get("status") == "success"
                and analysis_result
                and analysis_result.is_important
                and result.get("conversation_data")
            ):
                session.log_milestone(
                    "Creating email processing conversation",
                    {"user_id": user_id, "subject": subject},
                )

                # Extract conversation data from the LLM agent result
                conversation_data = result.get("conversation_data", {})
                user_message_content = conversation_data.get(
                    "user_message_content", f"New important email received: {subject}"
                )
                bot_message_content = conversation_data.get("bot_message_content", "")
                tool_data = conversation_data.get("tool_data", {})

                # Create conversation with simplified data
                try:
                    (
                        user_message_id,
                        conversation_id,
                    ) = await self.conversation_manager.create_email_processing_conversation(
                        {
                            "user_message_content": user_message_content,
                            "bot_message_content": bot_message_content,
                            "tool_data": tool_data,
                            "system_purpose": "email_processing",
                            "description": "Email Actions & Notifications",
                        },
                        user_id,
                        session,
                    )

                    if user_message_id and conversation_id:
                        session.log_milestone(
                            f"Conversation created successfully for {user_id}",
                            {
                                "conversation_id": conversation_id,
                                "user_message_id": user_message_id,
                            },
                        )

                        # Send notification only if conversation creation was successful
                        try:
                            await AIProactiveNotificationSource.create_proactive_notification(
                                user_id=user_id,
                                conversation_id=conversation_id,
                                message_id=user_message_id,
                                title="Important Email Processed",
                                body=f"I've processed an important email: {subject}. Check the conversation for actions taken.",
                                source=NotificationSourceEnum.EMAIL_TRIGGER,
                                send=True,
                            )
                            session.log_milestone(
                                f"Proactive notification sent for {user_id}",
                                {
                                    "conversation_id": conversation_id,
                                    "subject": subject,
                                },
                            )
                        except Exception as notification_error:
                            session.log_error(
                                "NOTIFICATION_CREATION_FAILED",
                                f"Failed to create notification for {user_id}: {notification_error}",
                                {"conversation_id": conversation_id},
                            )
                    else:
                        session.log_error(
                            "CONVERSATION_CREATION_FAILED",
                            f"Failed to create conversation for {user_id} - invalid IDs returned",
                        )

                except Exception as conv_error:
                    session.log_error(
                        "CONVERSATION_CREATION_ERROR",
                        f"Error creating conversation for {user_id}: {conv_error}",
                        {"user_id": user_id},
                    )
            else:
                session.log_milestone(
                    f"No conversation created for {user_id}",
                    {
                        "status": result.get("status"),
                        "is_important": analysis_result.is_important
                        if analysis_result
                        else False,
                        "has_conversation_data": bool(result.get("conversation_data")),
                    },
                )

        except Exception as e:
            session.log_error(
                "CONVERSATION_HANDLING_ERROR",
                f"Error handling conversation for {user_id}: {e}",
                {"user_id": user_id, "exception_type": type(e).__name__},
            )


# Initialize the email processor
email_processor = EmailProcessor()
