"""Unit tests for user Pydantic models."""

from pydantic import ValidationError
import pytest

from app.models.user_models import OnboardingNeed, OnboardingPreferences, OnboardingRequest

# ---------------------------------------------------------------------------
# OnboardingRequest.validate_timezone
# ---------------------------------------------------------------------------


class TestOnboardingRequestTimezone:
    """The ``timezone`` field validator now delegates to the canonical
    ``is_valid_timezone`` — it accepts IANA names, ±HH:MM offsets and UTC,
    rejects junk, and passes None/empty through."""

    def _build(self, timezone) -> OnboardingRequest:
        return OnboardingRequest(
            profession="Engineer",
            needs=["inbox"],
            timezone=timezone,
        )

    @pytest.mark.parametrize(
        "tz",
        ["Asia/Kolkata", "America/New_York", "+05:30", "-08:00", "UTC", "utc"],
    )
    def test_valid_timezone_preserved(self, tz):
        m = self._build(tz)
        assert m.timezone == tz

    def test_valid_timezone_is_stripped(self):
        m = self._build("  Asia/Kolkata  ")
        assert m.timezone == "Asia/Kolkata"

    @pytest.mark.parametrize(
        "tz",
        ["Not/AZone", "Mars/Phobos", "+5:30"],
    )
    def test_invalid_timezone_raises(self, tz):
        with pytest.raises(ValidationError):
            self._build(tz)

    def test_none_timezone_allowed(self):
        m = self._build(None)
        assert m.timezone is None

    def test_empty_timezone_allowed(self):
        m = self._build("")
        assert m.timezone == ""


@pytest.mark.unit
class TestStoredPreferencesFromBeforeTheQ2Rewrite:
    """Users who onboarded before the pain-based Q2 hold need values that no
    longer exist ("todos", "briefings", "reach") and up to seven picks. Their
    document is read back on every /user/me, at seeding, in the activation
    context and by account_fs, so it must always load; strictness belongs to
    the request model, not the stored one."""

    def test_unknown_need_values_are_dropped_in_order(self) -> None:
        prefs = OnboardingPreferences.model_validate(
            {"profession": "founder", "needs": ["todos", "inbox", "briefings", "calendar"]}
        )

        assert prefs.needs == [OnboardingNeed.INBOX, OnboardingNeed.CALENDAR]

    def test_more_picks_than_the_cap_keep_the_first_ones(self) -> None:
        prefs = OnboardingPreferences.model_validate(
            {"profession": "founder", "needs": ["inbox", "calendar", "reminders", "tools"]}
        )

        assert prefs.needs == [OnboardingNeed.INBOX, OnboardingNeed.CALENDAR]

    def test_only_unknown_values_leaves_no_picks(self) -> None:
        prefs = OnboardingPreferences.model_validate({"profession": "founder", "needs": ["memory"]})

        assert prefs.needs == []

    def test_the_request_model_still_rejects_an_unknown_need(self) -> None:
        with pytest.raises(ValidationError):
            OnboardingRequest(profession="founder", needs=["todos"])
