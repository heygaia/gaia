from fastapi import APIRouter, Depends
from composio import Composio
from openai import OpenAI
from app.config.settings import settings
from app.api.v1.dependencies.oauth_dependencies import get_current_user

router = APIRouter()

NOTION_AUTH_CONFIG_ID = "ac_r5-Q6qJ4U8Qk"


@router.post("/notion/connect")
async def connect_notion_account(user: dict = Depends(get_current_user)):
    """
    Initiates Notion OAuth connection for the current user via Composio.
    Returns a redirect URL for the user to authenticate.
    """
    try:
        composio_client = Composio(api_key="")
        connection_request = composio_client.connected_accounts.initiate(
            user_id=user["user_id"],
            auth_config_id=NOTION_AUTH_CONFIG_ID,
        )

        return {
            "status": "pending",
            "redirect_url": connection_request.redirect_url,
            "connection_id": connection_request.id
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/notion/page/create")
async def create_notion_page(user: dict = Depends(get_current_user)):
    """
    Creates a Notion page using Composio and OpenAI tool execution.
    Assumes the user's Notion account is already connected.
    """
    try:
        openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        composio_client = Composio(api_key="ak_WdZt4cbr16csoSZJ2IiH")

        tools = composio_client.tools.get(
            user_id=user["user_id"],
            toolkits=["NOTION"]
        )

        completion = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a tool-using assistant. "
                        "When creating a Notion page, always use the given parent_id exactly."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        "Create a Notion page titled 'this is peace of dog shit' "
                        "inside the parent page with ID dd58626e-ba3b-487f-8e1d-21fc48d15063."
                    )
                }
            ],
            tools=tools
        )
        result = composio_client.provider.handle_tool_calls(
            user_id=user["user_id"],
            response=completion
        )

        return {"status": "success", "result": result}

    except Exception as e:
        return {"status": "error", "message": str(e)}
