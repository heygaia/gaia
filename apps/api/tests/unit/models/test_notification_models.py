"""Notification model invariants.

The channel set is defined once, in ``NotificationChannel``. These tests are what
stops the preference model, the stored defaults and the enum from drifting apart —
which is exactly how ``imessage`` and ``email`` ended up honoured by delivery while
being invisible to the API.
"""

from app.constants.notifications import (
    DEFAULT_CHANNEL_PREFERENCES,
    DEFAULT_CHAT_CHANNEL_PRIORITY,
    EXTERNAL_NOTIFICATION_CHANNELS,
    USER_CONFIGURABLE_CHANNELS,
    NotificationChannel,
)
from app.models.notification.notification_models import (
    ChannelPreferences,
    ChannelPreferencesUpdate,
)

CONFIGURABLE_CHANNEL_VALUES = {channel.value for channel in USER_CONFIGURABLE_CHANNELS}


class TestChannelSetIsSingleSourced:
    def test_configurable_channels_are_every_channel_but_inapp(self):
        assert {channel.value for channel in NotificationChannel} - {
            NotificationChannel.INAPP.value
        } == CONFIGURABLE_CHANNEL_VALUES

    def test_defaults_cover_every_configurable_channel(self):
        assert set(DEFAULT_CHANNEL_PREFERENCES) == CONFIGURABLE_CHANNEL_VALUES

    def test_response_model_exposes_every_configurable_channel(self):
        assert set(ChannelPreferences.model_fields) == CONFIGURABLE_CHANNEL_VALUES

    def test_update_model_accepts_every_configurable_channel(self):
        assert set(ChannelPreferencesUpdate.model_fields) == CONFIGURABLE_CHANNEL_VALUES

    def test_update_model_omits_unset_channels(self):
        update = ChannelPreferencesUpdate(imessage=False)
        assert update.model_dump(exclude_none=True) == {"imessage": False}

    def test_briefing_priority_covers_every_chat_platform(self):
        """A chat platform missing here can never receive a briefing.

        The briefing picks ONE platform by walking this order, so a channel the
        user has linked and enabled but that is absent from the list is silently
        skipped — an iMessage-only user got no brief at all.
        """
        assert set(DEFAULT_CHAT_CHANNEL_PRIORITY) == {
            channel.value for channel in EXTERNAL_NOTIFICATION_CHANNELS
        }
