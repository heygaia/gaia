"""
Email processing session logger.

This module provides email-specific session logging that extends the base session logger.
"""

from typing import Any, Dict, Optional

from .base_session_logger import BaseProcessingSession, BaseSessionManager


class EmailProcessingSession(BaseProcessingSession):
    """
    Email processing session that tracks the entire workflow with structured logging.
    """

    def __init__(
        self, history_id: Optional[int], email_address: str, session_id: Optional[str] = None
    ):
        # Email-specific attributes (set before calling super().__init__)
        self.history_id = history_id
        self.email_address = email_address
        self.user_id: Optional[str] = None
        self.processed_messages_count = 0

        # Prepare session data for the base class
        session_data = {
            "history_id": history_id,
            "email_address": email_address,
        }

        # Initialize base class with email module name
        super().__init__(
            module_name="email", session_data=session_data, session_id=session_id
        )

    def _log_session_start(self):
        """Log the start of the email processing session."""
        self._log_with_session("INFO", "=" * 80)
        self._log_with_session("INFO", "EMAIL PROCESSING SESSION STARTED")
        self._log_with_session("INFO", "=" * 80)
        self._log_with_session("INFO", f"History ID: {self.history_id}")
        self._log_with_session("INFO", f"Email Address: {self.email_address}")
        self._log_with_session("INFO", f"Start Time: {self.start_time.isoformat()}")
        self._log_with_session("INFO", "-" * 80)

    def get_session_summary_data(self) -> Dict[str, Any]:
        """Get email-specific session summary data."""
        return {
            "User ID": self.user_id,
            "Email": self.email_address,
            "History ID": self.history_id,
            "Messages Processed": self.processed_messages_count,
        }

    def set_user_id(self, user_id: str):
        """Set the user ID once it's resolved."""
        self.user_id = user_id
        self._log_with_session("INFO", f"User ID resolved: {user_id}")

    def log_batch_processing(
        self, batch_number: int, batch_size: int, total_batches: int
    ):
        """Log batch processing information."""
        self._log_with_session(
            "INFO",
            f"Processing batch {batch_number}/{total_batches} ({batch_size} messages)",
        )

    def log_message_processing(self, message_id: str, subject: str, sender: str):
        """Log individual message processing."""
        self._log_with_session(
            "DEBUG",
            f"Processing message: {message_id}",
            {
                "subject": subject[:50] + "..." if len(subject) > 50 else subject,
                "sender": sender,
            },
        )

    def log_message_result(self, message_id: str, result: Dict[str, Any]):
        """Log the result of processing a message."""
        status = result.get("status", "unknown")
        if status == "error":
            self._log_with_session(
                "ERROR",
                f"Message {message_id} failed",
                {"error": result.get("error", "Unknown error")},
            )
        else:
            self._log_with_session(
                "DEBUG", f"Message {message_id} processed successfully"
            )

    def increment_processed_messages(self):
        """Increment the count of processed messages."""
        self.processed_messages_count += 1


class EmailSessionManager(BaseSessionManager):
    """
    Manages email processing sessions.
    """

    def __init__(self):
        super().__init__(EmailProcessingSession)

    def create_session(
        self, history_id: Optional[int], email_address: str
    ) -> EmailProcessingSession:
        """Create a new email processing session."""
        session = super().create_session(
            history_id=history_id, email_address=email_address
        )
        return session  # type: ignore


# Create a singleton instance for backward compatibility
_email_session_manager = EmailSessionManager()

# Expose the singleton methods as module-level functions for backward compatibility
create_session = _email_session_manager.create_session
get_session = _email_session_manager.get_session
end_session = _email_session_manager.end_session
get_active_sessions_count = _email_session_manager.get_active_sessions_count
