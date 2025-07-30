"""
OAuth Integration Configuration

This module defines all OAuth integrations dynamically.
Add new integrations by simply adding to the OAUTH_INTEGRATIONS list.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel


class OAuthScope(BaseModel):
    """OAuth scope configuration."""

    scope: str
    description: str


class OAuthIntegration(BaseModel):
    """OAuth integration configuration."""

    id: str
    name: str
    description: str
    icon: str
    category: str
    provider: str  # 'google', 'github', 'figma', 'notion', etc.
    scopes: List[OAuthScope]
    available: bool = True
    oauth_endpoints: Optional[Dict[str, str]] = None


# Define all integrations dynamically
OAUTH_INTEGRATIONS: List[OAuthIntegration] = [
    # Google integrations
    OAuthIntegration(
        id="google_calendar",
        name="Google Calendar",
        description="Schedule and manage your calendar events seamlessly",
        icon="https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Google_Calendar_icon_%282020%29.svg/640px-Google_Calendar_icon_%282020%29.svg.png",
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
    ),
    OAuthIntegration(
        id="google_docs",
        name="Google Docs",
        description="Create and edit documents with AI assistance",
        icon="https://upload.wikimedia.org/wikipedia/commons/thumb/6/66/Google_Docs_2020_Logo.svg/640px-Google_Docs_2020_Logo.svg.png",
        category="productivity",
        provider="google",
        scopes=[
            OAuthScope(
                scope="https://www.googleapis.com/auth/documents",
                description="Create and edit documents",
            ),
        ],
    ),
    OAuthIntegration(
        id="gmail",
        name="Gmail",
        description="Manage emails, compose messages, and organize your inbox",
        icon="https://upload.wikimedia.org/wikipedia/commons/7/7e/Gmail_icon_%282020%29.svg",
        category="communication",
        provider="google",
        scopes=[
            OAuthScope(
                scope="https://www.googleapis.com/auth/gmail.modify",
                description="Read, compose, and send emails",
            ),
        ],
    ),
    OAuthIntegration(
        id="google_drive",
        name="Google Drive",
        description="Access and manage your files in the cloud",
        icon="https://upload.wikimedia.org/wikipedia/commons/thumb/1/12/Google_Drive_icon_%282020%29.svg/640px-Google_Drive_icon_%282020%29.svg.png",
        category="storage",
        provider="google",
        scopes=[
            OAuthScope(
                scope="https://www.googleapis.com/auth/drive.file",
                description="Create and manage files",
            ),
        ],
    ),
    # Coming soon integrations
    OAuthIntegration(
        id="github",
        name="GitHub",
        description="Manage repositories, issues, and pull requests",
        icon="https://cdn.brandfetch.io/idZAyF9rlg/theme/light/symbol.svg?c=1dxbfHSJFAPEGdCLU4o5B",
        category="development",
        provider="github",
        scopes=[],
        available=False,
    ),
    OAuthIntegration(
        id="figma",
        name="Figma",
        description="Create and collaborate on design projects",
        icon="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/figma/figma-original.svg",
        category="creative",
        provider="figma",
        scopes=[],
        available=False,
    ),
    OAuthIntegration(
        id="notion",
        name="Notion",
        description="Manage pages, databases, and workspace content with AI",
        icon="https://upload.wikimedia.org/wikipedia/commons/4/45/Notion_app_logo.png",
        category="productivity",
        provider="notion",
        scopes=[],
        available=False,
    ),
    OAuthIntegration(
        id="whatsapp",
        name="WhatsApp",
        description="Send and receive messages",
        icon="https://upload.wikimedia.org/wikipedia/commons/thumb/6/6b/WhatsApp.svg/1024px-WhatsApp.svg.png?20220228223904",
        category="communication",
        provider="facebook",
        scopes=[],
        available=False,
    ),
]


def get_integration_by_id(integration_id: str) -> Optional[OAuthIntegration]:
    """Get an integration by its ID."""
    return next((i for i in OAUTH_INTEGRATIONS if i.id == integration_id), None)


def get_integrations_by_provider(provider: str) -> List[OAuthIntegration]:
    """Get all integrations for a specific provider."""
    return [i for i in OAUTH_INTEGRATIONS if i.provider == provider]


def get_available_integrations() -> List[OAuthIntegration]:
    """Get all available integrations."""
    return [i for i in OAUTH_INTEGRATIONS if i.available]


def get_integration_scopes(integration_id: str) -> List[str]:
    """Get the OAuth scopes for a specific integration."""
    integration = get_integration_by_id(integration_id)
    if not integration:
        return []
    return [scope.scope for scope in integration.scopes]
