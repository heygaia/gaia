"""The first-steps contract: a GET that derives the checklist and a POST that
collapses or expands it. There is deliberately no route that marks a step done."""

from unittest.mock import AsyncMock, patch

from httpx import AsyncClient
import pytest

from app.models.first_steps_models import FirstStep, FirstStepKey, FirstStepsResponse
from app.utils.errors import AppError
from tests.conftest import FAKE_USER

URL = "/api/v1/user/first-steps"
USER_ID = FAKE_USER["user_id"]
MODULE = "app.api.v1.endpoints.first_steps"


def _checklist(*, collapsed: bool) -> FirstStepsResponse:
    return FirstStepsResponse(
        steps=[FirstStep(key=key, done=key is FirstStepKey.SAY_HI) for key in FirstStepKey],
        collapsed=collapsed,
    )


@pytest.mark.unit
class TestGetFirstSteps:
    async def test_returns_the_derived_checklist(self, client: AsyncClient) -> None:
        with patch(
            f"{MODULE}.get_first_steps",
            new_callable=AsyncMock,
            return_value=_checklist(collapsed=False),
        ) as read:
            resp = await client.get(URL)

        assert resp.status_code == 200
        assert resp.json() == {
            "steps": [
                {"key": "say_hi", "done": True},
                {"key": "connect_integration", "done": False},
                {"key": "link_platform", "done": False},
                {"key": "create_workflow", "done": False},
            ],
            "collapsed": False,
        }
        read.assert_awaited_once_with(USER_ID)

    async def test_missing_user_is_a_404(self, client: AsyncClient) -> None:
        with patch(
            f"{MODULE}.get_first_steps",
            new_callable=AsyncMock,
            side_effect=AppError(message="User not found", status_code=404),
        ):
            resp = await client.get(URL)

        assert resp.status_code == 404

    async def test_requires_auth(self, unauthed_client: AsyncClient) -> None:
        resp = await unauthed_client.get(URL)
        assert resp.status_code == 401


@pytest.mark.unit
class TestCollapseFirstSteps:
    @pytest.mark.parametrize("collapsed", [True, False])
    async def test_persists_either_direction_and_returns_the_checklist(
        self, client: AsyncClient, collapsed: bool
    ) -> None:
        with patch(
            f"{MODULE}.set_first_steps_collapsed",
            new_callable=AsyncMock,
            return_value=_checklist(collapsed=collapsed),
        ) as persist:
            resp = await client.post(f"{URL}/collapse", json={"collapsed": collapsed})

        assert resp.status_code == 200
        assert resp.json()["collapsed"] is collapsed
        assert [step["key"] for step in resp.json()["steps"]] == [key.value for key in FirstStepKey]
        persist.assert_awaited_once_with(USER_ID, collapsed)

    async def test_a_missing_body_is_a_422(self, client: AsyncClient) -> None:
        resp = await client.post(f"{URL}/collapse")
        assert resp.status_code == 422

    async def test_requires_auth(self, unauthed_client: AsyncClient) -> None:
        resp = await unauthed_client.post(f"{URL}/collapse", json={"collapsed": True})
        assert resp.status_code == 401

    async def test_there_is_no_route_that_marks_a_step_done(self, client: AsyncClient) -> None:
        resp = await client.patch(URL, json={"key": "say_hi", "done": True})
        assert resp.status_code == 405
