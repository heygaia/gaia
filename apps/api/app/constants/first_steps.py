"""Activation checklist ("first steps") constants."""

# The ``users`` subdocument holding the checklist's only persisted state — the
# dismissal. Every step's ``done`` is derived from a real signal at read time.
FIRST_STEPS_FIELD = "first_steps"
FIRST_STEPS_DISMISSED_FIELD = f"{FIRST_STEPS_FIELD}.dismissed"
FIRST_STEPS_DISMISSED_AT_FIELD = f"{FIRST_STEPS_FIELD}.dismissed_at"
