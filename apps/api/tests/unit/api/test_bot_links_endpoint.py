"""Unit tests for the bot platform-linking endpoints.

Split out of ``test_bot_endpoint.py`` to match the route split: these cover
``app/api/v1/endpoints/bot_links.py`` (create-link-token, redeem-link-code,
link-token-info). Assertions are unchanged from the original module — only the
patch targets moved with the code.
"""

from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient
import pytest

from app.constants.auth import AUDIT_ACTOR_BOT_API
from app.models.bot_models import RedeemLinkCodeRequest
from app.models.payment_models import PlanType
from app.models.platform_models import PlatformLinkResult
from app.services.platform_link_code_service import PlatformLinkCodePayload
from app.utils.errors import AppError
from shared.py.wide_events import log, log_context

from app.api.v1.endpoints.bot_links import redeem_link_code  # isort: skip

BOT_BASE = "/api/v1/bot"
PLAN_PATCH = "app.services.platform_link_service.payment_service.get_cached_plan_type"


def _make_request(bot_api_key_valid: bool = True, **extra_state: object) -> MagicMock:
    """Build a fake Request whose .state carries bot auth attributes."""
    state = MagicMock()
    state.bot_api_key_valid = bot_api_key_valid
    state.bot_platform = extra_state.get("bot_platform")
    state.bot_platform_user_id = extra_state.get("bot_platform_user_id")
    state.user = extra_state.get("user")
    state.authenticated = extra_state.get("authenticated", False)
    return state


@pytest.fixture(autouse=True)
def _pro_plan_by_default():
    """GAIA is paid-only: default every test in this file to a paying user."""
    with patch(PLAN_PATCH, new_callable=AsyncMock, return_value=PlanType.PRO):
        yield


# ---------------------------------------------------------------------------
# POST /bot/create-link-token
# ---------------------------------------------------------------------------


