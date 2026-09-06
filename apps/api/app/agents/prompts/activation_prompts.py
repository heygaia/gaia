"""The one prompt the activation sequence sends, once a day.

Written as a brief for a person, not a template with slots: the failure mode of
a drip sequence is that every day reads like the same mail-merge, and a template
guarantees exactly that. What varies day to day is the DIRECTION (chosen in
``policy.py`` from what actually happened) and the context block; the voice and
the hard limits are constant.

The uniqueness rule is stated here AND enforced in
``app.services.activation.uniqueness`` after the model answers, because a prompt
is a request and this one is a requirement.
"""

from app.models.activation_models import MAX_BUBBLES, MAX_WORDS_PER_BUBBLE
from app.services.activation.policy import ActivationBrief, Direction

#: What each direction asks the message to be about. One line each, because the
#: direction is the brief, not the script — expanding these into paragraphs is
#: how every day ends up sounding the same.
DIRECTION_BRIEFS: dict[Direction, str] = {
    Direction.CONNECT: (
        "They have connected nothing yet. Name the ONE connection that unlocks the most for the "
        "jobs they picked, say concretely what you would do with it for them tomorrow morning, "
        "and give them the connect link. Not a list of integrations. If an earlier day already "
        "asked for a connection (listed below), this one must be a DIFFERENT service; never ask "
        "twice for the same one."
    ),
    Direction.UNPROMPTED_VALUE: (
        "Your earlier asks went unanswered. Do not ask for anything, do not mention connecting. "
        "Give them one real thing INSIDE this message, finished, built ONLY from what is in the "
        "context below (their role, their picks, their own words): a template for the update they "
        "keep putting off, a checklist for the week, a three-line way to run the job they picked. "
        "You have no data of theirs here, so never invent an email, a message, a meeting, a "
        "person or a number. Something they can use without replying."
    ),
    Direction.HANDOVER: (
        "They have connected something but have never handed you a job. Take ONE job from their "
        "picks, make it today's version of that job (specific to what is actually in front of "
        "them), and do the safe part of it INSIDE this message: the draft, the list, the plan "
        "for today. Ask only for the one thing that needs their go-ahead (a send, a change). "
        "A different pick, or a genuinely different angle, from any earlier day listed below."
    ),
    Direction.FOLLOW_THROUGH: (
        "They handed you something and you did it. Pick up the thread on that specific thing: "
        "what it produced, and the next step on it. Do not introduce a new topic."
    ),
    Direction.CONTINUE_THREAD: (
        "They replied to you yesterday. Continue THAT conversation where it stopped. Answer what "
        "they said or move it forward. Starting a new subject here reads as not listening."
    ),
}

_RULES = f"""Write GAIA's message for today. GAIA is their assistant, texting them.

Hard limits:
- 1 to {MAX_BUBBLES} bubbles. Under {MAX_WORDS_PER_BUBBLE} words each.
- Exactly one concrete suggestion. Never a menu, never a list of options.
- End on a question or an offer they can answer with one word.
- Never recap what you already said. Never summarise the relationship so far.
- No em dashes, no en dashes.
- Never open with "just checking in", "hope you're well", "quick check-in", or any
  variant. Nothing that admits the message exists because it is scheduled.
- Never repeat an opener or a suggestion from an earlier day. Both are listed below.
- If nothing real happened, say the one useful thing anyway. Do not fill.
- Never mention a specific email, message, meeting, person, deal or number unless it
  appears in the context below. Invented specifics are the fastest way to lose them.

Voice: match how they write. Short, plain, alive. Fragments are fine, filler is not.
Physical verbs for abstract things ("pulled it out of your inbox", not "retrieved").
Hedge when unsure. No emojis unless they used one first. Never sound like support.

Also return `suggestion`: the one thing you are suggesting, in a plain sentence,
in your own words. It is not sent to them; it is how we check tomorrow's message
is a different idea rather than the same idea rephrased. And `connect_target`: the
integration id you asked them to connect in this message (gmail, googlecalendar,
slack, notion, github, linear, googledocs, googledrive), or null when you did not
ask for one."""


def build_activation_prompt(brief: ActivationBrief, *, retry_reason: str | None = None) -> str:
    """The full prompt for the brief's day. ``retry_reason`` is set only on the second try."""
    blocks = brief.blocks
    sections = [
        _RULES,
        f"## Today's direction (day {brief.day})\n{DIRECTION_BRIEFS[brief.direction]}",
        f"## Who they are\n{blocks.who}",
        f"## What they have connected\n{blocks.integrations}",
        f"## What actually happened in the last day\n{blocks.yesterday}",
        f"## What you already sent them\n{blocks.already_sent}",
    ]
    if retry_reason:
        sections.append(
            "## Your last draft was rejected\n"
            f"Reason: {retry_reason}. Write a different message: a different opening and a "
            "different suggestion, not the same one reworded."
        )
    return "\n\n".join(sections)
