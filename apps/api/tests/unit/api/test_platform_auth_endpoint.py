"""Unit tests for the platform OAuth endpoints (app/api/v1/endpoints/platform_auth.py).

Covers the Discord/Slack OAuth callback success path and its analytics capture.
"""

from typing import ClassVar
from unittest.mock import AsyncMock, patch

from httpx import AsyncClient
import pytest

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


class _RecordingClient(_FakeAsyncClient):
    """Records the provider calls so the wire shape can be asserted exactly."""

    posts: ClassVar[list[tuple[tuple[object, ...], dict[str, object]]]] = []
    token_response: ClassVar[object] = _FakeTokenResponse()

    async def post(self, *args: object, **kwargs: object) -> object:
        _RecordingClient.posts.append((args, kwargs))
        return _RecordingClient.token_response


class _FailedTokenResponse:
    status_code = 400
    text = "invalid_grant"

    @staticmethod
    def json() -> dict:
        return {}


class _SlackRefusedTokenResponse:
    status_code = 200
    text = "ok false"

    @staticmethod
    def json() -> dict:
        return {"ok": False, "error": "invalid_code"}


class TestExchangeCode:
    """The token exchange is the one call whose exact wire shape the provider checks."""

    def setup_method(self) -> None:
        _RecordingClient.posts = []
        _RecordingClient.token_response = _FakeTokenResponse()

    async def test_posts_the_authorization_code_grant_to_the_token_url(self) -> None:
        from app.api.v1.endpoints.platform_auth import PLATFORM_CONFIGS, _exchange_code

        config = PLATFORM_CONFIGS["discord"]
        with (
            patch(f"{_MODULE}.httpx.AsyncClient", new=_RecordingClient),
            patch(f"{_MODULE}.settings") as settings,
        ):
            settings.DISCORD_OAUTH_CLIENT_ID = "cid"
            settings.DISCORD_OAUTH_CLIENT_SECRET = "csecret"
            settings.DISCORD_OAUTH_REDIRECT_URI = "https://api.test/cb"
            token_data = await _exchange_code(config, "c1")

        assert token_data == {"access_token": "tok_abc"}
        assert _RecordingClient.posts == [
            (
                ("https://discord.com/api/oauth2/token",),
                {
                    "data": {
                        "client_id": "cid",
                        "client_secret": "csecret",
                        "code": "c1",
                        "redirect_uri": "https://api.test/cb",
                        "grant_type": "authorization_code",
                    },
                    "headers": {"Content-Type": "application/x-www-form-urlencoded"},
                },
            )
        ]

    async def test_a_refused_exchange_is_logged_with_the_providers_answer(self) -> None:
        from app.api.v1.endpoints.platform_auth import (
            PLATFORM_CONFIGS,
            _CallbackRefused,
            _exchange_code,
        )

        _RecordingClient.token_response = _FailedTokenResponse()
        with (
            patch(f"{_MODULE}.httpx.AsyncClient", new=_RecordingClient),
            patch(f"{_MODULE}.log") as log,
            pytest.raises(_CallbackRefused) as refused,
        ):
            await _exchange_code(PLATFORM_CONFIGS["discord"], "c1")

        assert refused.value.oauth_error == "token_failed"
        assert str(refused.value) == "token_failed"
        log.error.assert_called_once_with(
            "[API] Platform token exchange failed",
            platform="discord",
            status_code=400,
            error="invalid_grant",
        )

    async def test_slack_saying_ok_false_is_a_refused_exchange(self) -> None:
        from app.api.v1.endpoints.platform_auth import (
            PLATFORM_CONFIGS,
            _CallbackRefused,
            _exchange_code,
        )

        _RecordingClient.token_response = _SlackRefusedTokenResponse()
        with (
            patch(f"{_MODULE}.httpx.AsyncClient", new=_RecordingClient),
            pytest.raises(_CallbackRefused) as refused,
        ):
            await _exchange_code(PLATFORM_CONFIGS["slack"], "c1")

        assert refused.value.oauth_error == "token_failed"


class TestDiscordStyleProfile:
    def test_prefers_the_global_name_for_display(self) -> None:
        from app.api.v1.endpoints.platform_auth import _discord_style_profile

        assert _discord_style_profile({"username": "u", "global_name": "G"}) == {
            "username": "u",
            "display_name": "G",
        }

    def test_falls_back_to_the_username_when_there_is_no_global_name(self) -> None:
        from app.api.v1.endpoints.platform_auth import _discord_style_profile

        assert _discord_style_profile({"username": "u"}) == {
            "username": "u",
            "display_name": "u",
        }


class TestBounce:
    async def test_every_redirect_lands_on_the_frontend(self, client: AsyncClient) -> None:
        from app.config.settings import settings

        resp = await client.get(f"{BASE}/discord/callback", follow_redirects=False)

        assert resp.headers["location"].startswith(settings.FRONTEND_URL)
