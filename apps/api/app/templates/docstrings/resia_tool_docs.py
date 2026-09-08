"""Docstrings for Resia voice-call and SMS tools."""

PLACE_PHONE_CALL = """
Place a real outbound phone call via Resia (US/Canada numbers only).

Use when the user asks GAIA to call someone: bookings, stock checks,
confirmations, callbacks. The call is placed by the shared GAIA voice agent:
it announces itself as an AI on a recorded line, names on_behalf_of, works
the objective using only the facts given, and never invents details.

Args:
    to_phone_number (str): Destination in E.164, e.g. +14155550123. US/CA only.
    objective (str): What to accomplish, briefed like a person: goal, facts
        the agent may state, and acceptable fallbacks.
    on_behalf_of (str): Person the agent says it is calling for.
    from_phone_number (str | None): Owned sender override. Unset = default.
    client_reference (str | None): Opaque dedupe label. Unset = auto.

Returns:
    dict with call_id and status (queued). The call has NOT happened yet;
    use get_phone_call_status to follow it. Costs real money on completion.
"""

GET_PHONE_CALL_STATUS = """
Read one Resia call: status, outcome, summary, transcript, cost.

Use after place_phone_call to follow a call. Resia has no long-poll: call
this again while status is queued/initiated/in_progress/post_processing.
Terminal states are completed/error/canceled. On completed, outcome is one
of achieved/partial/not_achieved/unclear with a summary and transcript.
On error, failure_code says why (nothing charged).

Args:
    call_id (str): The id place_phone_call returned.

Returns:
    dict with status, outcome, summary, transcript, duration_secs,
    charged_cents and failure_code.
"""

SEND_SMS = """
Send a real SMS via Resia to 1-100 US/Canada recipients (same body each).

Use when the user asks GAIA to text someone. Requires an owned sender
number and completed 10DLC registration — failures name the missing piece.
Every recipient is judged alone: bad numbers land in rejected, the rest send.

Args:
    to_phone_numbers (list[str]): Destinations in E.164. Max 100 per call.
    message (str): The one body every recipient gets (max 1600 chars).
    from_phone_number (str | None): Owned sender override. Unset = default.

Returns:
    dict with batch_id, per-message ids/statuses and rejected entries.
    Follow delivery with get_sms_status. Costs real money per segment.
"""

GET_SMS_STATUS = """
Read one Resia SMS batch: derived status plus per-state counts.

Use after send_sms. Batch status is in_progress until every message settles,
then completed (or canceled). Counts cover queued/sent/delivered/
delivery_unconfirmed/failed/canceled. Includes the first page of messages.

Args:
    batch_id (str): The id send_sms returned.

Returns:
    dict with status, counts, total and messages.
"""
