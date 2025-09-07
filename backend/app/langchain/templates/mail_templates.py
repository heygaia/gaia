"""Templates for mail-related tool responses."""

import base64
import email
import email.message
import email.parser
import email.policy
from html import unescape
from typing import Any, Dict, List

from app.langchain.prompts.mail_prompts import (
    COMPOSE_EMAIL_SUMMARY,
    EMAIL_PROCESSING_PLANNER,
    EMAIL_PROCESSING_REPLANNER,
)
from bs4 import BeautifulSoup
from langchain_core.prompts import PromptTemplate

# ============================================================================
# GmailMessageParser - Class-based email parsing using email.parser
# ============================================================================

class GmailMessageParser:
    """
    A class to parse Gmail messages using Python's email library.
    Handles raw Gmail data and exposes clean methods for content extraction.
    """

    def __init__(self, gmail_message: dict):
        """
        Initialize parser with Gmail message data.

        Args:
            gmail_message (dict): Gmail API message object
        """
        self.gmail_message = gmail_message
        self.email_message = None
        self._parsed = False

    def parse(self) -> bool:
        """
        Parse the Gmail message using email.parser.

        Returns:
            bool: True if parsing succeeded, False otherwise
        """
        try:
            self.email_message = self._parse_with_email_parser()
            self._parsed = True
            return self.email_message is not None

        except Exception as e:
            print(f"GmailMessageParser failed: {e}")
            self._parsed = False
            return False

    def _parse_with_email_parser(self) -> email.message.EmailMessage | None:
        """Parse Gmail message using email.parser exclusively."""
        # Try raw email data first (most reliable)
        raw_data = self.gmail_message.get("raw")
        if raw_data:
            raw_email_bytes = base64.urlsafe_b64decode(raw_data)
            parser = email.parser.BytesParser(policy=email.policy.default)
            return parser.parsebytes(raw_email_bytes)

        # Fallback: reconstruct from payload
        payload = self.gmail_message.get("payload", {})
        if payload:
            raw_email_string = self._reconstruct_raw_email(payload)
            if raw_email_string:
                parser = email.parser.Parser(policy=email.policy.default)
                return parser.parsestr(raw_email_string)

        return None

    def _reconstruct_raw_email(self, payload: dict) -> str:
        """Reconstruct raw email from Gmail payload for email.parser."""
        lines = []

        # Headers
        headers = payload.get("headers", [])
        for header in headers:
            name = header.get("name", "")
            value = header.get("value", "")
            if name and value:
                lines.append(f"{name}: {value}")

        # Content-Type if missing
        mime_type = payload.get("mimeType", "text/plain")
        if not any(h.get("name", "").lower() == "content-type" for h in headers):
            lines.append(f"Content-Type: {mime_type}")

        # Separator
        lines.append("")

        # Body
        body = self._reconstruct_body(payload)
        if body:
            lines.append(body)

        return "\r\n".join(lines)

    def _reconstruct_body(self, payload: dict) -> str:
        """Reconstruct email body from payload."""
        mime_type = payload.get("mimeType", "")

        if mime_type.startswith("multipart/"):
            # Multipart message
            boundary = "----=_GmailParser_Boundary_12345"
            lines = [f'Content-Type: {mime_type}; boundary="{boundary}"\r\n']

            parts = payload.get("parts", [])
            for part in parts:
                lines.append(f"--{boundary}")
                part_content = self._reconstruct_raw_email(part)
                lines.append(part_content)

            lines.append(f"--{boundary}--")
            return "\r\n".join(lines)
        else:
            # Single part
            data = payload.get("body", {}).get("data", "")
            if data:
                try:
                    decoded_bytes = base64.urlsafe_b64decode(data)
                    return decoded_bytes.decode("utf-8", errors="ignore")
                except Exception:
                    return data
        return ""

    def _handle_composio_message(self):
        """Handle Composio message format."""
        content = self.gmail_message.get("message_text", "")
        # Create a simple email message for Composio data
        self.email_message = email.message.EmailMessage()
        if "<" in content and ">" in content:
            self.email_message.set_content("", subtype="html")
            self.email_message.set_payload(content)
        else:
            self.email_message.set_content(content)
        self._parsed = True

    # ========================================================================
    # Public getter methods
    # ========================================================================

    @property
    def subject(self) -> str:
        """Get email subject."""
        if not self._parsed or not self.email_message:
            return ""
        return self.email_message.get("Subject", "")

    @property
    def sender(self) -> str:
        """Get sender (From header)."""
        if not self._parsed or not self.email_message:
            return ""
        return self.email_message.get("From", "")

    @property
    def to(self) -> str:
        """Get recipients (To header)."""
        if not self._parsed or not self.email_message:
            return ""
        return self.email_message.get("To", "")

    @property
    def cc(self) -> str:
        """Get CC recipients."""
        if not self._parsed or not self.email_message:
            return ""
        return self.email_message.get("Cc", "")

    @property
    def date(self) -> str:
        """Get email date."""
        if not self._parsed or not self.email_message:
            return ""
        return self.email_message.get("Date", "")

    @property
    def text_content(self) -> str:
        """Get plain text content."""
        if not self._parsed or not self.email_message:
            return ""

        # Handle Composio messages
        if "message_text" in self.gmail_message:
            content = self.gmail_message.get("message_text", "")
            if "<" in content and ">" in content:
                return _get_text_from_html(content)
            return content

        # Use email.parser walk method
        for part in self.email_message.walk():
            if part.get_content_type() == "text/plain":
                try:
                    return part.get_content()
                except Exception:
                    payload = part.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        return payload.decode("utf-8", errors="ignore")
                    elif isinstance(payload, str):
                        return payload

        # If no text/plain, extract from HTML
        html = self.html_content
        if html:
            return _get_text_from_html(html)

        return ""

    @property
    def html_content(self) -> str:
        """Get HTML content."""
        if not self._parsed or not self.email_message:
            return ""

        # Handle Composio messages
        if "message_text" in self.gmail_message:
            content = self.gmail_message.get("message_text", "")
            if "<" in content and ">" in content:
                return content
            return ""

        # Use email.parser walk method
        for part in self.email_message.walk():
            if part.get_content_type() == "text/html":
                try:
                    return part.get_content()
                except Exception:
                    payload = part.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        return payload.decode("utf-8", errors="ignore")
                    elif isinstance(payload, str):
                        return payload

        return ""

    @property
    def content(self) -> dict:
        """Get both text and HTML content."""
        return {"text": self.text_content, "html": self.html_content}

    @property
    def attachments(self) -> List[dict]:
        """Get email attachments."""
        attachments = []

        if not self._parsed or not self.email_message:
            # Fallback to manual extraction for Gmail API
            parts = self.gmail_message.get("payload", {}).get("parts", [])
            for part in parts:
                if part.get("filename") and part.get("body", {}).get("attachmentId"):
                    attachments.append(
                        {
                            "filename": part.get("filename"),
                            "attachmentId": part.get("body", {}).get("attachmentId"),
                            "mimeType": part.get("mimeType"),
                            "size": part.get("body", {}).get("size"),
                            "messageId": self.gmail_message.get("id", ""),
                        }
                    )
            return attachments

        # Use email.parser for attachments
        for part in self.email_message.walk():
            if part.get_content_disposition() == "attachment":
                filename = part.get_filename()
                if filename:
                    attachments.append(
                        {
                            "filename": filename,
                            "mimeType": part.get_content_type(),
                            "size": len(part.get_payload(decode=True) or b""),
                            "messageId": self.gmail_message.get("id", ""),
                            "content": part.get_payload(decode=True),
                        }
                    )

        return attachments

    @property
    def labels(self) -> List[str]:
        """Get Gmail labels."""
        return self.gmail_message.get("labelIds", [])

    @property
    def is_read(self) -> bool:
        """Check if email is read."""
        return "UNREAD" not in self.labels

    @property
    def has_attachments(self) -> bool:
        """Check if email has attachments."""
        return len(self.attachments) > 0 or "HAS_ATTACHMENT" in self.labels


