"""One day of the activation sequence: one user, one message, one platform.

Enqueued deferred to the user's next 08:00 local — first by onboarding
completion, then by each run for the day after. Nothing sweeps: a cron over
every user would fire five times a day for people who finished the sequence
weeks ago, and the send hour is per-user anyway.

The order inside a run is the whole design. Read, decide, claim, write, deliver,
record. Every stop condition is evaluated before the model call, so a skipped
day costs a handful of reads. The claim is taken before the send and released
when the send fails, so a redelivered ARQ job is a no-op but a broker outage
still gets a real retry.
"""

from datetime import UTC, datetime
from typing import Any

from app.db.redis import redis_cache
from app.db.repositories.users import user_repository
from app.models.activation_models import ActivationMessage
from app.models.chat_models import ConversationSource
from app.services.activation import context
from app.services.activation.copy import ActivationCopyError, draft_message
from app.services.activation.policy import (
    SEQUENCE_LENGTH,
    ActivationBrief,
    claim_key,
    direction,
    skip_reason,
)
from app.services.activation.schedule import next_send_at
from app.services.analytics_service import AnalyticsEvents, capture_event
from app.services.delivery import chat_sync
from app.services.outbound_delivery import OutboundResult, publish_outbound_message
from app.utils.redis_utils import RedisPoolManager
from app.workers.queue import enqueue_worker_job
from shared.py.wide_events import log

#: ARQ task name. One constant so the enqueue sites and the registration cannot
#: drift into a job nobody consumes.
ACTIVATION_TASK = "send_activation_message"
#: How long a day's claim stays in Redis. Longer than the gap between a send and
#: any plausible ARQ redelivery, shorter than forever: the user document is the
#: durable record, this key only stops a double send.
CLAIM_TTL_SECONDS = 172_800  # 48 hours


class ActivationDeliveryError(Exception):
    """The message could not be published. ARQ retries; the day stays unclaimed."""


async def _claim(user_id: str, day: int) -> bool:
    """Take the once-per-day send claim. ``False`` means someone else has it."""
    return bool(
        await redis_cache.client.set(claim_key(user_id, day), "1", nx=True, ex=CLAIM_TTL_SECONDS)
    )


async def _release(user_id: str, day: int) -> None:
    await redis_cache.client.delete(claim_key(user_id, day))


async def enqueue_next_day(user_id: str, day: int, timezone_raw: str | None, now: datetime) -> None:
    """Defer day ``day`` to the user's next 08:00 local.

    The job id is per user per day, so a duplicate enqueue (a replayed
    onboarding completion, an ARQ retry that already scheduled tomorrow) is
    deduped by ARQ rather than producing two messages.
    """
    if day >= SEQUENCE_LENGTH:
        return
    pool = await RedisPoolManager.get_pool()
    await enqueue_worker_job(
        pool,
        ACTIVATION_TASK,
        user_id,
        day,
        _job_id=f"{ACTIVATION_TASK}:{user_id}:{day}",
        _defer_until=next_send_at(timezone_raw, now),
    )


def _skip(user_id: str, day: int, reason: str) -> str:
    log.set(skipped=reason)
    capture_event(user_id, AnalyticsEvents.ACTIVATION_DAY_SKIPPED, {"day": day, "reason": reason})
    return f"skip {user_id} day {day}: {reason}"


async def send_activation_message(ctx: dict[str, Any], user_id: str, day: int) -> str:  # noqa: ARG001 -- ARQ injects ctx positionally into every registered task
    """Send day ``day`` of the activation sequence, or skip it with a reason."""
    log.set(user_id=user_id, user={"id": user_id}, activation_day=day)
    now = datetime.now(UTC)

    user = await user_repository.get(user_id)
    if user is None:
        return _skip(user_id, day, "unknown_user")

    run = await context.gather(user, now)
    stop = skip_reason(run.facts)
    if stop is not None:
        # A terminal reason ends the sequence; "they were active today" is just
        # today, so tomorrow is still scheduled and the day is not counted.
        if stop is stop.USER_ACTIVE_TODAY:
            await enqueue_next_day(user_id, day, user.timezone, now)
        return _skip(user_id, day, stop)

    # ``platform`` is not None here: has_channel is a stop condition above.
    platform = run.platform
    assert platform is not None
    source = ConversationSource.coerce(platform)
    if source is None:
        return _skip(user_id, day, "unsupported_platform")

    today = direction(run.facts)
    log.set(direction=today, platform=platform)

    if not await _claim(user_id, day):
        return _skip(user_id, day, "already_claimed")

    try:
        draft = await draft_message(
            ActivationBrief(day=day, direction=today, blocks=run.blocks),
            earlier=run.state.earlier_drafts(),
        )
    except ActivationCopyError as e:
        # The claim stays: a day whose copy could not be written is spent, not
        # retried into a second model bill for the same morning.
        log.set(copy_error=str(e))
        await enqueue_next_day(user_id, day + 1, user.timezone, now)
        return _skip(user_id, day, "copy_failed")

    result = await publish_outbound_message(source, user_id, draft.bubbles)
    if result is not OutboundResult.PUBLISHED:
        await _release(user_id, day)
        if result is OutboundResult.FAILED:
            raise ActivationDeliveryError(f"activation publish failed for {user_id} on {platform}")
        return _skip(user_id, day, "publish_skipped")

    message = ActivationMessage(
        day=day,
        direction=today,
        platform=platform,
        sent_at=now,
        bubbles=draft.bubbles,
        suggestion=draft.suggestion,
        connect_target=draft.connect_target,
    )
    # The bot never sees GAIA's outbound in its own history, so the reply to
    # this message would otherwise arrive with no context at all.
    await chat_sync.persist_bot_message(user_id, user.model_dump(), platform, draft.bubbles)
    await user_repository.record_activation_message(user_id, message)
    capture_event(
        user_id,
        AnalyticsEvents.ACTIVATION_DAY_SENT,
        {"day": day, "platform": platform, "direction": today},
    )
    await enqueue_next_day(user_id, day + 1, user.timezone, now)
    log.set(bubbles=len(draft.bubbles))
    return f"sent activation day {day} to {user_id} on {platform}"
