"""GAIA's whole first contact on a freshly linked platform, composed by the server.

Deterministic and LLM-free, by decision. The first version handed the composed
opener to the model as a normal turn and asked the prompt for the shape; live
runs showed it skipping the per-pick lines, delegating to the executor, and
sometimes never producing the connect links at all. The one message a user is
guaranteed to read is not something to leave to sampling.

The shape, in order, one bubble each:

1. the hello (:func:`compose_link_greeting`),
2. one line per thing they picked — their problem, then what GAIA will do,
3. the first move: the connect links those picks need, or the offer to start.

The rules of the voice apply here as everywhere (``agents/prompts/comms_prompts``):
short lines, plain words, no exclamation marks, no emoji, never a feature list.
"""

from app.config.oauth_config import get_integration_by_id
from app.db.repositories.user_integrations import user_integration_repository
from app.models.user_models import OnboardingNeed, OnboardingPreferences
from app.services.connect_link_service import build_connect_link_url

#: The hello a bot sends the moment a link code is redeemed. Deterministic and
#: server-owned because a first contact that opens on a restatement of the
#: user's onboarding picks reads like a machine resuming a thread they never
#: started.
LINK_GREETING_WITH_NAME = "Hey {name}. I'm with you on {platform} now."
#: Same line with the name clause dropped: greeting a blank is worse than not
#: using a name at all.
LINK_GREETING = "Hey. I'm with you on {platform} now."


def compose_link_greeting(platform: str, name: str | None) -> str:
    """GAIA's hello on a freshly linked platform.

    ``name`` is the GAIA user's full name; only the first token is used, because
    a greeting that says the surname is an email, not a text.
    """
    from app.services.onboarding.first_conversation import (  # noqa: PLC0415 -- first_conversation imports the onboarding package for its phrases; a top-level import back would be a cycle
        platform_label,
    )

    label = platform_label(platform)
    tokens = (name or "").split()
    if tokens:
        return LINK_GREETING_WITH_NAME.format(name=tokens[0], platform=label)
    return LINK_GREETING.format(platform=label)


