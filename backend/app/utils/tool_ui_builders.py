from typing import Callable, Dict, List, Optional, Union

from composio.types import ToolExecuteParams
from langgraph.config import get_stream_writer

FRONTEND_BUILDERS: Dict[str, Callable[[str, ToolExecuteParams], Optional[dict]]] = {}


def register_frontend_builder(tools: Union[str, List[str]]):
    def decorator(func: Callable[[str, ToolExecuteParams], Optional[dict]]):
        if isinstance(tools, str):
            FRONTEND_BUILDERS[tools] = func
        else:
            for tool in tools:
                FRONTEND_BUILDERS[tool] = func
        return func

    return decorator


@register_frontend_builder(
    [
        "GMAIL_CREATE_EMAIL_DRAFT",
        "GMAIL_FETCH_EMAILS",
        "GMAIL_FETCH_MESSAGE_BY_THREAD_ID",
    ]
)
def gmail_tools_builder(tool: str, params: ToolExecuteParams) -> Optional[dict]:
    args = params.get("arguments", {})
    print("fucking tool is called")

    if tool == "GMAIL_CREATE_EMAIL_DRAFT":
        return {
            "email_compose_data": [
                {
                    "to": [args.get("recipient_email")],
                    "subject": args.get("subject"),
                    "body": args.get("body"),
                }
            ]
        }

    elif tool == "GMAIL_FETCH_EMAILS":
        messages = args.get("messages", [])
        email_fetch_data = []
        for msg in messages:
            email_fetch_data.append(
                {
                    "from": msg.get("sender", msg.get("from")),
                    "subject": msg.get("subject"),
                    "time": msg.get("timestamp", msg.get("time")),
                    "thread_id": msg.get("thread_id"),
                }
            )
        return {"email_fetch_data": email_fetch_data}

    elif tool == "GMAIL_FETCH_MESSAGE_BY_THREAD_ID":
        thread_data = {
            "thread_id": args.get("thread_id", ""),
            "messages": args.get("messages", []),
        }
        return {"email_thread_data": thread_data}

    return None

def frontend_stream_modifier(
    tool: str,
    toolkit: str,
    params: ToolExecuteParams,
) -> ToolExecuteParams:
    """
    Runs before a tool executes to stream custom payloads to the frontend.
    Uses registered builders for clean, scalable tool handling.
    """
    builder = FRONTEND_BUILDERS.get(tool)
    if builder:
        payload = builder(tool, params)
        if payload:
            writer = get_stream_writer()
            writer(payload)

    return params
