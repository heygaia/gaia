"""Unit tests for Agnost turn telemetry."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.services.agnost_service import begin_turn, end_turn


def _settings(org_id: str | None) -> SimpleNamespace:
    return SimpleNamespace(AGNOST_ORG_ID=org_id, AGNOST_ENDPOINT="https://api.agnost.ai")


class TestBeginTurn:
    def test_returns_none_when_org_id_missing(self) -> None:
        with (
            patch("app.services.agnost_service.settings", _settings(None)),
            patch("app.services.agnost_service.agnost") as mock_sdk,
        ):
            assert (
                begin_turn(
                    user_id="u1",
                    conversation_id="c1",
                    user_input="hello",
                )
                is None
            )
            mock_sdk.begin.assert_not_called()

    def test_returns_none_when_user_id_missing(self) -> None:
        with (
            patch("app.services.agnost_service.settings", _settings("org-1")),
            patch("app.services.agnost_service.agnost") as mock_sdk,
        ):
            assert (
                begin_turn(
                    user_id="",
                    conversation_id="c1",
                    user_input="hello",
                )
                is None
            )
            mock_sdk.begin.assert_not_called()

    def test_passes_real_ids_input_and_agent(self) -> None:
        interaction = MagicMock()
        with (
            patch("app.services.agnost_service.settings", _settings("org-1")),
            patch("app.services.agnost_service.agnost") as mock_sdk,
        ):
            mock_sdk.begin.return_value = interaction

            result = begin_turn(
                user_id="u1",
                conversation_id="c1",
                user_input="hello",
                properties={"source": "web"},
            )

            assert result is interaction
            kwargs = mock_sdk.begin.call_args.kwargs
            assert kwargs["user_id"] == "u1"
            assert kwargs["conversation_id"] == "c1"
            assert kwargs["input"] == "hello"
            assert kwargs["agent_name"] == "comms_agent"
            assert kwargs["properties"] == {"source": "web"}

    def test_sdk_failure_returns_none_without_raising(self) -> None:
        with (
            patch("app.services.agnost_service.settings", _settings("org-1")),
            patch("app.services.agnost_service.agnost") as mock_sdk,
        ):
            mock_sdk.begin.side_effect = RuntimeError("boom")

            assert (
                begin_turn(
                    user_id="u1",
                    conversation_id="c1",
                    user_input="hello",
                )
                is None
            )


class TestEndTurn:
    def test_none_interaction_is_noop(self) -> None:
        end_turn(None, output="hi", success=True)

    def test_closes_with_output_and_success(self) -> None:
        interaction = MagicMock()

        end_turn(interaction, output="hi", success=True)

        interaction.end.assert_called_once_with(output="hi", success=True)

    def test_failure_close_carries_success_false(self) -> None:
        interaction = MagicMock()

        end_turn(interaction, output="boom", success=False)

        interaction.end.assert_called_once_with(output="boom", success=False)

    def test_properties_merged_before_close(self) -> None:
        interaction = MagicMock()

        end_turn(interaction, output="hi", success=True, properties={"cancelled": True})

        interaction.set_properties.assert_called_once_with({"cancelled": True})
        interaction.end.assert_called_once_with(output="hi", success=True)

    def test_no_properties_skips_set_properties(self) -> None:
        interaction = MagicMock()

        end_turn(interaction, output="hi", success=True)

        interaction.set_properties.assert_not_called()
        interaction.end.assert_called_once_with(output="hi", success=True)

    def test_sdk_failure_does_not_raise(self) -> None:
        interaction = MagicMock()
        interaction.end.side_effect = RuntimeError("boom")

        end_turn(interaction, output="hi", success=True)