#: One promise per pick: their problem in GAIA's words, then the thing GAIA will
#: do about it. Second person, two short sentences, present problem then future
#: promise — the shape Aryan asked for ("since you face X, I'll do Y"), written
#: as speech rather than as that literal template.
#:
#: Every member of ``OnboardingNeed`` has an entry and a drift test enforces it:
#: a need with no promise renders as a silently skipped pick, which is the one
#: failure this whole module exists to stop.
NEED_PROMISES: dict[OnboardingNeed, str] = {
    OnboardingNeed.INBOX: (
        "Your inbox is out of control. Every morning I'll have it sorted and the replies drafted."
    ),
    OnboardingNeed.CALENDAR: "You walk into meetings cold. I'll brief you before each one.",
    OnboardingNeed.MORNINGS: "Mornings start behind. You'll get a brief before the day does.",
    OnboardingNeed.REMINDERS: "Things slip. Tell me once and I'll remind you when it matters.",
    OnboardingNeed.GRUNT_WORK: "Grunt work eats your week. Hand it to me and it's done.",
    OnboardingNeed.TOOLS: (
        "You live in too many tools. Name the one you're in most and I'll run it from here."
    ),
    OnboardingNeed.FOUNDER_TEAM_UPDATES: (
        "You chase your team for updates. I'll bring you what moved, every day."
    ),
    OnboardingNeed.FOUNDER_COMPETITORS: (
        "Nobody is watching your competitors. I'll track them and tell you what changed."
    ),
    OnboardingNeed.EXECUTIVE_REPORTS: (
        "Reports pile up unread. I'll cut each one to a page with the numbers that moved."
    ),
    OnboardingNeed.EXECUTIVE_DECISIONS: (
        "Decisions pile up on you. I'll bring you the blocked ones with enough context to "
        "decide in one read."
    ),
    OnboardingNeed.SALES_LEADS: (
        "Leads go cold. I'll hold the open deals and nudge you the moment one goes quiet."
    ),
    OnboardingNeed.SALES_CALL_RESEARCH: (
        "You research before every call. I'll have the brief waiting before you dial."
    ),
    OnboardingNeed.PRODUCT_FEEDBACK: (
        "Feedback is scattered. I'll gather it into one digest, grouped by theme."
    ),
    OnboardingNeed.PRODUCT_SPECS: (
        "Specs take forever. I'll draft the next one from the feedback and you edit it."
    ),
    OnboardingNeed.MARKETING_CONTENT: (
        "Content is always behind. I'll draft the next piece ahead of its slot, in your voice."
    ),
    OnboardingNeed.MARKETING_REPORTS: (
        "You build the same report by hand. I'll write it on schedule from your numbers."
    ),
    OnboardingNeed.ENGINEERING_PRS: (
        "PRs wait on you. I'll list what needs your review, with a summary of each."
    ),
    OnboardingNeed.ENGINEERING_NOTIFICATIONS: (
        "Notifications drown you. I'll turn them into one digest a day, only what needs you."
    ),
    OnboardingNeed.FINANCE_NUMBERS: (
        "You chase people for numbers. I'll do the chasing and track who has sent."
    ),
    OnboardingNeed.FINANCE_REPORTS: (
        "The same report every week. I'll draft it on schedule and flag what changed."
    ),
    OnboardingNeed.CREATIVE_REVISIONS: (
        "Revisions pile up. I'll gather every one into a single list, open versus done."
    ),
    OnboardingNeed.CREATIVE_DEADLINES: (
        "Deadlines sneak up. I'll hold them for you and warn you early."
    ),
    OnboardingNeed.STUDENT_ASSIGNMENTS: (
        "Assignments pile up. I'll hold them with their due dates and nudge you before each one."
    ),
    OnboardingNeed.STUDENT_EXAMS: (
        "Exams arrive before you're ready. I'll turn your notes into a study digest and "
        "practice questions."
    ),
}

#: Their own words under "Something else". No promise exists for it, so GAIA
#: says it back and commits, rather than inventing a plan for text nobody parsed.
OTHER_NEED_PROMISE = 'You said: "{other_need}". I\'ll take that on too.'

#: What each pick actually needs switched on, in ``OAUTH_INTEGRATIONS`` ids.
#: Derived from ``NEED_PLAYBOOKS`` in ``agents/prompts/new_user_prompts``: a pick
#: whose playbook opens by ASKING where the work lives (which tool, where
#: feedback lands, which notifications are loudest) has no entry here, because
#: minting a connect link for a guess is a link the user has no reason to tap.
NEED_INTEGRATIONS: dict[OnboardingNeed, tuple[str, ...]] = {
    OnboardingNeed.INBOX: ("gmail",),
    OnboardingNeed.CALENDAR: ("googlecalendar",),
    OnboardingNeed.MORNINGS: ("gmail", "googlecalendar"),
    OnboardingNeed.REMINDERS: ("googlecalendar",),
    OnboardingNeed.GRUNT_WORK: (),
    OnboardingNeed.TOOLS: (),
    OnboardingNeed.FOUNDER_TEAM_UPDATES: ("slack",),
    OnboardingNeed.FOUNDER_COMPETITORS: (),
    OnboardingNeed.EXECUTIVE_REPORTS: (),
    OnboardingNeed.EXECUTIVE_DECISIONS: ("slack", "gmail"),
    OnboardingNeed.SALES_LEADS: ("gmail",),
    OnboardingNeed.SALES_CALL_RESEARCH: ("googlecalendar",),
    OnboardingNeed.PRODUCT_FEEDBACK: (),
    OnboardingNeed.PRODUCT_SPECS: ("notion",),
    OnboardingNeed.MARKETING_CONTENT: (),
    OnboardingNeed.MARKETING_REPORTS: (),
    OnboardingNeed.ENGINEERING_PRS: ("github",),
    OnboardingNeed.ENGINEERING_NOTIFICATIONS: (),
    OnboardingNeed.FINANCE_NUMBERS: ("slack", "gmail"),
    OnboardingNeed.FINANCE_REPORTS: (),
    OnboardingNeed.CREATIVE_REVISIONS: (),
    OnboardingNeed.CREATIVE_DEADLINES: ("googlecalendar",),
    OnboardingNeed.STUDENT_ASSIGNMENTS: ("googlecalendar",),
    OnboardingNeed.STUDENT_EXAMS: (),
}

