import asyncio
from typing import Optional

from app.config.loggers import app_logger as logger
from app.config.oauth_config import get_composio_social_configs
from app.config.settings import settings
from app.models.oauth_models import TriggerConfig
from app.services.langchain_composio_service import LangchainProvider
from app.utils.query_utils import add_query_param
from app.utils.tool_ui_builders import frontend_stream_modifier
from composio import Composio, before_execute
from composio.types import ToolExecuteParams

# Generate COMPOSIO_SOCIAL_CONFIGS dynamically from oauth_config
COMPOSIO_SOCIAL_CONFIGS = get_composio_social_configs()


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

    def connect_account(
        self, provider: str, user_id: str, frontend_redirect_path: Optional[str] = None
    ) -> dict:
        """
        Initiates connection flow for a given provider and user.
        """
        if provider not in COMPOSIO_SOCIAL_CONFIGS:
            raise ValueError(f"Provider '{provider}' not supported")

        config = COMPOSIO_SOCIAL_CONFIGS[provider]

        try:
            callback_url = (
                add_query_param(
                    settings.COMPOSIO_REDIRECT_URI,
                    "frontend_redirect_path",
                    frontend_redirect_path,
                )
                if frontend_redirect_path
                else settings.COMPOSIO_REDIRECT_URI
            )

            connection_request = self.composio.connected_accounts.initiate(
                user_id=user_id,
                auth_config_id=config.auth_config_id,
                callback_url=callback_url,
            )

            return {
                "status": "pending",
                "redirect_url": connection_request.redirect_url,
                "connection_id": connection_request.id,
            }
        except Exception as e:
            logger.error(f"Error connecting {provider} for {user_id}: {e}")
            raise

    def get_tools(self, tool_kit: str, exclude_tools: Optional[list[str]] = None):
        tools = self.composio.tools.get(
            user_id="",
            toolkits=[tool_kit],
        )
        exclude_tools = exclude_tools or []
        tools_name = [tool.name for tool in tools if tool.name not in exclude_tools]
        user_id_modifier = before_execute(tools=tools_name)(extract_user_id_from_params)
        after_modifier = before_execute(tools=tools_name)(frontend_stream_modifier)

        return self.composio.tools.get(
            user_id="",
            toolkits=[tool_kit],
            modifiers=[after_modifier, user_id_modifier],
        )

    def check_connection_status(
        self, providers: list[str], user_id: str
    ) -> dict[str, bool]:
        """
        Check if a user has active connections for given providers.
        Returns a dictionary mapping provider names to connection status.
        """
        result = {}
        required_auth_config_ids = []

        # Initialize all providers as disconnected
        for provider in providers:
            result[provider] = False
            if provider in COMPOSIO_SOCIAL_CONFIGS:
                required_auth_config_ids.append(
                    COMPOSIO_SOCIAL_CONFIGS[provider].auth_config_id
                )

        try:
            # Get all connected accounts for the user
            user_accounts = self.composio.connected_accounts.list(
                user_ids=[user_id],
                auth_config_ids=required_auth_config_ids,
                limit=len(required_auth_config_ids),
            )

            # Create a mapping of auth_config_ids to check
            auth_config_provider_map = {}
            for provider in providers:
                if provider in COMPOSIO_SOCIAL_CONFIGS:
                    auth_config_id = COMPOSIO_SOCIAL_CONFIGS[provider].auth_config_id
                    auth_config_provider_map[auth_config_id] = provider

            # Check each account against our providers
            for account in user_accounts.items:
                # Only check active accounts
                if not account.auth_config.is_disabled and account.status == "ACTIVE":
                    account_auth_config_id = account.auth_config.id

                    result[auth_config_provider_map[account_auth_config_id]] = True

            return result

        except Exception as e:
            logger.error(
                f"Error checking connection status for providers {providers} and user {user_id}: {e}"
            )
            return result

    def get_connected_account_by_id(self, connected_account_id: str):
        """
        Retrieve a connected account by its ID.
        """
        try:
            connected_account = self.composio.connected_accounts.get(
                nanoid=connected_account_id,
            )

            return connected_account
        except Exception as e:
            logger.error(
                f"Error retrieving connected account {connected_account_id}: {e}"
            )
            return None

    async def handle_subscribe_trigger(
        self, user_id: str, triggers: list[TriggerConfig]
    ):
        """
        Handle the subscription trigger for a specific provider.
        """
        print(f"Subscribing triggers for user {user_id}: {triggers}")
        try:
            # Create tasks for each trigger to run them concurrently
            def create_trigger(trigger: TriggerConfig):
                return self.composio.triggers.create(
                    user_id=user_id,
                    slug=trigger.slug,
                    trigger_config=trigger.config,
                )

            tasks = [
                asyncio.get_event_loop().run_in_executor(None, create_trigger, trigger)
                for trigger in triggers
            ]

            # Execute all trigger creation tasks concurrently
            return await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Error handling subscribe trigger for {user_id}: {e}")


composio_service = ComposioService()
