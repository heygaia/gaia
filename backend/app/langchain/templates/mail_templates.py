"""Templates for mail-related tool responses."""

import base64
from html import unescape
from typing import Any, Dict

from app.langchain.prompts.mail_prompts import (
    COMPOSE_EMAIL_SUMMARY,
    EMAIL_PROCESSING_PLANNER,
    EMAIL_PROCESSING_REPLANNER,
)
from bs4 import BeautifulSoup
from langchain_core.prompts import PromptTemplate

# ============================================================================
# Email Extraction Utilities (copied from process_email.py)
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


def extract_recipients(message: dict) -> str:
    """
    Extracts the recipient's email address from a Gmail message.
    Args:
        message (dict): The Gmail message object.
    Returns:
        str: The recipient's email address.
    """
    headers = message.get("payload", {}).get("headers", [])
    for header in headers:
        if header.get("name") == "To":
            return header.get("value", "")
    return ""


def extract_cc(message: dict) -> str:
    """
    Extracts the CC email addresses from a Gmail message.
    Args:
        message (dict): The Gmail message object.
    Returns:
        str: The CC email addresses.
    """
    headers = message.get("payload", {}).get("headers", [])
    for header in headers:
        if header.get("name") == "Cc":
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
                    "filename": part.get("filename"),
                    "attachmentId": part.get("body", {}).get("attachmentId"),
                    "mimeType": part.get("mimeType"),
                    "size": part.get("body", {}).get("size"),
                    "messageId": message.get("id", ""),
                }
            )

    return attachments


# ============================================================================
# Template Functions (updated to use extraction functions)
# ============================================================================


# Template for minimal message representation
def minimal_message_template(
    email_data: Dict[str, Any], short_body=True
) -> Dict[str, Any]:
    """
    Convert a Gmail message to a minimal representation with only essential fields.

    Args:
        email_data: The full Gmail message data

    Returns:
        A dictionary with only the most essential email fields
    """
    body_content = extract_string_content(email_data)
    labels = extract_labels(email_data)

    return {
        "id": email_data.get("id", ""),
        "threadId": email_data.get("threadId", ""),
        "from": extract_sender(email_data),
        "to": extract_recipients(email_data),
        "subject": extract_subject(email_data),
        "snippet": email_data.get("snippet", ""),
        "time": extract_date(email_data),
        "isRead": "UNREAD" not in labels,
        "hasAttachment": "HAS_ATTACHMENT" in labels,
        "body": body_content[:100] if short_body else body_content,
        "labels": labels,
    }


# Template for message details (when a single message needs more detail)
def detailed_message_template(email_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a Gmail message to a detailed but optimized representation.

    Args:
        email_data: The full Gmail message data

    Returns:
        A dictionary with the essential email fields plus body content
    """
    minimal_data = minimal_message_template(email_data, short_body=False)
    return {
        **minimal_data,
        "body": extract_string_content(email_data),
        "cc": extract_cc(email_data),
    }


# Template for label information
def label_template(label_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a Gmail label to a minimal representation.

    Args:
        label_data: The full Gmail label data

    Returns:
        A dictionary with only the essential label fields
    """
    return {
        "id": label_data.get("id", ""),
        "name": label_data.get("name", ""),
        "type": label_data.get("type", "user"),
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
            minimal_message_template(msg, short_body=False)
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
    Convert a Gmail draft to a minimal representation.

    Args:
        draft_data: The full Gmail draft data

    Returns:
        A dictionary with only the essential draft fields
    """
    message = draft_data.get("message", {})
    return {
        "id": draft_data.get("id", ""),
        "message": {
            "to": extract_recipients(message),
            "subject": extract_subject(message),
            "snippet": message.get("snippet", ""),
            "body": extract_string_content(message),
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


def process_search_messages_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """Process the response from search_gmail_messages tool to minimize data."""
    return process_list_messages_response(response)


def process_list_labels_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """Process the response from list_gmail_labels tool to minimize data."""
    processed_response: Dict[str, Any] = {}

    if "labels" in response:
        processed_response["labels"] = [
            label_template(label) for label in response.get("labels", [])
        ]
        processed_response["labelCount"] = str(len(processed_response["labels"]))

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
