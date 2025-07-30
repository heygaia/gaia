"""Templates for mail-related tool responses."""

from typing import Any, Dict

from app.langchain.prompts.mail_prompts import (
    COMPOSE_EMAIL_SUMMARY,
    EMAIL_PROCESSING_PLANNER,
    EMAIL_PROCESSING_REPLANNER,
)
from langchain_core.prompts import PromptTemplate


# Template for minimal message representation
def minimal_message_template(email_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a Gmail message to a minimal representation with only essential fields.

    Args:
        email_data: The full Gmail message data

    Returns:
        A dictionary with only the most essential email fields
    """
    return {
        "id": email_data.get("id", ""),
        "threadId": email_data.get("threadId", ""),
        "from": email_data.get("from", ""),
        "to": email_data.get("to", ""),
        "subject": email_data.get("subject", ""),
        "snippet": email_data.get("snippet", ""),
        "time": email_data.get("time", ""),
        "isRead": "UNREAD" not in email_data.get("labelIds", []),
        "hasAttachment": "HAS_ATTACHMENT" in email_data.get("labelIds", []),
        "body": email_data.get("body", ""),
        "labels": email_data.get("labelIds", []),
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
    minimal_data = minimal_message_template(email_data)
    return {
        **minimal_data,
        "body": email_data.get("body", ""),
        "cc": email_data.get("cc", ""),
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
            minimal_message_template(msg) for msg in thread_data.get("messages", [])
        ],
        "messageCount": len(thread_data.get("messages", [])),
        "instructions": """

        Understand the mail and output your response based on the following analysis Framework:
        When fetching and analyzing email threads, always include:

        ✓ Urgent Action Required:
        - Identify any time-sensitive items that need immediate attention
        - Flag deadlines, urgent requests, or critical decisions needed
        - Highlight any escalations or priority communications

        ✓ Key Issues Identified:
        - Extract main problems, concerns, or challenges discussed
        - Identify blockers, conflicts, or unresolved matters
        - Note any recurring issues or patterns in the conversation

        ✓ Required Actions:
        - List specific tasks, deliverables, or next steps mentioned
        - Identify who is responsible for each action item
        - Extract any commitments, agreements, or promises made

        ✓ Timeline:
        - Extract all dates, deadlines, and time-sensitive milestones
        - Identify project phases, meeting schedules, or delivery dates
        - Note any timeline changes or delays discussed

        ✓ Current Status:
        - Summarize the current state of projects or discussions
        - Identify what has been completed vs. what remains pending
        - Note any status updates, progress reports, or milestone achievements

        Do not include them if they're not specified in the email, it's fine. Summarise the body and the information instead of showing the details manually, ensure its concise and easy to understand.
        don't just copy paste the details of the mail. Do not provide unnecessary information to the user about the mail that they cannot discertain certain information from
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
            "to": message.get("to", ""),
            "subject": message.get("subject", ""),
            "snippet": message.get("snippet", ""),
            "body": message.get("body", ""),
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
