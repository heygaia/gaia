"""Which integrations a user has connected, read once and cached.

Below ``oauth_service`` on purpose: the workflow layer asks this question
(``integration_requirements``) and ``oauth_service`` imports the workflow
layer for pause/resume, so the reader lives where both can import it.
"""

from __future__ import annotations

from app.config.oauth_config import OAUTH_INTEGRATIONS, get_integration_scopes
from app.config.token_repository import token_repository
from app.constants.cache import OAUTH_STATUS_KEY
from app.constants.integrations import (
    INTEGRATION_STATUS_CONNECTED,
    MANAGED_BY_COMPOSIO,
    MANAGED_BY_MCP,
    MANAGED_BY_SELF,
)
from app.constants.log_tags import LogTag
from app.db.repositories.user_integrations import user_integration_repository
from app.decorators.caching import Cacheable
from app.services.composio.composio_service import get_composio_service
from shared.py.wide_events import OAuthContext, log


@Cacheable(ttl=86400, key_pattern=f"{OAUTH_STATUS_KEY}:{{user_id}}")
async def get_all_integrations_status(user_id: str) -> dict[str, bool]:
    """
    Get status for ALL integrations for a user. This is the ONLY cached function.

    Strategy:
    1. Query MongoDB user_integrations first (canonical source for user connections)
    2. For platform integrations not in user_integrations, check external services
       (supports legacy users who connected before user_integrations existed)

    Args:
        user_id: The user ID to check status for

    Returns:
        dict[str, bool]: Mapping of integration_id -> connection status for ALL integrations
    """
    result = {}

    # Step 1: Get all user_integrations from MongoDB (canonical source)
    user_ints = await user_integration_repository.list_for_user(user_id, limit=100)
    mongo_status = {
        ui.integration_id: ui.status == INTEGRATION_STATUS_CONNECTED for ui in user_ints
    }

    # Track which platform integrations need external verification
    composio_providers = []
    composio_id_to_provider = {}

    for integration in OAUTH_INTEGRATIONS:
        if not integration.available:
            result[integration.id] = False
            continue

        # If user has this integration in MongoDB, use that status
        if integration.id in mongo_status:
            result[integration.id] = mongo_status[integration.id]
            continue

        # Not in MongoDB - check external services (legacy support)
        if integration.managed_by == MANAGED_BY_MCP:
            # All MCPs (auth or not) use MongoDB user_integrations as source of truth
            # If not in mongo_status, they're not connected
            result[integration.id] = False
        elif integration.managed_by == MANAGED_BY_COMPOSIO:
            composio_providers.append(integration.provider)
            composio_id_to_provider[integration.id] = integration.provider
        elif integration.managed_by == MANAGED_BY_SELF:
            # Check self-managed integrations (Google) via PostgreSQL tokens
            try:
                token = await token_repository.get_token(
                    user_id, integration.provider, renew_if_expired=True
                )
                authorized_scopes = str(token.get("scope", "")).split()
                required_scopes = get_integration_scopes(integration.id)
                result[integration.id] = all(
                    scope in authorized_scopes for scope in required_scopes
                )
            except Exception as e:
                log.debug(
                    f"{LogTag.OAUTH} Token not found for",
                    provider=integration.provider,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                result[integration.id] = False

    # Step 2: Batch check Composio integrations not in MongoDB
    if composio_providers:
        try:
            composio_service = get_composio_service()
            status_map = await composio_service.check_connection_status(composio_providers, user_id)
            for integration_id, provider in composio_id_to_provider.items():
                result[integration_id] = status_map.get(provider, False)
        except Exception as e:
            log.error(
                f"{LogTag.OAUTH} Error batch checking Composio integrations",
                error=str(e),
                error_type=type(e).__name__,
                user_id=user_id,
            )
            for integration_id in composio_id_to_provider:
                result[integration_id] = False

    # Include custom integrations from MongoDB that are connected
    for integration_id, is_connected in mongo_status.items():
        if integration_id not in result:
            result[integration_id] = is_connected

    log.set(oauth=OAuthContext(operation="status"), result_count=len(result))
    return result
