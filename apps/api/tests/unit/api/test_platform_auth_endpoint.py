"""Unit tests for the platform OAuth endpoints (app/api/v1/endpoints/platform_auth.py).

Covers the Discord/Slack OAuth callback success path and its analytics capture.
"""

from unittest.mock import AsyncMock, patch

from httpx import AsyncClient

from app.models.platform_models import PlatformLinkResult
from app.utils.errors import create_error

_MODULE = "app.api.v1.endpoints.platform_auth"
BASE = "/api/v1/platform-auth"


class _FakeTokenResponse:
    status_code = 200

    @staticmethod
    def json() -> dict:
        return {"access_token": "tok_abc"}


class _FakeUserInfoResponse:
    status_code = 200

    @staticmethod
    def json() -> dict:
        return {"id": "DISC1", "username": "user", "global_name": "User"}


class _FakeAsyncClient:
    """Stand-in for httpx.AsyncClient covering the token + user-info calls."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        pass

    async def __aenter__(self) -> "_FakeAsyncClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        pass

    async def post(self, *args: object, **kwargs: object) -> _FakeTokenResponse:
        return _FakeTokenResponse()

    async def get(self, *args: object, **kwargs: object) -> _FakeUserInfoResponse:
        return _FakeUserInfoResponse()


class TestPlatformOAuthCallback:
    """GET /api/v1/platform-auth/{platform}/callback"""

    async def test_discord_callback_captures_connected_event(self, client: AsyncClient) -> None:
        link_result = PlatformLinkResult(
            status="linked",
            platform="discord",
            platform_user_id="DISC1",
            connected_at="2024-01-01T00:00:00Z",
            is_new_link=True,
        )
        with (
            patch(
                "app.services.oauth.oauth_state_service.validate_and_consume_oauth_state",
                new_callable=AsyncMock,
                return_value={"user_id": "uid1", "redirect_path": "/settings"},
            ) as mock_validate,
            patch(f"{_MODULE}.httpx.AsyncClient", new=_FakeAsyncClient),
            patch(
                f"{_MODULE}.complete_platform_link",
                new_callable=AsyncMock,
                return_value=link_result,
            ) as mock_complete,
        ):
            resp = await client.get(
                f"{BASE}/discord/callback",
                params={"code": "c1", "state": "s1"},
                follow_redirects=False,
            )

        # The signed state param must reach validation verbatim — a mutated
        # call that drops or replaces the argument would silently accept
        # forged callbacks.
        mock_validate.assert_called_once_with("s1")
        assert resp.status_code in (302, 307)
        assert "oauth_success=true" in resp.headers["location"]
        # Explicit user id, not the request context: the platform OAuth
        # redirect carries no WorkOS session, so a context capture would land
        # the link on an anonymous profile.
        # One implementation of the link's follow-through (greeting, account
        # sync, analytics) for every route that creates a link: this one used
        # to inline three of the four and skip the sync.
        mock_complete.assert_awaited_once()
        assert mock_complete.await_args.args == ("uid1", "discord", "DISC1")

    async def test_a_link_owned_by_another_account_redirects_with_already_linked(
        self, client: AsyncClient
    ) -> None:
        with (
            patch(
                "app.services.oauth.oauth_state_service.validate_and_consume_oauth_state",
                new_callable=AsyncMock,
                return_value={"user_id": "uid1", "redirect_path": "/settings"},
            ),
            patch(f"{_MODULE}.httpx.AsyncClient", new=_FakeAsyncClient),
            patch(
                f"{_MODULE}.complete_platform_link",
                new_callable=AsyncMock,
                side_effect=create_error(
                    message="already linked", why="other account", fix="unlink", status_code=409
                ),
            ),
        ):
            resp = await client.get(
                f"{BASE}/discord/callback",
                params={"code": "c1", "state": "s1"},
                follow_redirects=False,
            )

        assert resp.status_code in (302, 307)
        assert "oauth_error=already_linked" in resp.headers["location"]

    async def test_callback_invalid_state_redirects_with_error(self, client: AsyncClient) -> None:
        """A consumed/invalid state token must bounce to the UI error path."""
        with patch(
            "app.services.oauth.oauth_state_service.validate_and_consume_oauth_state",
            new_callable=AsyncMock,
            return_value=None,
        ):
            resp = await client.get(
                f"{BASE}/discord/callback",
                params={"code": "c1", "state": "bad"},
                follow_redirects=False,
            )
        assert resp.status_code in (302, 307)
        assert "oauth_error=invalid_state" in resp.headers["location"]

    async def test_callback_missing_params_redirects_with_error(self, client: AsyncClient) -> None:
        """Missing code/state must bounce before any provider call is made."""
        resp = await client.get(f"{BASE}/discord/callback", follow_redirects=False)
        assert resp.status_code in (302, 307)
        assert "oauth_error=missing_params" in resp.headers["location"]
