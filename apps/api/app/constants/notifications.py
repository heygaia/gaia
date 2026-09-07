"""
Push Notification Constants
"""

from enum import StrEnum
import re

# Maximum devices a user can register for push notifications
MAX_DEVICES_PER_USER = 10

# Expo push token format: ExponentPushToken[xxx] or ExpoPushToken[xxx]
EXPO_TOKEN_PATTERN = re.compile(r"^Expo(nent)?PushToken\[[a-zA-Z0-9_-]+\]$")


class NotificationChannel(StrEnum):
    """Every surface a notification can be delivered on.

    Single source of truth: the preference model, the endpoint, the repository
    writes and the delivery-time preference lookup all derive from these members,
    so a new channel cannot be honoured by delivery while staying invisible in the
    API.
    """

    INAPP = "inapp"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    WHATSAPP = "whatsapp"
    SLACK = "slack"
    IMESSAGE = "imessage"
    EMAIL = "email"


# External channel types that are auto-injected based on platform links
EXTERNAL_NOTIFICATION_CHANNELS = (
    NotificationChannel.TELEGRAM,
    NotificationChannel.DISCORD,
    NotificationChannel.WHATSAPP,
    NotificationChannel.SLACK,
    NotificationChannel.IMESSAGE,
)

# All channel types that are auto-injected when no channels are explicitly specified.
# inapp is always available; the external platforms respect user preferences.
ALL_AUTO_INJECTED_CHANNELS = (NotificationChannel.INAPP, *EXTERNAL_NOTIFICATION_CHANNELS)

# Channels the user can switch on and off. inapp is excluded: it is always
# delivered, so it has no preference to store.
USER_CONFIGURABLE_CHANNELS = (*EXTERNAL_NOTIFICATION_CHANNELS, NotificationChannel.EMAIL)

# Default enabled state for every user-configurable channel
DEFAULT_CHANNEL_PREFERENCES: dict[str, bool] = {
    channel.value: True for channel in USER_CONFIGURABLE_CHANNELS
}

# Workflow-completion notification copy. GAIA texts like a friend (first person,
# casual), not a status bar. Each entry is (title, body); {title} is the workflow
# name. One pair is picked per run so repeats don't read like a robot. This is the
# in-app (web) heads-up and it carries a "View Results" button, so bodies stay warm
# and channel-agnostic: they never claim a specific place ("in your chat"), since a
# web user has no external chat and reaches the result through the button.
WORKFLOW_DONE_COPY: tuple[tuple[str, str], ...] = (
    ("sorted {title} for you", "it's all ready whenever you are 🙌"),
    ("{title} is done", "had a proper look — everything's ready for you"),
    ("just wrapped up {title}", "pulled it all together, take a peek"),
    ("handled {title} for you", "all done end to end, give it a look"),
    ("finished {title}", "got everything ready for you to check out"),
    ("{title}: all set", "took care of it, here's what I found"),
)


def pick_workflow_done_copy(workflow_id: str, title: str, salt: str) -> tuple[str, str]:
    """Pick one human completion title/body, rotating per run, no RNG.

    ``salt`` (a per-run value such as a timestamp) only seeds the rotation so the
    same workflow doesn't always read identically; it is never shown to the user.
    """
    seed = sum(ord(c) for c in f"{workflow_id}{salt}")
    title_tmpl, body = WORKFLOW_DONE_COPY[seed % len(WORKFLOW_DONE_COPY)]
    return title_tmpl.format(title=title), body