def _get_text_from_html(html_content):
    """Extract text from HTML content."""
    if not html_content:
        return ""

    soup = BeautifulSoup(unescape(html_content), "html.parser")
    return soup.get_text()


# Template for minimal message representation
def minimal_message_template(
    email_data: Dict[str, Any], short_body=True, include_both_formats=False
) -> Dict[str, Any]:
    """
    Convert a Gmail message to a minimal representation with only essential fields.

    Args:
        email_data: The full Gmail message data
        short_body: Whether to truncate body content to 100 characters
        include_both_formats: Whether to include both text and HTML content

    Returns:
        A dictionary with only the most essential email fields
    """
    # Use GmailMessageParser directly for efficiency
    parser = GmailMessageParser(email_data)
    parser.parse()

    content = parser.content if include_both_formats else None
    body_content = content["text"] if content else parser.text_content
    labels = parser.labels

    result = {
        "id": email_data.get("id", ""),
        "threadId": email_data.get("threadId", ""),
        "from": parser.sender,
        "to": parser.to,
        "subject": parser.subject,
        "snippet": email_data.get("snippet", ""),
        "time": parser.date,
        "isRead": "UNREAD" not in labels,
        "hasAttachment": "HAS_ATTACHMENT" in labels,
        "body": body_content[:100] if short_body else body_content,
        "labels": labels,
    }

    # Add content formats if requested
    if include_both_formats and content:
        result["content"] = {
            "text": content["text"],
            "html": content["html"],
        }

    return result


