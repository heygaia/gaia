"""
Google OAuth Scope Dependencies

This module provides FastAPI dependencies for validating Google OAuth scopes
before allowing access to protected endpoints that require specific integrations.
"""

from typing import List, Literal, Union

import httpx
from app.api.v1.dependencies.oauth_dependencies import get_current_user
from app.config.loggers import auth_logger as logger
from app.config.oauth_config import get_integration_scopes, get_short_name_mapping
from app.config.token_repository import token_repository
from fastapi import Depends, HTTPException, status

http_async_client = httpx.AsyncClient(timeout=10.0)


def require_google_scope(scope: Union[str, List[str]]):
    """
    Dependency factory that creates a dependency to check for specific Google OAuth scopes.

    Args:
        scope: The required Google OAuth scope(s). Can be a single scope string or a list of scopes.
               If a list is provided, ALL scopes must be present.

    Returns:
        A dependency function that validates the user has the required scope(s)

    Raises:
        HTTPException: 403 if the user doesn't have the required scope(s)
    """

    async def wrapper(user: dict = Depends(get_current_user)):
        user_id = user.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found",
            )

        try:
            try:
                token = await token_repository.get_token(
                    user_id, "google", renew_if_expired=True
                )
                authorized_scopes = str(token.get("scope", "")).split()
            except HTTPException:
                authorized_scopes = []

            # Handle both single scope and list of scopes
            required_scopes = [scope] if isinstance(scope, str) else scope
            missing_scopes = [s for s in required_scopes if s not in authorized_scopes]

            if missing_scopes:
                categories = [s.split("/")[-1].split(".")[0] for s in missing_scopes]
                unique_categories = list(set(categories))
                friendly_list = ", ".join(unique_categories)
                detail = {
                    "type": "integration",
                    "message": f"Missing permissions: {friendly_list}. Please connect integrations in settings.",
                }
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=detail,
                )

            return user

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error checking OAuth scope: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to verify OAuth permissions",
            )

    return wrapper


def require_google_integration(
    integration: Literal["gmail", "calendar", "drive", "docs"],
):
    """
    Convenience function to get scope dependency by integration name.

    Usage Examples:

        # For Calendar endpoints (requires both read and write scopes)
        @app.get("/calendar/events")
        def get_events(user = Depends(require_google_integration("calendar"))):
            # user has Calendar scope with both read and write permissions

        # For Gmail endpoints
        @app.get("/gmail/messages")
        def get_messages(user = Depends(require_google_integration("gmail"))):
            # user has Gmail scope with required permissions

    Args:
        integration: The Google integration short name

    Returns:
        The corresponding scope dependency function

    Raises:
        ValueError: If unknown integration name is provided
    """
    # Get the short name mapping from oauth_config (single source of truth)
    short_name_mapping = get_short_name_mapping()

    if integration not in short_name_mapping:
        raise ValueError(
            f"Unknown integration: {integration}. Available: {list(short_name_mapping.keys())}"
        )

    integration_id = short_name_mapping[integration]
    scope_urls = get_integration_scopes(integration_id)

    if not scope_urls:
        raise ValueError(f"No scopes found for integration: {integration_id}")

    return require_google_scope(scope_urls)
