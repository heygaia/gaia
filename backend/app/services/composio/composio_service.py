import asyncio
import time
from typing import Optional

from app.config.loggers import langchain_logger as logger
from app.config.oauth_config import get_composio_social_configs
from app.config.settings import settings
from app.core.lazy_loader import MissingKeyStrategy, lazy_provider, providers
from app.decorators.caching import Cacheable, CacheInvalidator
from app.models.oauth_models import TriggerConfig
from app.services.composio.langchain_composio_service import LangchainProvider
from app.utils.composio_hooks.composio_hooks import (
    master_after_execute_hook,
    master_before_execute_hook,
)
from app.utils.query_utils import add_query_param
from composio import Composio, after_execute, before_execute

COMPOSIO_SOCIAL_CONFIGS = get_composio_social_configs()


class ComposioService:
    def __init__(self, api_key: str):
        self.composio = Composio(provider=LangchainProvider(), api_key=api_key)

    @CacheInvalidator(
        key_patterns=[
            "composio:connection_status:{user_id}",
        ]
    )
    async def connect_account(
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

            # Run the synchronous Composio call in a thread pool
            loop = asyncio.get_event_loop()
            connection_request = await loop.run_in_executor(
                None,
                lambda: self.composio.connected_accounts.initiate(
                    user_id=user_id,
                    auth_config_id=config.auth_config_id,
                    callback_url=callback_url,
                ),
            )

            return {
                "status": "pending",
                "redirect_url": connection_request.redirect_url,
                "connection_id": connection_request.id,
            }
        except Exception as e:
            logger.error(f"Error connecting {provider} for {user_id}: {e}")
            raise

    async def get_tools(self, tool_kit: str, exclude_tools: Optional[list[str]] = None):
        """
        Get tools for a specific toolkit with unified master hooks.

        The master hooks handle ALL tools automatically including:
        - User ID extraction from RunnableConfig metadata
        - Frontend streaming setup
        - All registered tool-specific hooks (Gmail, etc.)
        """
        logger.info(f"Loading {tool_kit} toolkit...")
        start_time = time.time()

        # Run the first tools.get() call asynchronously
        tools = await asyncio.to_thread(
            self.composio.tools.get, user_id="", toolkits=[tool_kit], limit=100
        )

        exclude_tools = exclude_tools or []
        tools_name = [tool.name for tool in tools if tool.name not in exclude_tools]

        master_before_modifier = before_execute(tools=tools_name)(
            master_before_execute_hook
        )
        master_after_modifier = after_execute(tools=tools_name)(
            master_after_execute_hook
        )

        # Run the second tools.get() call asynchronously
        result = await asyncio.to_thread(
            self.composio.tools.get,
            user_id="",
            toolkits=[tool_kit],
            modifiers=[master_before_modifier, master_after_modifier],
            limit=1000,
        )

        tools_time = time.time() - start_time
        logger.info(
            f"{tool_kit} toolkit loaded: {len(result)} tools in {tools_time:.3f}s"
        )
        return result

    def get_tool(
        self,
        tool_name: str,
        use_before_hook: bool = True,
        use_after_hook: bool = True,
        user_id: str = "",
    ):
        """
        Get a specific tool by name with configurable hooks.

        Args:
            tool_name: Name of the specific tool to retrieve (e.g., 'GMAIL_SEND_EMAIL')
            use_before_hook: Whether to apply master before execute hook
            use_after_hook: Whether to apply master after execute hook

        Returns:
            The specific tool with selected hooks applied, or None if not found
        """
        try:
            modifiers = []

            # Add hooks based on flags
            if use_before_hook:
                master_before_modifier = before_execute(tools=[tool_name])(
                    master_before_execute_hook
                )
                modifiers.append(master_before_modifier)

            if use_after_hook:
                master_after_modifier = after_execute(tools=[tool_name])(
                    master_after_execute_hook
                )
                modifiers.append(master_after_modifier)

            tools = self.composio.tools.get(
                user_id=user_id,
                tools=[tool_name],
                modifiers=modifiers,
            )

            return tools[0] if tools else None
        except Exception as e:
            logger.error(f"Error getting tool {tool_name}: {e}")
            return None

    @Cacheable(
        key_pattern="composio:connection_status:{user_id}",
        ttl=300,  # 5 minutes
        serializer=lambda result: result,
        deserializer=lambda result: result,
    )
    async def check_connection_status(
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
            # Get all connected accounts for the user (run in thread pool)
            loop = asyncio.get_event_loop()
            user_accounts = await loop.run_in_executor(
                None,
                lambda: self.composio.connected_accounts.list(
                    user_ids=[user_id],
                    auth_config_ids=required_auth_config_ids,
                    limit=len(required_auth_config_ids),
                ),
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
                    if account_auth_config_id in auth_config_provider_map:
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
        logger.info(f"Subscribing triggers for user {user_id}: {triggers}")
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


@lazy_provider(
    name="composio_service",
    required_keys=[settings.COMPOSIO_KEY],
    strategy=MissingKeyStrategy.WARN,
    auto_initialize=False,
)
def init_composio_service():
    # This condition is just for type checking purposes and will never be false at runtime
    # because of the required_keys in the lazy_provider decorator
    if settings.COMPOSIO_KEY is None:
        raise RuntimeError("COMPOSIO_KEY is not set in settings")

    return ComposioService(settings.COMPOSIO_KEY)


def get_composio_service():
    service = providers.get("composio_service")
    if service is None:
        raise RuntimeError("ComposioService is not available")
    return service
