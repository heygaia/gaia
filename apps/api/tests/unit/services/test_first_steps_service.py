"""The activation checklist derives every ``done`` from a real signal at read
time; only the dismissal is persisted. Repositories are the seams."""

from unittest.mock import AsyncMock, patch

import pytest

from app.models.first_steps_models import FirstStepKey, FirstStepsResponse, FirstStepsState
from app.models.user_models import UserDocument
from app.services.analytics_service import AnalyticsEvents
from app.services.first_steps_service import dismiss_first_steps, get_first_steps
from app.utils.errors import AppError

MODULE = "app.services.first_steps_service"
USER_ID = "507f1f77bcf86cd799439011"


def _user(**overrides: object) -> UserDocument:
    return UserDocument.model_validate({"id": USER_ID, "email": "test@example.com", **overrides})


@pytest.fixture
def repos():
    """Every signal false, user present, nothing dismissed — tests flip one at a time."""
    with (
        patch(f"{MODULE}.user_repository") as users,
        patch(f"{MODULE}.conversation_repository") as conversations,
        patch(f"{MODULE}.get_all_integrations_status", new_callable=AsyncMock) as integrations,
        patch(f"{MODULE}.workflow_repository") as workflows,
        patch(f"{MODULE}.capture_context_event") as capture,
    ):
        users.get = AsyncMock(return_value=_user())
        users.dismiss_first_steps = AsyncMock(return_value=True)
        conversations.has_sent_message = AsyncMock(return_value=False)
        integrations.return_value = {"gmail": False, "notion": False}
        workflows.count_for_user = AsyncMock(return_value=0)
        workflows.count_public_for_user = AsyncMock(return_value=0)
        yield {
            "users": users,
            "conversations": conversations,
            "integrations": integrations,
            "workflows": workflows,
            "capture": capture,
        }


def _done(response: FirstStepsResponse) -> dict[FirstStepKey, bool]:
    return {step.key: step.done for step in response.steps}


@pytest.mark.unit
class TestFirstStepKey:
    def test_members_in_checklist_order(self) -> None:
        assert [key.value for key in FirstStepKey] == [
            "say_hi",
            "connect_integration",
            "link_platform",
            "create_workflow",
            "publish_workflow",
        ]


@pytest.mark.unit
class TestGetFirstSteps:
    async def test_fresh_user_has_every_step_open_and_not_dismissed(self, repos) -> None:
        result = await get_first_steps(USER_ID)

        assert [step.key for step in result.steps] == list(FirstStepKey)
        assert _done(result) == dict.fromkeys(FirstStepKey, False)
        assert result.dismissed is False

    async def test_say_hi_is_the_sent_message_signal(self, repos) -> None:
        repos["conversations"].has_sent_message.return_value = True

        result = await get_first_steps(USER_ID)

        assert _done(result)[FirstStepKey.SAY_HI] is True
        repos["conversations"].has_sent_message.assert_awaited_once_with(USER_ID)

    async def test_connect_integration_counts_any_connected_integration(self, repos) -> None:
        repos["integrations"].return_value = {"gmail": False, "notion": True}

        result = await get_first_steps(USER_ID)

        assert _done(result)[FirstStepKey.CONNECT_INTEGRATION] is True
        repos["integrations"].assert_awaited_once_with(USER_ID)

    async def test_connect_integration_counts_gmail(self, repos) -> None:
        """Gmail is self-managed, so it only reads as connected through the
        canonical status map — a raw ``user_integrations`` count misses it."""
        repos["integrations"].return_value = {"gmail": True, "notion": False}

        assert _done(await get_first_steps(USER_ID))[FirstStepKey.CONNECT_INTEGRATION] is True

    async def test_link_platform_needs_a_link_with_an_id(self, repos) -> None:
        repos["users"].get.return_value = _user(platform_links={"telegram": {"id": "42"}})

        assert _done(await get_first_steps(USER_ID))[FirstStepKey.LINK_PLATFORM] is True

    async def test_link_platform_ignores_a_link_without_an_id(self, repos) -> None:
        repos["users"].get.return_value = _user(platform_links={"telegram": {"id": ""}})

        assert _done(await get_first_steps(USER_ID))[FirstStepKey.LINK_PLATFORM] is False

    async def test_create_workflow_excludes_todo_and_system_workflows(self, repos) -> None:
        repos["workflows"].count_for_user.return_value = 2

        result = await get_first_steps(USER_ID)

        assert _done(result)[FirstStepKey.CREATE_WORKFLOW] is True
        repos["workflows"].count_for_user.assert_awaited_once_with(
            USER_ID, exclude_todo_workflows=True, exclude_system_workflows=True
        )

    async def test_publish_workflow_is_a_public_workflow_of_the_user(self, repos) -> None:
        repos["workflows"].count_public_for_user.return_value = 1

        result = await get_first_steps(USER_ID)

        assert _done(result)[FirstStepKey.PUBLISH_WORKFLOW] is True
        repos["workflows"].count_public_for_user.assert_awaited_once_with(USER_ID)

    async def test_dismissed_is_read_from_the_user_document(self, repos) -> None:
        repos["users"].get.return_value = _user(first_steps=FirstStepsState(dismissed=True))

        assert (await get_first_steps(USER_ID)).dismissed is True

    async def test_missing_user_is_a_404(self, repos) -> None:
        repos["users"].get.return_value = None

        with pytest.raises(AppError) as excinfo:
            await get_first_steps(USER_ID)
        assert excinfo.value.status_code == 404


@pytest.mark.unit
class TestDismissFirstSteps:
    async def test_persists_the_dismissal_and_returns_the_checklist(self, repos) -> None:
        repos["users"].get.return_value = _user(first_steps=FirstStepsState(dismissed=True))
        repos["conversations"].has_sent_message.return_value = True

        result = await dismiss_first_steps(USER_ID)

        repos["users"].dismiss_first_steps.assert_awaited_once_with(USER_ID)
        assert result.dismissed is True
        assert _done(result)[FirstStepKey.SAY_HI] is True

    async def test_emits_the_dismiss_event_with_counts_only(self, repos) -> None:
        repos["users"].get.return_value = _user(
            first_steps=FirstStepsState(dismissed=True),
            platform_links={"telegram": {"id": "42"}},
        )
        repos["conversations"].has_sent_message.return_value = True

        await dismiss_first_steps(USER_ID)

        repos["capture"].assert_called_once_with(
            AnalyticsEvents.FIRST_STEPS_DISMISSED,
            {"steps_done": 2, "steps_total": len(FirstStepKey)},
        )

    async def test_missing_user_is_a_404_and_emits_nothing(self, repos) -> None:
        repos["users"].dismiss_first_steps.return_value = False

        with pytest.raises(AppError) as excinfo:
            await dismiss_first_steps(USER_ID)
        assert excinfo.value.status_code == 404
        repos["capture"].assert_not_called()
