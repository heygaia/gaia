"""Tests for app/api/v1/endpoints/short_links.py"""

from unittest.mock import AsyncMock, patch

from httpx import AsyncClient
import pytest

# routes.py mounts the short-links router at its own "/l" prefix.
BASE = "/api/v1/l"

_ENDPOINT = "app.api.v1.endpoints.short_links"


class TestResolveShortLink:
    """Tests for GET /l/{slug}."""

    @pytest.mark.asyncio
    async def test_resolved_artifact_is_never_cached(self, client: AsyncClient) -> None:
        """A capability URL can be revoked at any moment; a cached 200 in a
        browser or an intermediary would keep serving content the owner has
        already taken back."""
        artifact = {
            "title": "Q3 plan",
            "content": "body",
            "todo_id": "todo-1",
            "target_type": "todo_canvas",
        }
        with patch(f"{_ENDPOINT}.get_public_artifact", AsyncMock(return_value=artifact)):
            response = await client.get(f"{BASE}/abcdefghijk")

        assert response.status_code == 200
        assert response.json() == artifact
        assert response.headers["cache-control"] == "no-store"

    @pytest.mark.asyncio
    async def test_unknown_slug_is_404(self, client: AsyncClient) -> None:
        with patch(f"{_ENDPOINT}.get_public_artifact", AsyncMock(return_value=None)):
            response = await client.get(f"{BASE}/abcdefghijk")

        assert response.status_code == 404
