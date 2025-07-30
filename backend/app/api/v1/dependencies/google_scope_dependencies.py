"""
Google OAuth Scope Dependencies

This module provides FastAPI dependencies for validating Google OAuth scopes
before allowing access to protected endpoints that require specific integrations.
"""

from typing import Literal, Union, List, Dict

import httpx
from fastapi import HTTPException, Depends, status

from app.api.v1.dependencies.oauth_dependencies import get_current_user
from app.config.loggers import auth_logger as logger

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
        access_token = user.get("access_token")
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Access token not found",
            )

        try:
            # Check Google token info to get authorized scopes
            token_info_response = await http_async_client.get(
                f"https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={access_token}"
            )

            if token_info_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid access token",
                )

            token_data = token_info_response.json()
            authorized_scopes = token_data.get("scope", "").split()

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


# Mapping of integration names to their required OAuth scope URLs
GOOGLE_SCOPE_URLS: Dict[str, Union[str, List[str]]] = {
    "gmail": "https://www.googleapis.com/auth/gmail.modify",
    "calendar": [
        "https://www.googleapis.com/auth/calendar.events",
        "https://www.googleapis.com/auth/calendar.readonly",
    ],
    "drive": "https://www.googleapis.com/auth/drive.file",
    "docs": "https://www.googleapis.com/auth/documents",
}


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

        # For Calendar readonly endpoints
        @app.get("/calendar/events/readonly")
        def get_events_readonly(user = Depends(require_google_integration("calendar_readonly"))):
            # user has Calendar readonly scope

    Args:
        integration: The Google integration name

    Returns:
        The corresponding scope dependency function

    Raises:
        ValueError: If unknown integration name is provided
    """
    if integration not in GOOGLE_SCOPE_URLS:
        raise ValueError(
            f"Unknown integration: {integration}. Available: {list(GOOGLE_SCOPE_URLS.keys())}"
        )

    scope_urls = GOOGLE_SCOPE_URLS[integration]
    return require_google_scope(scope_urls)
