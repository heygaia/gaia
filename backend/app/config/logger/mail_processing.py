"""
Email processing session logger using Loguru.
Provides structured session-based logging with file rotation and auto-retention.
"""

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger

# Global Loguru setup (should be done once at app startup)
LOG_DIR = Path("logs/email_sessions")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logger.add(
    LOG_DIR / "email_processing.log",
    rotation="10 MB",
    retention="15 days",
    compression="zip",
    enqueue=True,  # For thread/process safety
    backtrace=True,
    diagnose=True,
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | [SESSION:{extra[session_id]}] | {message}",
)


class EmailProcessingSession:
    def __init__(
        self, history_id: int, email_address: str, session_id: Optional[str] = None
    ):
        self.history_id = history_id
        self.email_address = email_address
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self.user_id: Optional[str] = None
        self.processed_messages_count = 0
        self.start_time = datetime.now(timezone.utc)

        self._logger = logger.bind(session_id=self.session_id)
        self._log_session_start()

    def _log(self, level: str, message: str, **kwargs):
        log_method = getattr(self._logger, level.lower())
        if kwargs:
            message += " | " + ", ".join(f"{k}={v}" for k, v in kwargs.items())
        log_method(message)

    def _log_session_start(self):
        self._log("info", "=" * 80)
        self._log("info", "EMAIL PROCESSING SESSION STARTED")
        self._log("info", "=" * 80)
        self._log("info", f"History ID: {self.history_id}")
        self._log("info", f"Email Address: {self.email_address}")
        self._log("info", f"Start Time: {self.start_time.isoformat()}")
        self._log("info", "-" * 80)

    def set_user_id(self, user_id: str):
        self.user_id = user_id
        self._log("info", "User ID resolved", user_id=user_id)

    def log_batch_processing(
        self, batch_number: int, batch_size: int, total_batches: int
    ):
        self._log(
            "info",
            f"Processing batch {batch_number}/{total_batches} ({batch_size} messages)",
        )

    def log_message_processing(self, message_id: str, subject: str, sender: str):
        short_subject = subject[:50] + "..." if len(subject) > 50 else subject
        self._log(
            "debug",
            f"Processing message: {message_id}",
            subject=short_subject,
            sender=sender,
        )

    def log_message_result(self, message_id: str, result: Dict[str, Any]):
        status = result.get("status", "unknown")
        if status == "error":
            self._log(
                "error",
                f"Message {message_id} failed",
                error=result.get("error", "Unknown error"),
            )
        else:
            self._log("debug", f"Message {message_id} processed successfully")

    def increment_processed_messages(self):
        self.processed_messages_count += 1

    def log_session_summary(self, final_result: Dict[str, Any]):
        end_time = datetime.now(timezone.utc)
        duration = (end_time - self.start_time).total_seconds()

        self._log("info", "-" * 80)
        self._log("info", "SESSION SUMMARY")
        self._log("info", "-" * 80)
        self._log("info", f"Session ID: {self.session_id}")
        self._log("info", f"Duration: {duration:.2f} seconds")
        self._log("info", f"Final Status: {final_result.get('status', 'unknown')}")
        self._log("info", f"Email Address: {self.email_address}")
        self._log("info", f"User ID: {self.user_id}")
        self._log("info", f"History ID: {self.history_id}")
        self._log("info", f"Messages Processed: {self.processed_messages_count}")
        self._log("info", "=" * 80)
        self._log("info", "EMAIL PROCESSING SESSION COMPLETED")
        self._log("info", "=" * 80)

    def log_milestone(self, milestone: str, details: Optional[Dict[str, Any]] = None):
        """Log a major milestone in the email processing session."""
        self._log("info", f"MILESTONE: {milestone}", **(details or {}))

    def log_error(
        self,
        error_type: str,
        error_message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Log an error with context."""
        self._log("error", f"ERROR: {error_type} - {error_message}", **(details or {}))


class EmailSessionManager:
    def __init__(self):
        self._active_sessions: Dict[str, EmailProcessingSession] = {}

    def create_session(
        self, history_id: int, email_address: str
    ) -> EmailProcessingSession:
        session = EmailProcessingSession(history_id, email_address)
        self._active_sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[EmailProcessingSession]:
        return self._active_sessions.get(session_id)

    def end_session(self, session_id: str):
        self._active_sessions.pop(session_id, None)

    def get_active_sessions_count(self) -> int:
        return len(self._active_sessions)


# Singleton instance
_email_session_manager = EmailSessionManager()
create_session = _email_session_manager.create_session
get_session = _email_session_manager.get_session
end_session = _email_session_manager.end_session
get_active_sessions_count = _email_session_manager.get_active_sessions_count
