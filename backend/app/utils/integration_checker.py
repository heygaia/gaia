"""
Integration Connection Checker Utility

This module provides utilities to check if a user has the required integration
permissions and stream connection prompts to the frontend when needed.
"""

from typing import Optional
import httpx
from langgraph.config import get_stream_writer

from app.config.oauth_config import get_integration_by_id
from app.config.loggers import auth_logger as logger

http_async_client = httpx.AsyncClient(timeout=10.0)

# Mapping of tool categories to required integrations
TOOL_INTEGRATION_MAPPING = {
    "mail": "gmail",
    "calendar": "google_calendar",
    "google_docs": "google_docs",
    "google_drive": "google_drive",
    # Add more mappings as needed
}

# Mapping of integration IDs to their required scopes
INTEGRATION_SCOPE_MAPPING = {
    "gmail": ["https://www.googleapis.com/auth/gmail.modify"],
    "google_calendar": [
        "https://www.googleapis.com/auth/calendar.events",
        "https://www.googleapis.com/auth/calendar.readonly",
    ],
    "google_docs": ["https://www.googleapis.com/auth/documents"],
    "google_drive": ["https://www.googleapis.com/auth/drive.file"],
}


async def check_user_has_integration(access_token: str, integration_id: str) -> bool:
    """
    Check if the user has the required integration permissions.

    Args:
        access_token: User's OAuth access token
        integration_id: The integration ID to check (e.g., 'gmail', 'google_calendar')

    Returns:
        bool: True if user has required permissions, False otherwise
    """
    if not access_token:
        return False

    try:
        # Get required scopes for this integration
        required_scopes = INTEGRATION_SCOPE_MAPPING.get(integration_id, [])
        if not required_scopes:
            logger.warning(f"No scopes defined for integration: {integration_id}")
            return False

        # Check Google token info to get authorized scopes
        token_info_response = await http_async_client.get(
            f"https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={access_token}"
        )

        if token_info_response.status_code != 200:
            logger.warning("Invalid access token when checking integration permissions")
            return False

        token_data = token_info_response.json()
        authorized_scopes = token_data.get("scope", "").split()

        # Check if all required scopes are present
        missing_scopes = [
            scope for scope in required_scopes if scope not in authorized_scopes
        ]
        return len(missing_scopes) == 0

    except Exception as e:
        logger.error(f"Error checking integration permissions: {e}")
        return False


async def stream_integration_connection_prompt(
    integration_id: str,
    tool_name: Optional[str] = None,
    tool_category: Optional[str] = None,
    message: Optional[str] = None,
) -> None:
    """
    Stream an integration connection prompt to the frontend.

    Args:
        integration_id: The integration ID that needs to be connected
        tool_name: Optional tool name that triggered this requirement
        tool_category: Optional tool category
        message: Optional custom message to display
    """
    try:
        writer = get_stream_writer()
        if not writer:
            logger.warning("No stream writer available for integration prompt")
            return

        # Get integration details
        integration = get_integration_by_id(integration_id)
        if not integration:
            logger.error(f"Integration not found: {integration_id}")
            return

        # Prepare the integration connection data
        connection_data = {
            "integration_connection_required": {
                "integration_id": integration_id,
                "integration_name": integration.name,
                "integration_icon": integration.icon,
                "integration_description": integration.description,
                "integration_category": integration.category,
                "tool_name": tool_name,
                "tool_category": tool_category,
                "message": message
                or f"To use {str(tool_name).replace('_', ' ') or 'this feature'}, please connect your {integration.name} account.",
                "connect_url": f"/oauth/login/integration/{integration_id}",
                "settings_url": "/settings?section=integrations",
            }
        }

        # Stream the data to frontend
        writer(connection_data)
        logger.info(f"Streamed integration connection prompt for: {integration_id}")

    except Exception as e:
        logger.error(f"Error streaming integration connection prompt: {e}")


def get_required_integration_for_tool_category(tool_category: str) -> Optional[str]:
    """
    Get the required integration ID for a given tool category.

    Args:
        tool_category: The tool category (e.g., 'mail', 'calendar')

    Returns:
        Optional[str]: The integration ID if one is required, None otherwise
    """
    return TOOL_INTEGRATION_MAPPING.get(tool_category)


async def check_and_prompt_integration(
    access_token: str, tool_category: str, tool_name: Optional[str] = None
) -> bool:
    """
    Check if user has required integration and prompt if not.

    Args:
        access_token: User's OAuth access token
        tool_category: The tool category being accessed
        tool_name: Optional tool name for better messaging

    Returns:
        bool: True if user has required permissions, False if prompt was sent
    """
    required_integration = get_required_integration_for_tool_category(tool_category)
    if not required_integration:
        # No integration required for this tool category
        return True

    has_integration = await check_user_has_integration(
        access_token, required_integration
    )
    if has_integration:
        return True

    # User doesn't have the required integration, send connection prompt
    await stream_integration_connection_prompt(
        integration_id=required_integration,
        tool_name=tool_name,
        tool_category=tool_category,
    )
    return False
