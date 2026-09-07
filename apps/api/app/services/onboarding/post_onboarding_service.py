"""Post-onboarding data seeding."""

from app.constants.log_tags import LogTag
from app.utils.seeding_utils import seed_onboarding_todo
from shared.py.wide_events import log


async def seed_initial_user_data(user_id: str) -> None:
    """Seed the onboarding todo. The welcome conversation is seeded by the
    intelligence pipeline, not here."""
    try:
        log.info(f"{LogTag.ONBOARDING} Starting data seeding for user", user_id=user_id)
        await seed_onboarding_todo(user_id)
        log.info(f"{LogTag.ONBOARDING} Completed data seeding for user", user_id=user_id)

    except Exception as e:
        log.error(
            f"{LogTag.ONBOARDING} Error in seed_initial_user_data for user",
            user_id=user_id,
            error=str(e),
            error_type=type(e).__name__,
        )
