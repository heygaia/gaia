"""Resia (voice calls + SMS) constants."""

RESIA_BASE_URL = "https://api.resia.ai"
RESIA_TIMEOUT_SECONDS = 30

E164_RE = r"^\+[1-9]\d{7,14}$"

# Resia dials United States and Canada only.
US_CA_PREFIX = "+1"

TERMINAL_CALL_STATUSES = frozenset({"completed", "error", "canceled"})

SMS_MAX_CHARS = 1600
MAX_SMS_RECIPIENTS = 100
