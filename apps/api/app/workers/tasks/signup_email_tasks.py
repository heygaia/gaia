"""Signup's outbound ESP deliveries, as a durable ARQ job.

The welcome email and the marketing-audience contact are HTTP round-trips to an
external provider, so signup must not wait on them. Running them as an
in-process fire-and-forget task made signup fast but left the delivery with no
owner: nothing drains those tasks on shutdown, so an API restart mid-send
dropped both effects without even reaching their own failure loggers — the user
silently never got the founder email and never entered the nurture sequence.

Queued in Redis instead, the job outlives the process that enqueued it: ARQ only
removes a job from the queue once it finishes, so a worker that dies mid-send
leaves the job to be picked up and re-run.
"""

from __future__ import annotations

import asyncio
from typing import Any

from app.constants.log_tags import LogTag
from app.services.email import add_marketing_contact, send_welcome_email
from shared.py.wide_events import log

# Bounds each ESP round-trip on its own. Without it a provider that accepts the
# connection and never answers holds a worker slot for the job's whole timeout
# (30 minutes) and the other delivery is never reported either.
SIGNUP_EMAIL_TIMEOUT_SECONDS = 10


async def _send_welcome(user_id: str, email: str, signup_name: str) -> None:
    """Deliver the welcome email; a failure is recorded, never raised."""
    try:
        async with asyncio.timeout(SIGNUP_EMAIL_TIMEOUT_SECONDS):
            await send_welcome_email(email, signup_name, user_id=user_id)
        log.info(f"{LogTag.OAUTH} Welcome email sent to new user", user={"id": user_id})
    except Exception as e:
        log.error(
            f"{LogTag.OAUTH} Failed to send welcome email to",
            user={"id": user_id},
            error=str(e),
            error_type=type(e).__name__,
        )


async def _add_contact(user_id: str, email: str, signup_name: str) -> None:
    """Add the signup to the marketing audience; a failure is recorded, never raised."""
    try:
        async with asyncio.timeout(SIGNUP_EMAIL_TIMEOUT_SECONDS):
            await add_marketing_contact(email, signup_name, user_id=user_id)
        log.info(
            f"{LogTag.OAUTH} Contact added to marketing audience for new user",
            user={"id": user_id},
        )
    except Exception as e:
        log.error(
            f"{LogTag.OAUTH} Failed to add marketing contact for",
            user={"id": user_id},
            error=str(e),
            error_type=type(e).__name__,
        )


async def deliver_signup_emails(
    _ctx: dict[str, Any], user_id: str, email: str, signup_name: str
) -> str:
    """Run both signup deliveries concurrently; neither may fail the other.

    Both failure paths are swallowed on purpose: the account already exists, so
    there is nothing to roll back, and raising here would only make ARQ retry a
    welcome email the provider may well have already sent. The wide event is
    where a lost delivery is diagnosed.
    """
    await asyncio.gather(
        _send_welcome(user_id, email, signup_name),
        _add_contact(user_id, email, signup_name),
        return_exceptions=True,
    )
    return f"Signup deliveries attempted for {user_id}"