#: Counts spelled out, because "2 taps" in a text message reads like a receipt.
#: Beyond three the digit is clearer than the word anyway.
_TAP_COUNTS = {1: "One", 2: "Two", 3: "Three"}

#: No links to hand over: the first move is still GAIA's to offer, and a first
#: contact that ends on the promises alone ends on nothing to say yes to.
NO_LINKS_LINE = "Say the word and I'll start."


def needed_integration_ids(preferences: OnboardingPreferences) -> list[str]:
    """The integrations this user's picks need, deduped, in the order they picked.

    Pick order matters: the first thing they tapped is the thing they came for,
    so its connect link is the first one they see.
    """
    seen: list[str] = []
    for need in preferences.needs or []:
        for integration_id in NEED_INTEGRATIONS.get(need, ()):
            if integration_id not in seen:
                seen.append(integration_id)
    return seen


def _integration_display_name(integration_id: str) -> str:
    """The name the OAuth config gives this integration, for user-facing copy."""
    integration = get_integration_by_id(integration_id)
    return integration.name if integration else integration_id


def _first_move_bubbles(connect_links: list[tuple[str, str]]) -> list[str]:
    if not connect_links:
        return [NO_LINKS_LINE]
    count = len(connect_links)
    if count == 1:
        lead = "One tap and that switches on. The link is live for the next hour:"
    else:
        lead = (
            f"{_TAP_COUNTS.get(count, str(count))} taps and those switch on. "
            "Links are live for the next hour:"
        )
    return [lead] + [
        f"{_integration_display_name(integration_id)}: {url}"
        for integration_id, url in connect_links
    ]


def compose_first_contact(
    platform: str,
    name: str | None,
    preferences: OnboardingPreferences,
    connect_links: list[tuple[str, str]],
) -> list[str]:
    """Every bubble a bot sends right after a one-tap link, in order.

    ``connect_links`` are ``(integration_id, url)`` pairs already minted by the
    caller for whatever :func:`needed_integration_ids` returned MINUS what the
    user already has connected. Minting is I/O and this stays pure, so the copy
    can be asserted without a Redis or a Mongo in the room.
    """
    bubbles = [compose_link_greeting(platform, name)]

    for need in preferences.needs or []:
        promise = NEED_PROMISES.get(need)
        if promise:
            bubbles.append(promise)

    other = (preferences.other_need or "").strip().rstrip(".!")
    if other:
        bubbles.append(OTHER_NEED_PROMISE.format(other_need=other))

    bubbles.extend(_first_move_bubbles(connect_links))
    return bubbles


async def build_first_contact(
    user_id: str,
    platform: str,
    name: str | None,
    preferences: OnboardingPreferences,
) -> list[str]:
    """:func:`compose_first_contact` with the connect links resolved and minted.

    An integration the user already connected is dropped rather than re-offered:
    the whole point of the links is that they are the first move, and a link to
    something already on is a tap that does nothing.

    A link that could not be minted (Redis down) is dropped too — an unusable
    URL in a first message is worse than one fewer.
    """
    connect_links: list[tuple[str, str]] = []
    for integration_id in needed_integration_ids(preferences):
        if await user_integration_repository.is_connected(user_id, integration_id):
            continue
        url = await build_connect_link_url(user_id, integration_id)
        if url:
            connect_links.append((integration_id, url))

    return compose_first_contact(platform, name, preferences, connect_links)
