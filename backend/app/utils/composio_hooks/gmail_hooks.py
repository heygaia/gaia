"""
Gmail-specific hooks using the enhanced decorator system.

These hooks demonstrate the power of the new multi-tool/toolkit decorators
with conditional logic based on tool names.
"""

from typing import Any

from app.config.loggers import app_logger as logger
from app.langchain.templates.mail_templates import (
    detailed_message_template,
    minimal_message_template,
    thread_template,
)
from langgraph.config import get_stream_writer

from .registry import register_after_hook, register_before_hook


# @register_after_hook(
#     tools=["GMAIL_FETCH_EMAILS", "GMAIL_LIST_THREADS", "GMAIL_SEND_EMAIL"]
# )
# def gmail_output_processor(tool: str, toolkit: str, response: Any) -> Any:
#     """
#     Universal Gmail output processor that handles multiple Gmail tools.
#     Uses conditional logic based on tool name for specific processing.
#     """
#     if not response or not isinstance(response, dict):
#         return response

#     try:
#         # Handle GMAIL_FETCH_EMAILS
#         if tool == "GMAIL_FETCH_EMAILS":
#             emails_data = response.get("data", [])
#             if not emails_data:
#                 return response

#             # Check if we should use minimal or detailed template
#             use_minimal = len(emails_data) > 5

#             processed_emails = []
#             for email in emails_data:
#                 if use_minimal:
#                     processed_email = minimal_message_template(email)
#                 else:
#                     processed_email = detailed_message_template(email)
#                 processed_emails.append(processed_email)

#             # Create processed response
#             processed_response = {
#                 **response,
#                 "data": processed_emails,
#                 "processed": True,
#                 "template_used": "minimal" if use_minimal else "detailed",
#             }

#             logger.debug(
#                 f"Processed {len(processed_emails)} Gmail emails with {processed_response['template_used']} template"
#             )
#             return processed_response

#         # Handle GMAIL_LIST_THREADS
#         elif tool == "GMAIL_LIST_THREADS":
#             threads_data = response.get("data", [])
#             if not threads_data:
#                 return response

#             processed_threads = []
#             for thread in threads_data:
#                 processed_thread = thread_template(thread)
#                 processed_threads.append(processed_thread)

#             # Create processed response
#             processed_response = {
#                 **response,
#                 "data": processed_threads,
#                 "processed": True,
#                 "template_used": "thread_list",
#             }

#             logger.debug(f"Processed {len(processed_threads)} Gmail threads")
#             return processed_response

#         # Handle GMAIL_SEND_EMAIL
#         elif tool == "GMAIL_SEND_EMAIL":
#             # Check if email was sent successfully
#             if response.get("success", False) or "message_id" in response.get(
#                 "data", {}
#             ):
#                 user_message = "Email sent successfully!"
#                 status = "sent"
#             else:
#                 user_message = "Failed to send email"
#                 status = "failed"

#             # Add timestamp if not present
#             timestamp = response.get("timestamp")
#             if not timestamp:
#                 from datetime import datetime

#                 timestamp = datetime.now().isoformat()

#             # Create processed response
#             processed_response = {
#                 **response,
#                 "user_message": user_message,
#                 "status": status,
#                 "timestamp": timestamp,
#             }

#             logger.debug(
#                 f"Processed Gmail send output: {processed_response.get('status', 'unknown')}"
#             )
#             return processed_response

#     except Exception as e:
#         logger.error(f"Error processing Gmail {tool} output: {e}")
#         return response
#     return response

@register_before_hook(
    tools=["GMAIL_SEND_EMAIL", "GMAIL_CREATE_EMAIL_DRAFT"]
)
def gmail_compose_hook(tool: str, toolkit: str, response: Any):
    payload = None
    response = response.get("arguments", {})
    if tool == "GMAIL_CREATE_EMAIL_DRAFT":
        payload = {
            "email_compose_data": [
                {
                    "to": [response.get("recipient_email")],
                    "subject": response.get("subject"),
                    "body": response.get("body"),
                }
            ]
        }
    if payload:
        writer = get_stream_writer()
        writer(payload)
    return response


@register_after_hook(tools=["GMAIL_FETCH_EMAILS"])
def gmail_fetch_hook(tool: str, toolkit: str, response: Any):
    print("this is fetch email tool response but after",response)

    