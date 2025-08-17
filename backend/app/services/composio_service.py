from app.config.loggers import app_logger as logger
from app.config.settings import settings
from app.services.langchain_composio_service import LangchainProvider
from composio import Composio, before_execute
from composio.types import ToolExecuteParams

SOCIAL_CONFIGS = {
    "notion": {"auth_config_id": "ac_9Yho1TxOcxHh", "toolkit": "NOTION"},
    "twitter": {"auth_config_id": "ac_o66V1UO0-GI2", "toolkit": "TWITTER"},
    "google_sheets": {"auth_config_id": "ac_r5-Q6qJ4U8Qk", "toolkit": "GOOGLE_SHEETS"},
    "linkedin": {"auth_config_id": "ac_X0iHigf4UZ2c", "toolkit": "LINKEDIN"},
}

def extract_user_id_from_params(
    tool: str,
    toolkit: str,
    params: ToolExecuteParams,
) -> ToolExecuteParams:
    """
    Extract user_id from RunnableConfig metadata and add it to tool execution params.

    This function is used as a before_execute modifier for Composio tools to ensure
    user context is properly passed through during tool execution.
    """
    arguments = params.get("arguments", {})
    if not arguments:
        return params

    config = arguments.pop("__runnable_config__", None)
    if config is None:
        return params

    metadata = config.get("metadata", {}) if isinstance(config, dict) else {}
    if not metadata:
        return params

    user_id = metadata.get("user_id")
    if user_id is None:
        return params

    params["user_id"] = user_id
    return params


class ComposioService:
    def __init__(self):
        self.composio = Composio(
            provider=LangchainProvider(), api_key=settings.COMPOSIO_KEY
        )

    def connect_account(self, provider: str, user_id: str):
        """
        Initiates connection flow for a given provider and user.
        """
        if provider not in SOCIAL_CONFIGS:
            raise ValueError(f"Provider '{provider}' not supported")

        config = SOCIAL_CONFIGS[provider]

        try:
            connection_request = self.composio.connected_accounts.initiate(
                user_id=user_id, auth_config_id=config["auth_config_id"]
            )

            return {
                "status": "pending",
                "redirect_url": connection_request.redirect_url,
                "connection_id": connection_request.id,
            }
        except Exception as e:
            logger.error(f"Error connecting {provider} for {user_id}: {e}")
            raise

    def get_tools(self, tool_kit: str):
        tools = self.composio.tools.get(
            user_id="",
            toolkits=[tool_kit],
        )
        tools_name = [tool.name for tool in tools]

        # Applying the before_execute decorator dynamically
        user_id_modifier = before_execute(tools=tools_name)(extract_user_id_from_params)

        return self.composio.tools.get(
            user_id="",
            toolkits=[tool_kit],
            modifiers=[user_id_modifier],
        )


composio_service = ComposioService()
