"""
OAuth Integration Configuration

Single source of truth for all OAuth integration configurations in GAIA.
Defines integrations, scopes, display properties, and relationships.

OAuthScope: Defines OAuth permission scopes with URL and description.
Used for: Backend permission validation, frontend permission displays.

OAuthIntegration: Core integration definition with fields:
- id: Unique identifier for API endpoints, database records, frontend routing
- name: Human-readable name for frontend UI and user messages
- description: Detailed explanation for integration cards and settings pages
- icons: List of icon URLs for frontend UI components and different display sizes
- category: Groups integrations for frontend filtering, slash commands, settings organization
- provider: OAuth provider for flow routing, token management, API client selection
- scopes: Required permissions for OAuth authorization and validation
- available: Feature flag for frontend display logic and API availability
- oauth_endpoints: Custom OAuth URLs for non-standard providers
- is_special: Marks unified integrations for special frontend handling
- display_priority: Numeric sort order for frontend lists and dropdowns
- included_integrations: Child integration IDs for unified integrations
- short_name: Quick access identifier for slash commands and convenience functions

IntegrationConfigResponse: API model that converts backend fields to frontend camelCase.

Used by:
- google_scope_dependencies.py: Permission validation
- integration_checker.py: User permission checking
- oauth.py router: OAuth flows and status endpoints
- Frontend components: Integration cards, settings, slash commands
- Services: API client setup and token management

Integration types:
- Individual: Single service with own scopes (gmail, google_calendar)
- Unified: Multiple services with combined scopes (google_workspace)
- Coming soon: Placeholder with available=False (github, figma)
"""

from functools import cache
from typing import Dict, List, Optional

from app.models.oauth_models import (
    ComposioConfig,
    OAuthIntegration,
    OAuthScope,
    TriggerConfig,
)

