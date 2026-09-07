"""Post-onboarding personalization service."""

from app.constants.log_tags import LogTag
from app.db.repositories.users import user_repository
from app.models.onboarding_models import ProfileCardDesign, UserProfileMetadata
from app.models.user_models import BioStatus
from app.services.system_workflows.provisioner import provision_universal_system_workflows
from app.utils.seeding_utils import seed_onboarding_todo
from shared.py.wide_events import log


async def save_personalization_data(
    user_id: str,
    card_design: ProfileCardDesign,
    metadata: UserProfileMetadata,
    personality_phrase: str,
    user_bio: str,
    bio_status: BioStatus,
) -> None:
    """Save the generated holo-card personalization bundle to the user document.

    The suggested workflows are not part of this bundle: they are persisted on
    their own by the workflows step, which finishes independently of the card.
    """
    try:
        await user_repository.save_personalization(
            user_id,
            house=card_design.house,
            personality_phrase=personality_phrase,
            user_bio=user_bio,
            bio_status=bio_status,
            account_number=metadata.account_number,
            member_since=metadata.member_since,
            overlay_color=card_design.overlay_color,
            overlay_opacity=card_design.overlay_opacity,
            workflow_ids=[],
        )
        log.info(f"{LogTag.ONBOARDING} Saved personalization data for user", user_id=user_id)

    except Exception as e:
        log.error(
            f"{LogTag.ONBOARDING} Error saving personalization data",
            error=str(e),
            error_type=type(e).__name__,
            user_id=user_id,
            exc_info=True,
        )


async def seed_initial_user_data(user_id: str) -> None:
    """Seed the onboarding todo and the universal system workflows. The welcome
    conversation is seeded by the intelligence pipeline, not here.

    Runs after complete_onboarding() has written the profile timezone, which is
    what the provisioner stamps onto the briefing schedules. Silent, like the
    per-integration provisioning during onboarding: the onboarding UI surfaces
    the workflows itself.
    """
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

    await provision_universal_system_workflows(user_id, notify=False)