# Template for message details (when a single message needs more detail)
def detailed_message_template(email_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a Gmail message to a detailed but optimized representation including both text and HTML content.

    Args:
        email_data: The full Gmail message data

    Returns:
        A dictionary with the essential email fields plus body content in both formats
    """
    # Use GmailMessageParser directly for efficiency
    parser = GmailMessageParser(email_data)
    parser.parse()

    content = parser.content
    labels = parser.labels

    return {
        "id": email_data.get("id", ""),
        "threadId": email_data.get("threadId", ""),
        "from": parser.sender,
        "to": parser.to,
        "subject": parser.subject,
        "snippet": email_data.get("snippet", ""),
        "time": parser.date,
        "isRead": "UNREAD" not in labels,
        "hasAttachment": "HAS_ATTACHMENT" in labels,
        "body": content["text"],  # Plain text for backward compatibility
        "labels": labels,
        "content": {"text": content["text"], "html": content["html"]},
        "cc": parser.cc,
    }


# Template for thread information
def thread_template(thread_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a Gmail thread to a minimal representation.

    Args:
        thread_data: The full Gmail thread data

    Returns:
        A dictionary with thread ID and minimized messages
    """
    return {
        "id": thread_data.get("id", ""),
        "messages": [
            minimal_message_template(msg, short_body=False, include_both_formats=True)
            for msg in thread_data.get("messages", [])
        ],
        "messageCount": len(thread_data.get("messages", [])),
        "instructions": """
        Understand the **actual email body content** and summarize it intelligently using the following framework.

        Your job is to extract meaning from the email — do not repeat sender, subject, or metadata that is already visible to the user.

        🎯 Focus on summarizing the **actual email message**, not the headers.

        Use this analysis framework to guide your summary:

        ✓ Urgent Action Required:
        - Highlight time-sensitive tasks, deadlines, or urgent requests

        ✓ Key Issues Identified:
        - Summarize problems, blockers, concerns, or recurring issues

        ✓ Required Actions:
        - Extract any tasks, decisions, or next steps
        - Mention who's responsible if it's clear

        ✓ Timeline:
        - Pull out any mentioned deadlines, meetings, or delays

        ✓ Current Status:
        - Describe progress, decisions made, or what's still pending

        📌 Be concise. Avoid copy-pasting text or restating obvious content.
        📌 If none of the framework categories apply, simply summarize the email’s **core message or intent**.
        📌 Never repeat information the user already sees (like sender name or subject).
        📌 The goal is to help the user quickly understand **what the email is actually saying or asking**, in plain, helpful language.
        """,
    }


# Template for draft information
def draft_template(draft_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a Gmail draft to a minimal representation including both text and HTML content.

    Args:
        draft_data: The full Gmail draft data

    Returns:
        A dictionary with the essential draft fields including text and HTML content
    """
    message = draft_data.get("message", {})

    # Use GmailMessageParser directly for efficiency
    parser = GmailMessageParser(message)
    parser.parse()

    content = parser.content

    return {
        "id": draft_data.get("id", ""),
        "message": {
            "to": parser.to,
            "subject": parser.subject,
            "snippet": message.get("snippet", ""),
            "body": content["text"],  # Plain text for backward compatibility
            "content": {"text": content["text"], "html": content["html"]},
        },
    }


# Process tool responses
def process_list_messages_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """Process the response from list_gmail_messages tool to minimize data."""
    processed_response = {
        "nextPageToken": response.get("nextPageToken"),
        "resultSize": len(response.get("messages", [])),
    }

    if "messages" in response:
        processed_response["messages"] = [
            minimal_message_template(msg) for msg in response.get("messages", [])
        ]

    if "error" in response:
        processed_response["error"] = response["error"]

    return processed_response



def process_list_drafts_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """Process the response from list_email_drafts tool to minimize data."""
    processed_response = {
        "nextPageToken": response.get("nextPageToken"),
        "resultSize": len(response.get("drafts", [])),
    }

    if "drafts" in response:
        processed_response["drafts"] = [
            draft_template(draft) for draft in response.get("drafts", [])
        ]

    if "error" in response:
        processed_response["error"] = response["error"]

    return processed_response


def process_get_thread_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """Process the response from get_email_thread tool to minimize data."""
    return thread_template(response)


# Compose email template
COMPOSE_EMAIL_TEMPLATE = PromptTemplate(
    input_variables=["subject", "body"],
    template=COMPOSE_EMAIL_SUMMARY,
)

# Email processing plan template
EMAIL_PROCESSING_PLAN_TEMPLATE = PromptTemplate(
    input_variables=["messages", "format_instructions"],
    template=EMAIL_PROCESSING_PLANNER,
)

# Email processing replan template
EMAIL_PROCESSING_REPLAN_TEMPLATE = PromptTemplate(
    input_variables=["input", "plan", "past_steps", "format_instructions"],
    template=EMAIL_PROCESSING_REPLANNER,
)

MAIL_RECEIVED_USER_MESSAGE_TEMPLATE = PromptTemplate(
    input_variables=["sender", "subject", "snippet"],
    template="""📩 New Email Received
From: {sender}
Subject: {subject}

📬 Content:
{snippet}
""",
)