# Define all integrations dynamically
OAUTH_INTEGRATIONS: List[OAuthIntegration] = [
    # Google Workspace - Unified Integration
    OAuthIntegration(
        id="google_workspace",
        name="Google Workspace",
        description="Connect all Google tools at once",
        icons=[
            "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/Google_%22G%22_logo.svg/1920px-Google_%22G%22_logo.svg.png",
            "https://upload.wikimedia.org/wikipedia/commons/7/7e/Gmail_icon_%282020%29.svg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Google_Calendar_icon_%282020%29.svg/640px-Google_Calendar_icon_%282020%29.svg.png",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/6/66/Google_Docs_2020_Logo.svg/640px-Google_Docs_2020_Logo.svg.png",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/1/12/Google_Drive_icon_%282020%29.svg/640px-Google_Drive_icon_%282020%29.svg.png",
        ],
        category="productivity",
        provider="google",
        scopes=[
            # Combined scopes from all Google integrations
            OAuthScope(
                scope="https://www.googleapis.com/auth/gmail.modify",
                description="Read, compose, and send emails",
            ),
            OAuthScope(
                scope="https://www.googleapis.com/auth/calendar.events",
                description="Create and manage calendar events",
            ),
            OAuthScope(
                scope="https://www.googleapis.com/auth/calendar.readonly",
                description="View calendar events",
            ),
            OAuthScope(
                scope="https://www.googleapis.com/auth/documents",
                description="Create and edit documents",
            ),
            OAuthScope(
                scope="https://www.googleapis.com/auth/drive.file",
                description="Create and manage files",
            ),
        ],
        is_special=True,
        display_priority=100,
        included_integrations=[
            "gmail",
            "google_calendar",
            "google_docs",
            "google_drive",
        ],
        managed_by="self",
    ),
    # Individual Google integrations
    OAuthIntegration(
        id="google_calendar",
        name="Google Calendar",
        description="Schedule and manage your calendar events seamlessly",
        icons=[
            "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Google_Calendar_icon_%282020%29.svg/640px-Google_Calendar_icon_%282020%29.svg.png"
        ],
        category="productivity",
        provider="google",
        scopes=[
            OAuthScope(
                scope="https://www.googleapis.com/auth/calendar.events",
                description="Create and manage calendar events",
            ),
            OAuthScope(
                scope="https://www.googleapis.com/auth/calendar.readonly",
                description="View calendar events",
            ),
        ],
        short_name="calendar",
        managed_by="self",
    ),
    OAuthIntegration(
        id="google_docs",
        name="Google Docs",
        description="Create and edit documents with AI assistance",
        icons=[
            "https://upload.wikimedia.org/wikipedia/commons/thumb/6/66/Google_Docs_2020_Logo.svg/640px-Google_Docs_2020_Logo.svg.png"
        ],
        category="productivity",
        provider="google",
        scopes=[
            OAuthScope(
                scope="https://www.googleapis.com/auth/documents",
                description="Create and edit documents",
            ),
        ],
        short_name="docs",
        managed_by="self",
    ),
    OAuthIntegration(
        id="gmail",
        name="Gmail",
        description="Manage emails, compose messages, and organize your inbox",
        icons=[
            "https://upload.wikimedia.org/wikipedia/commons/7/7e/Gmail_icon_%282020%29.svg"
        ],
        category="communication",
        provider="gmail",
        scopes=[
            OAuthScope(
                scope="https://www.googleapis.com/auth/gmail.modify",
                description="Read, compose, and send emails",
            )
        ],
        short_name="gmail",
        managed_by="composio",
        composio_config=ComposioConfig(
            auth_config_id="ac_Tnn55kCyinEJ", toolkit="GMAIL"
        ),
        associated_triggers=[
            TriggerConfig(
                slug="GMAIL_NEW_GMAIL_MESSAGE",
                name="New Gmail Message",
                description="Triggered when a new Gmail message arrives",
                config={"labelIds": "INBOX", "user_id": "me", "interval": 1},
            )
        ],
    ),
    OAuthIntegration(
        id="google_drive",
        name="Google Drive",
        description="Access and manage your files in the cloud",
        icons=[
            "https://upload.wikimedia.org/wikipedia/commons/thumb/1/12/Google_Drive_icon_%282020%29.svg/640px-Google_Drive_icon_%282020%29.svg.png"
        ],
        category="storage",
        provider="google",
        scopes=[
            OAuthScope(
                scope="https://www.googleapis.com/auth/drive.file",
                description="Create and manage files",
            ),
        ],
        short_name="drive",
        managed_by="self",
    ),
    # Composio integrations
    OAuthIntegration(
        id="notion",
        name="Notion",
        description="Manage pages, databases, and workspace content with AI",
        icons=[
            "https://upload.wikimedia.org/wikipedia/commons/4/45/Notion_app_logo.png"
        ],
        category="productivity",
        provider="notion",
        scopes=[],
        available=True,
        managed_by="composio",
        composio_config=ComposioConfig(
            auth_config_id="ac_DR3IWp9-Kezl", toolkit="NOTION"
        ),
    ),
    OAuthIntegration(
        id="twitter",
        name="Twitter",
        description="Post tweets, read timelines, and manage your account with AI-powered tools",
        icons=[
            "https://upload.wikimedia.org/wikipedia/commons/thumb/c/ce/X_logo_2023.svg/600px-X_logo_2023.svg.png?20250120013756"
        ],
        category="social",
        provider="twitter",
        scopes=[],
        available=True,
        managed_by="composio",
        composio_config=ComposioConfig(
            auth_config_id="ac_vloH3fnhIeUa", toolkit="TWITTER"
        ),
    ),
    OAuthIntegration(
        id="google_sheets",
        name="Google Sheets",
        description="Create, read, and update Google Sheets with AI-powered tools for automation and data management",
        icons=[
            "https://upload.wikimedia.org/wikipedia/commons/a/ae/Google_Sheets_2020_Logo.svg"
        ],
        category="productivity",
        provider="google_sheets",
        scopes=[],
        available=True,
        managed_by="composio",
        composio_config=ComposioConfig(
            auth_config_id="ac_18I3fRfWyXDu", toolkit="GOOGLE_SHEETS"
        ),
    ),
    OAuthIntegration(
        id="linkedin",
        name="LinkedIn",
        description="Share posts, engage with your network, and manage your professional presence using AI-powered tools",
        icons=[
            "https://upload.wikimedia.org/wikipedia/commons/c/ca/LinkedIn_logo_initials.png"
        ],
        category="social",
        provider="linkedin",
        scopes=[],
        available=True,
        managed_by="composio",
        composio_config=ComposioConfig(
            auth_config_id="ac_GMeJBELf3z_m", toolkit="LINKEDIN"
        ),
    ),
]

@cache
def get_integration_by_id(integration_id: str) -> Optional[OAuthIntegration]:
    """Get an integration by its ID."""
    return next((i for i in OAUTH_INTEGRATIONS if i.id == integration_id), None)

@cache
def get_integration_scopes(integration_id: str) -> List[str]:
    """Get the OAuth scopes for a specific integration."""
    integration = get_integration_by_id(integration_id)
    if not integration:
        return []
    return [scope.scope for scope in integration.scopes]

@cache
def get_short_name_mapping() -> Dict[str, str]:
    """Get mapping of short names to integration IDs for convenience functions."""
    return {i.short_name: i.id for i in OAUTH_INTEGRATIONS if i.short_name}


@cache
def get_composio_social_configs() -> Dict[str, ComposioConfig]:
    """Generate COMPOSIO_SOCIAL_CONFIGS dynamically from integrations managed by Composio."""
    configs = {}
    for integration in OAUTH_INTEGRATIONS:
        if integration.managed_by == "composio" and integration.composio_config:
            configs[integration.provider] = integration.composio_config
    return configs


@cache
def get_integration_by_config(auth_config_id: str) -> Optional[OAuthIntegration]:
    """Get an integration by its Composio auth config ID."""
    return next(
        (
            i
            for i in OAUTH_INTEGRATIONS
            if i.composio_config and i.composio_config.auth_config_id == auth_config_id
        ),
        None,
    )