class TestCreateLinkToken:
    """POST /api/v1/bot/create-link-token"""

    @patch("app.api.v1.endpoints.bot_links.redis_cache")
    @patch("app.api.v1.endpoints.bot_links.require_bot_api_key", new_callable=AsyncMock)
    async def test_create_link_token_success(
        self,
        mock_auth: AsyncMock,
        mock_redis: MagicMock,
        client: AsyncClient,
    ):
        mock_redis.client = AsyncMock()
        response = await client.post(
            f"{BOT_BASE}/create-link-token",
            json={
                "platform": "discord",
                "platform_user_id": "user123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "auth_url" in data

    @patch("app.api.v1.endpoints.bot_links.require_bot_api_key", new_callable=AsyncMock)
    async def test_create_link_token_validation_error(
        self,
        mock_auth: AsyncMock,
        client: AsyncClient,
    ):
        """Missing required fields returns 422."""
        response = await client.post(
            f"{BOT_BASE}/create-link-token",
            json={},
        )
        assert response.status_code == 422

    async def test_create_link_token_no_api_key(self, client: AsyncClient):
        """Without bot_api_key_valid on request.state, require_bot_api_key raises 401."""
        response = await client.post(
            f"{BOT_BASE}/create-link-token",
            json={"platform": "discord", "platform_user_id": "u1"},
        )
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# POST /bot/redeem-link-code
# ---------------------------------------------------------------------------

REDEEM_BODY = {"platform": "telegram", "platform_user_id": "TG42", "code": "CODE123"}
FIRST_MESSAGE = "Hi! I'm a founder. I could use help with my inbox. Who are you?"
PEEK_PATCH = "app.api.v1.endpoints.bot_links.peek_platform_link_code"
DISCARD_PATCH = "app.api.v1.endpoints.bot_links.discard_platform_link_code"
COMPLETE_PATCH = "app.api.v1.endpoints.bot_links.complete_platform_link"


def _link_result(is_new_link: bool = True) -> PlatformLinkResult:
    return PlatformLinkResult(
        status="linked",
        platform="telegram",
        platform_user_id="TG42",
        connected_at="2026-09-01T00:00:00Z",
        is_new_link=is_new_link,
    )


class TestRedeemLinkCode:
    """POST /api/v1/bot/redeem-link-code"""

    async def test_no_api_key(self, client: AsyncClient):
        response = await client.post(f"{BOT_BASE}/redeem-link-code", json=REDEEM_BODY)
        assert response.status_code == 401

    @patch("app.api.v1.endpoints.bot_links.require_bot_api_key", new_callable=AsyncMock)
    async def test_happy_path_links_and_returns_the_first_message(
        self, _auth: AsyncMock, client: AsyncClient
    ):
        with (
            patch(
                PEEK_PATCH,
                new_callable=AsyncMock,
                return_value=PlatformLinkCodePayload(user_id="user1", first_message=FIRST_MESSAGE),
            ),
            patch(DISCARD_PATCH, new_callable=AsyncMock) as mock_discard,
            patch(
                COMPLETE_PATCH, new_callable=AsyncMock, return_value=_link_result()
            ) as mock_complete,
        ):
            response = await client.post(
                f"{BOT_BASE}/redeem-link-code",
                json={**REDEEM_BODY, "username": "tg_user", "display_name": "TG User"},
            )

        assert response.status_code == 200
        assert response.json() == {"linked": True, "first_message": FIRST_MESSAGE}
        mock_discard.assert_awaited_once_with("CODE123")
        # The code, not the request body, decides which GAIA user gets linked.
        mock_complete.assert_awaited_once_with(
            "user1",
            "telegram",
            "TG42",
            profile={"username": "tg_user", "display_name": "TG User"},
        )

    @patch("app.api.v1.endpoints.bot_links.require_bot_api_key", new_callable=AsyncMock)
    async def test_expired_or_unknown_code_is_rejected_without_linking(
        self, _auth: AsyncMock, client: AsyncClient
    ):
        with (
            patch(PEEK_PATCH, new_callable=AsyncMock, return_value=None),
            patch(DISCARD_PATCH, new_callable=AsyncMock),
            patch(COMPLETE_PATCH, new_callable=AsyncMock) as mock_complete,
        ):
            response = await client.post(f"{BOT_BASE}/redeem-link-code", json=REDEEM_BODY)

        assert response.status_code == 400
        assert "expired" in response.json()["message"].lower()
        mock_complete.assert_not_awaited()

    @patch("app.api.v1.endpoints.bot_links.require_bot_api_key", new_callable=AsyncMock)
    async def test_reused_code_is_rejected_on_the_second_call(
        self, _auth: AsyncMock, client: AsyncClient
    ):
        """Single-use: the store hands the binding over exactly once."""
        payload = PlatformLinkCodePayload(user_id="user1", first_message=FIRST_MESSAGE)
        with (
            patch(PEEK_PATCH, new_callable=AsyncMock, side_effect=[payload, None]),
            patch(DISCARD_PATCH, new_callable=AsyncMock),
            patch(COMPLETE_PATCH, new_callable=AsyncMock, return_value=_link_result()),
        ):
            first = await client.post(f"{BOT_BASE}/redeem-link-code", json=REDEEM_BODY)
            second = await client.post(f"{BOT_BASE}/redeem-link-code", json=REDEEM_BODY)

        assert first.status_code == 200
        assert second.status_code == 400

    @patch("app.api.v1.endpoints.bot_links.require_bot_api_key", new_callable=AsyncMock)
    async def test_account_linked_elsewhere_returns_409(
        self, _auth: AsyncMock, client: AsyncClient
    ):
        with (
            patch(
                PEEK_PATCH,
                new_callable=AsyncMock,
                return_value=PlatformLinkCodePayload(user_id="user1", first_message=FIRST_MESSAGE),
            ),
            patch(DISCARD_PATCH, new_callable=AsyncMock) as mock_discard,
            patch(
                COMPLETE_PATCH,
                new_callable=AsyncMock,
                side_effect=AppError(
                    message="This telegram account is already linked to another GAIA user",
                    status_code=409,
                ),
            ),
        ):
            response = await client.post(f"{BOT_BASE}/redeem-link-code", json=REDEEM_BODY)

        assert response.status_code == 409
        # The refusal asks the user to unlink and tap again: the code must still work.
        mock_discard.assert_not_awaited()
        assert "already linked" in response.json()["message"]

    @patch("app.api.v1.endpoints.bot_links.require_bot_api_key", new_callable=AsyncMock)
    async def test_invalid_platform_is_rejected(self, _auth: AsyncMock, client: AsyncClient):
        response = await client.post(
            f"{BOT_BASE}/redeem-link-code", json={**REDEEM_BODY, "platform": "myspace"}
        )
        assert response.status_code == 422
        # The rejection names the offending platform — a bot operator sending a
        # typo'd platform has to be able to tell what was wrong from the body.
        errors = response.json()["detail"]
        assert [err["loc"] for err in errors] == [["body", "platform"]]
        assert "myspace" in errors[0]["msg"]

    @patch("app.api.v1.endpoints.bot_links.require_bot_api_key", new_callable=AsyncMock)
    async def test_header_mismatch_is_rejected_before_the_code_is_consumed(
        self, _auth: AsyncMock, client: AsyncClient
    ):
        """An API-key holder must not redeem a code onto someone else's handle."""

        async def _mismatched_request(request):
            request.state.bot_platform = "telegram"
            request.state.bot_platform_user_id = "SOMEONE_ELSE"

        with (
            patch(
                "app.api.v1.endpoints.bot_links.require_bot_api_key",
                new=AsyncMock(side_effect=_mismatched_request),
            ),
            patch(PEEK_PATCH, new_callable=AsyncMock) as mock_peek,
        ):
            response = await client.post(f"{BOT_BASE}/redeem-link-code", json=REDEEM_BODY)

        assert response.status_code == 403
        mock_peek.assert_not_awaited()

    @patch("app.api.v1.endpoints.bot_links.require_bot_api_key", new_callable=AsyncMock)
    async def test_a_platform_mismatch_alone_is_enough_to_reject(
        self, _auth: AsyncMock, client: AsyncClient
    ):
        """The two halves of the guard are independent: a Discord key redeeming a
        Telegram code carries the SAME handle it is authenticated for, so only
        the platform half can catch it."""

        async def _wrong_platform(request):
            request.state.bot_platform = "discord"
            request.state.bot_platform_user_id = "TG42"

        with (
            patch(
                "app.api.v1.endpoints.bot_links.require_bot_api_key",
                new=AsyncMock(side_effect=_wrong_platform),
            ),
            patch(PEEK_PATCH, new_callable=AsyncMock) as mock_peek,
        ):
            response = await client.post(f"{BOT_BASE}/redeem-link-code", json=REDEEM_BODY)

        assert response.status_code == 403
        mock_peek.assert_not_awaited()

    @patch("app.api.v1.endpoints.bot_links.require_bot_api_key", new_callable=AsyncMock)
    async def test_the_expired_code_body_tells_the_user_what_to_do_next(
        self, _auth: AsyncMock, client: AsyncClient
    ):
        """This body is the whole reply a bot user sees when a one-tap link goes
        stale — the why/fix pair is what turns a dead end into a retry."""
        with (
            patch(PEEK_PATCH, new_callable=AsyncMock, return_value=None),
            patch(DISCARD_PATCH, new_callable=AsyncMock),
        ):
            response = await client.post(f"{BOT_BASE}/redeem-link-code", json=REDEEM_BODY)

        assert response.status_code == 400
        assert response.json() == {
            "message": "This link has expired or was already used.",
            "why": "the one-tap code is single-use and short-lived",
            "fix": "head back to GAIA on the web and pick your platform again",
        }

    @patch("app.api.v1.endpoints.bot_links.require_bot_api_key", new_callable=AsyncMock)
    async def test_the_header_mismatch_body_names_the_mismatch(
        self, _auth: AsyncMock, client: AsyncClient
    ):
        async def _mismatched_request(request):
            request.state.bot_platform = "telegram"
            request.state.bot_platform_user_id = "SOMEONE_ELSE"

        with patch(
            "app.api.v1.endpoints.bot_links.require_bot_api_key",
            new=AsyncMock(side_effect=_mismatched_request),
        ):
            response = await client.post(f"{BOT_BASE}/redeem-link-code", json=REDEEM_BODY)

        assert response.status_code == 403
        assert response.json() == {
            "message": "Request body does not match the authenticated bot headers"
        }

    async def test_a_matching_header_is_not_treated_as_a_mismatch(self, client: AsyncClient):
        """The guard compares for INEQUALITY: flipped to `==`, the ordinary case
        where the bot's own headers match the body would 403 every redemption."""

        async def _matching_request(request):
            request.state.bot_platform = "telegram"
            request.state.bot_platform_user_id = "TG42"

        with (
            patch(
                "app.api.v1.endpoints.bot_links.require_bot_api_key",
                new=AsyncMock(side_effect=_matching_request),
            ),
            patch(
                PEEK_PATCH,
                new_callable=AsyncMock,
                return_value=PlatformLinkCodePayload(user_id="user1", first_message=FIRST_MESSAGE),
            ),
            patch(DISCARD_PATCH, new_callable=AsyncMock),
            patch(COMPLETE_PATCH, new_callable=AsyncMock, return_value=_link_result()),
        ):
            response = await client.post(f"{BOT_BASE}/redeem-link-code", json=REDEEM_BODY)

        assert response.status_code == 200

    async def test_the_presented_code_is_the_one_redeemed_and_the_plan_is_checked(
        self, client: AsyncClient
    ):
        """The code is the credential and the plan check is the paywall: a call
        that loses either argument links the wrong person, or nobody's plan."""
        with (
            patch("app.api.v1.endpoints.bot_links.require_bot_api_key", new=AsyncMock()),
            patch(
                PEEK_PATCH,
                new_callable=AsyncMock,
                return_value=PlatformLinkCodePayload(user_id="user1", first_message=FIRST_MESSAGE),
            ) as mock_peek,
            patch(DISCARD_PATCH, new_callable=AsyncMock) as mock_discard,
            patch(
                "app.api.v1.endpoints.bot_links.require_platform_plan", new_callable=AsyncMock
            ) as mock_plan,
            patch(COMPLETE_PATCH, new_callable=AsyncMock, return_value=_link_result()),
        ):
            response = await client.post(f"{BOT_BASE}/redeem-link-code", json=REDEEM_BODY)

        assert response.status_code == 200
        mock_peek.assert_awaited_once_with("CODE123")
        mock_plan.assert_awaited_once_with("user1", "telegram")
        # Spent exactly once, and only after the link was written.
        mock_discard.assert_awaited_once_with("CODE123")

    @patch("app.api.v1.endpoints.bot_links.require_bot_api_key", new_callable=AsyncMock)
    async def test_a_plan_wall_leaves_the_code_live_for_the_retry(
        self, _auth: AsyncMock, client: AsyncClient
    ):
        """A lapsed user who taps the link, subscribes, and taps again must not
        be told the link expired: the wall refuses without spending the code."""
        with (
            patch(
                PEEK_PATCH,
                new_callable=AsyncMock,
                return_value=PlatformLinkCodePayload(user_id="user1", first_message=FIRST_MESSAGE),
            ),
            patch(DISCARD_PATCH, new_callable=AsyncMock) as mock_discard,
            patch(
                "app.api.v1.endpoints.bot_links.require_platform_plan",
                new=AsyncMock(
                    side_effect=AppError(message="Subscription required", status_code=402)
                ),
            ),
            patch(COMPLETE_PATCH, new_callable=AsyncMock) as mock_complete,
        ):
            response = await client.post(f"{BOT_BASE}/redeem-link-code", json=REDEEM_BODY)

        assert response.status_code == 402
        mock_complete.assert_not_awaited()
        mock_discard.assert_not_awaited()

    async def test_a_successful_redemption_stamps_the_wide_event_and_the_audit_trail(self):
        """Linking a platform account is an auth-grade event: the audit entry is
        the only record of which GAIA user claimed which handle, and the wide
        event is what makes the redemption findable at all."""
        body = RedeemLinkCodeRequest(platform="telegram", platform_user_id="TG42", code="CODE123")
        request = MagicMock()
        request.state = _make_request()

        with (
            patch("app.api.v1.endpoints.bot_links.require_bot_api_key", new=AsyncMock()),
            patch(
                PEEK_PATCH,
                new_callable=AsyncMock,
                return_value=PlatformLinkCodePayload(user_id="user1", first_message=FIRST_MESSAGE),
            ),
            patch(DISCARD_PATCH, new_callable=AsyncMock),
            patch("app.api.v1.endpoints.bot_links.require_platform_plan", new=AsyncMock()),
            patch(COMPLETE_PATCH, new_callable=AsyncMock, return_value=_link_result()),
        ):
            async with log_context("redeem_link_code_test"):
                result = await redeem_link_code(request, body)
                event = dict(log.get())

        assert result.linked is True
        assert event["operation"] == "redeem_link_code"
        assert event["platform"] == "telegram"
        assert event["user"] == {"id": "user1"}
        assert event["outcome"] == "success"
        assert event["is_new_link"] is True
        assert event["audit"] == [
            {
                "msg": "platform account linked via one-tap code",
                "actor": "user1",
                "resource": "TG42",
                "provider": "telegram",
            }
        ]

    async def test_a_rejected_code_is_audited_with_its_reason_and_never_the_code(self):
        """A probe hammering codes has to be findable, and the audit entry is the
        only place that records it — never carrying the code, which is the
        credential being guessed."""
        body = RedeemLinkCodeRequest(platform="telegram", platform_user_id="TG42", code="CODE123")
        request = MagicMock()
        request.state = _make_request()

        with (
            patch("app.api.v1.endpoints.bot_links.require_bot_api_key", new=AsyncMock()),
            patch(PEEK_PATCH, new_callable=AsyncMock, return_value=None),
            patch(DISCARD_PATCH, new_callable=AsyncMock),
        ):
            async with log_context("redeem_link_code_test"):
                with pytest.raises(AppError) as exc_info:
                    await redeem_link_code(request, body)
                event = dict(log.get())

        assert exc_info.value.status_code == 400
        assert event["audit"] == [
            {
                "msg": "platform link code rejected",
                "actor": AUDIT_ACTOR_BOT_API,
                "resource": "TG42",
                "provider": "telegram",
                "reason": "unknown_or_expired_code",
            }
        ]
        assert "CODE123" not in str(event)

    async def test_a_header_mismatch_is_audited_as_a_mismatch_not_a_bad_code(self):
        """Two rejections share one audit message, so `reason` is the only thing
        separating an expired link from an API key reaching for someone else's
        handle — the second is an attack, the first is a Tuesday."""
        body = RedeemLinkCodeRequest(platform="telegram", platform_user_id="TG42", code="CODE123")
        request = MagicMock()
        request.state = _make_request(bot_platform="telegram", bot_platform_user_id="SOMEONE_ELSE")

        with patch("app.api.v1.endpoints.bot_links.require_bot_api_key", new=AsyncMock()):
            async with log_context("redeem_link_code_test"):
                with pytest.raises(AppError) as exc_info:
                    await redeem_link_code(request, body)
                event = dict(log.get())

        assert exc_info.value.status_code == 403
        assert exc_info.value.message == "Request body does not match the authenticated bot headers"
        assert event["operation"] == "redeem_link_code"
        assert event["platform"] == "telegram"
        assert event["audit"] == [
            {
                "msg": "platform link code rejected",
                "actor": AUDIT_ACTOR_BOT_API,
                "resource": "TG42",
                "provider": "telegram",
                "reason": "platform_header_mismatch",
            }
        ]


# ---------------------------------------------------------------------------
# GET /bot/link-token-info/{token}
# ---------------------------------------------------------------------------


class TestGetLinkTokenInfo:
    """GET /api/v1/bot/link-token-info/{token}"""

    @patch("app.api.v1.endpoints.bot_links.redis_cache")
    async def test_link_token_info_success(
        self,
        mock_redis: MagicMock,
        client: AsyncClient,
    ):
        mock_redis.client.hgetall = AsyncMock(
            return_value={
                "platform": "discord",
                "username": "alice",
                "display_name": "Alice",
            }
        )
        response = await client.get(f"{BOT_BASE}/link-token-info/sometoken")
        assert response.status_code == 200
        data = response.json()
        assert data["platform"] == "discord"
        assert data["username"] == "alice"

    @patch("app.api.v1.endpoints.bot_links.redis_cache")
    async def test_link_token_info_not_found(
        self,
        mock_redis: MagicMock,
        client: AsyncClient,
    ):
        mock_redis.client.hgetall = AsyncMock(return_value={})
        response = await client.get(f"{BOT_BASE}/link-token-info/badtoken")
        assert response.status_code == 404
