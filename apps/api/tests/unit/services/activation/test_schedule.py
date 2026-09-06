"""The next send is the user's local 8am, as a UTC instant, across DST."""

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.services.activation.schedule import SEND_HOUR_LOCAL, next_send_at


def _local(tz: str, *parts: int) -> datetime:
    return datetime(*parts, tzinfo=ZoneInfo(tz))


class TestNextSendAt:
    def test_before_eight_today_sends_today_at_eight_local(self) -> None:
        now = _local("Asia/Kolkata", 2026, 9, 7, 6, 30)
        assert next_send_at("Asia/Kolkata", now) == _local("Asia/Kolkata", 2026, 9, 7, 8, 0)

    def test_exactly_eight_is_not_today(self) -> None:
        now = _local("Asia/Kolkata", 2026, 9, 7, 8, 0)
        assert next_send_at("Asia/Kolkata", now) == _local("Asia/Kolkata", 2026, 9, 8, 8, 0)

    def test_after_eight_sends_tomorrow_at_eight_local(self) -> None:
        now = _local("America/New_York", 2026, 9, 7, 22, 15)
        assert next_send_at("America/New_York", now) == _local("America/New_York", 2026, 9, 8, 8, 0)

    def test_the_result_is_a_utc_instant(self) -> None:
        got = next_send_at("Asia/Kolkata", _local("Asia/Kolkata", 2026, 9, 7, 6, 30))
        # Identity, not equality: a same-offset stand-in for UTC is not UTC.
        assert got.tzinfo is UTC
        assert got == datetime(2026, 9, 7, 2, 30, tzinfo=UTC)

    def test_dst_end_keeps_eight_on_the_wall_clock(self) -> None:
        """New York falls back on 2026-11-01; the night before, 8am tomorrow is
        still 8am local, which is one UTC hour later than the day before."""
        before = next_send_at("America/New_York", _local("America/New_York", 2026, 10, 31, 9, 0))
        assert before == _local("America/New_York", 2026, 11, 1, 8, 0)
        assert before.astimezone(UTC).hour == 13
        day_before = next_send_at(
            "America/New_York", _local("America/New_York", 2026, 10, 30, 9, 0)
        )
        assert day_before.astimezone(UTC).hour == 12

    def test_dst_start_keeps_eight_on_the_wall_clock(self) -> None:
        """New York springs forward on 2026-03-08."""
        got = next_send_at("America/New_York", _local("America/New_York", 2026, 3, 7, 9, 0))
        assert got == _local("America/New_York", 2026, 3, 8, 8, 0)
        assert got.astimezone(UTC).hour == 12

    @pytest.mark.parametrize("raw", [None, "", "Not/AZone"])
    def test_no_usable_timezone_falls_back_to_utc(self, raw: str | None) -> None:
        now = datetime(2026, 9, 7, 9, 0, tzinfo=UTC)
        assert next_send_at(raw, now) == datetime(2026, 9, 8, 8, 0, tzinfo=UTC)

    def test_an_offset_timezone_is_honoured(self) -> None:
        now = datetime(2026, 9, 7, 0, 0, tzinfo=UTC)
        assert next_send_at("+05:30", now) == datetime(2026, 9, 7, 2, 30, tzinfo=UTC)

    def test_a_custom_hour(self) -> None:
        now = datetime(2026, 9, 7, 0, 0, tzinfo=UTC)
        assert next_send_at("UTC", now, hour=18) == datetime(2026, 9, 7, 18, 0, tzinfo=UTC)

    def test_a_naive_now_is_refused(self) -> None:
        with pytest.raises(ValueError, match="^next_send_at needs an aware datetime$"):
            next_send_at("UTC", datetime(2026, 9, 7, 9, 0))

    def test_the_default_hour_is_eight(self) -> None:
        assert SEND_HOUR_LOCAL == 8
        now = datetime(2026, 9, 7, 0, 0, tzinfo=UTC)
        assert next_send_at("UTC", now) == next_send_at("UTC", now, hour=8)

    def test_always_strictly_in_the_future(self) -> None:
        now = datetime(2026, 9, 7, 7, 59, 59, 999999, tzinfo=UTC)
        assert next_send_at("UTC", now) - now == timedelta(microseconds=1)
