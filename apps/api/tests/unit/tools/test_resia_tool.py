"""Unit tests for app.agents.tools.resia_tool."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas.resia_schemas import CallPlaced, CallRead, TextBatchPlaced
from app.services.resia_service import ResiaError

FAKE_USER_ID = "507f1f77bcf86cd799439011"

MODULE = "app.agents.tools.resia_tool"


def _make_config(user_id: str = FAKE_USER_ID) -> dict[str, Any]:
    return {"metadata": {"user_id": user_id}}


def _placed() -> CallPlaced:
    return CallPlaced.model_validate(
        {
            "id": "call-1",
            "status": "queued",
            "created_at": "2026-09-08T17:57:38.921+00:00",
            "call_agent_version_id": "v1",
        }
    )


class TestPlacePhoneCall:
    @patch(f"{MODULE}.get_stream_writer")
    @patch(f"{MODULE}.resia_service.place_call", new_callable=AsyncMock)
    async def test_streams_card_and_returns_id(
        self, mock_place: AsyncMock, mock_writer_factory: MagicMock
    ) -> None:
        writer = MagicMock()
        mock_writer_factory.return_value = writer
        mock_place.return_value = _placed()

        from app.agents.tools.resia_tool import place_phone_call

        result = await place_phone_call.coroutine(
            config=_make_config(),
            to_phone_number="+14155550123",
            objective="Book a table",
            on_behalf_of="Alex",
        )

        assert result["call_id"] == "call-1"
        assert result["status"] == "queued"
        mock_place.assert_awaited_once_with(
            "+14155550123", "Book a table", "Alex", FAKE_USER_ID, None, None
        )
        card = writer.call_args[0][0]["phone_call_data"]
        assert card["call_id"] == "call-1"

    @patch(f"{MODULE}.get_stream_writer")
    @patch(f"{MODULE}.resia_service.place_call", new_callable=AsyncMock)
    async def test_missing_user_never_dials(
        self, mock_place: AsyncMock, mock_writer_factory: MagicMock
    ) -> None:
        from app.agents.tools.resia_tool import place_phone_call

        result = await place_phone_call.coroutine(
            config={"metadata": {}},
            to_phone_number="+14155550123",
            objective="Book a table",
            on_behalf_of="Alex",
        )

        assert result["error"] == "User authentication required"
        mock_place.assert_not_awaited()
        mock_writer_factory.assert_not_called()

    @patch(f"{MODULE}.get_stream_writer")
    @patch(f"{MODULE}.resia_service.place_call", new_callable=AsyncMock)
    async def test_rate_limit_hint_names_wait(
        self, mock_place: AsyncMock, mock_writer_factory: MagicMock
    ) -> None:
        mock_writer_factory.return_value = MagicMock()
        mock_place.side_effect = ResiaError("rate_limited", "Slow down", "req-1", 429, 7)

        from app.agents.tools.resia_tool import place_phone_call

        result = await place_phone_call.coroutine(
            config=_make_config(),
            to_phone_number="+14155550123",
            objective="Book a table",
            on_behalf_of="Alex",
        )

        assert "Retry after 7s" in result["error"]


class TestGetPhoneCallStatus:
    @patch(f"{MODULE}.get_stream_writer")
    @patch(f"{MODULE}.resia_service.get_call", new_callable=AsyncMock)
    async def test_returns_terminal_result(
        self, mock_get: AsyncMock, mock_writer_factory: MagicMock
    ) -> None:
        mock_get.return_value = CallRead.model_validate(
            {
                "id": "call-1",
                "status": "completed",
                "created_at": "2026-09-08T17:57:38.921+00:00",
                "call_agent_version_id": "v1",
                "to_phone_number": "+14155550123",
                "outcome": "achieved",
                "summary": "Booked.",
                "transcript": [{"role": "assistant", "content": "Hi"}],
            }
        )

        from app.agents.tools.resia_tool import get_phone_call_status

        result = await get_phone_call_status.coroutine(config=_make_config(), call_id="call-1")

        assert result["outcome"] == "achieved"
        assert result["transcript"] == [{"role": "assistant", "content": "Hi"}]
        mock_writer_factory.assert_not_called()


class TestSendSms:
    @patch(f"{MODULE}.get_stream_writer")
    @patch(f"{MODULE}.resia_service.send_text_batch", new_callable=AsyncMock)
    async def test_maps_messages_and_rejected_positions(
        self, mock_send: AsyncMock, mock_writer_factory: MagicMock
    ) -> None:
        writer = MagicMock()
        mock_writer_factory.return_value = writer
        mock_send.return_value = TextBatchPlaced.model_validate(
            {
                "id": "batch-1",
                "status": "in_progress",
                "text_messages": [
                    {
                        "text_message_id": "msg-1",
                        "to_phone_number": "+14155550123",
                        "status": "queued",
                        "created_at": "2026-09-08T17:57:38.921+00:00",
                    }
                ],
                "rejected_text_messages": [
                    {"position": 1, "to_phone_number": "+14155550123", "reason": "Duplicate"}
                ],
            }
        )

        from app.agents.tools.resia_tool import send_sms

        result = await send_sms.coroutine(
            config=_make_config(),
            to_phone_numbers=["+14155550123", "+14155550123"],
            message="Hi",
        )

        assert result["batch_id"] == "batch-1"
        assert result["recipient_count"] == 1
        assert result["rejected"] == [
            {"to_phone_number": "+14155550123", "reason": "Duplicate", "position": 1}
        ]
        card = writer.call_args[0][0]["sms_data"]
        assert card["batch_id"] == "batch-1"
