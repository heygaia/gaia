from typing import Callable, Dict
from langgraph.config import get_stream_writer
from composio.types import ToolExecuteParams

FRONTEND_BUILDERS: Dict[str, Callable[[ToolExecuteParams], dict]] = {}

def register_frontend_builder(tool: str):
    def decorator(func: Callable[[ToolExecuteParams], dict]):
        FRONTEND_BUILDERS[tool] = func
        return func
    return decorator


@register_frontend_builder("GMAIL_CREATE_EMAIL_DRAFT")
def gmail_builder(params: ToolExecuteParams):
    args = params.get("arguments", {})
    return {
        "email_compose_data": [
            {
                "to": [args.get("recipient_email")],
                "subject": args.get("subject"),
                "body": args.get("body"),
            }
        ]
    }


def frontend_stream_modifier(
    tool: str,
    toolkit: str,
    params: ToolExecuteParams,
) -> ToolExecuteParams:
    """
    Runs before a tool executes to stream custom payloads to the frontend.

    This modifier looks up a registered frontend builder for the given tool,
    generates the corresponding payload, and sends it through the stream writer.
    The payload can be used by the frontend to render custom UI components
    (e.g., email composer for Gmail, page preview for Notion, etc.).

    Returns the original params unchanged so execution can proceed normally.
    """
    builder = FRONTEND_BUILDERS.get(tool)
    if builder:
        payload = builder(params)
        writer = get_stream_writer()
        writer(payload)
    return params
