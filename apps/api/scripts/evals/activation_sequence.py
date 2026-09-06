#!/usr/bin/env python3
# mypy: ignore-errors -- dev eval script; typing not maintained here
"""
Read five days of the activation sequence the way a user would, then score them.

Not a test: it calls the REAL model, five times per synthetic user, through the
same ``draft_message`` the worker uses — including the repetition check, which
is the thing most likely to be wrong. No API and no database: each user is a
role, two Q2 picks, and a scripted "yesterday" per day, on a frozen clock. What
this proves is the copy and the uniqueness guard. What it does NOT prove is
scheduling, delivery, the claim, or anything Mongo-shaped; those are the unit
and integration tiers.

A judge model then answers the five questions that decide whether someone keeps
a bot texting them, and rates the run out of 5.

Usage (from apps/api/):

    uv run python scripts/evals/activation_sequence.py
    uv run python scripts/evals/activation_sequence.py --users 3
"""

import argparse
import asyncio
from datetime import UTC, datetime
from pathlib import Path
import sys

backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from pydantic import BaseModel

from app.agents.llm.client import LLMInvokeOptions, ainvoke_llm, background_structured_runnable
from app.models.activation_models import ActivationDraft
from app.models.user_models import OnboardingNeed, OnboardingPreferences
from app.services.activation.context import format_who_block
from app.services.activation.copy import ActivationCopyError, draft_message
from app.services.activation.policy import SEQUENCE_LENGTH, Direction, Facts, direction

JUDGE_TIMEOUT_SECONDS = 90.0
#: A frozen clock so two runs of this script are comparable.
FROZEN_NOW = datetime(2026, 5, 4, 8, 0, tzinfo=UTC)


class Persona(BaseModel):
    """One synthetic user: who they are, and what happens to them each day."""

    name: str
    profession: str
    needs: list[OnboardingNeed]
    other_need: str | None = None
    integrations: list[str]
    #: One scripted "what happened yesterday" per day, day 0 first.
    days: list[str]


PERSONAS = [
    Persona(
        name="founder-cold",
        profession="founder",
        needs=[OnboardingNeed.INBOX, OnboardingNeed.FOUNDER_TEAM_UPDATES],
        integrations=[],
        days=[
            "Nothing. They signed up and closed the tab.",
            "Nothing. No messages, nothing connected.",
            "Nothing.",
            "- [them] what do you actually do",
            "- [them] ok connected gmail\n- [you] great, want the morning sort tomorrow?",
        ],
    ),
    Persona(
        name="sales-warm",
        profession="sales",
        needs=[OnboardingNeed.SALES_LEADS, OnboardingNeed.SALES_CALL_RESEARCH],
        other_need="I forget to follow up after demos",
        integrations=["Gmail", "Google Calendar"],
        days=[
            "Nothing yet, but Gmail and Calendar are connected.",
            "- [them] can you pull the thread with Acme\n- [you] here it is, last reply was Tuesday",
            "- [them] draft a follow up to Acme\n- [you] drafted it, want me to send?",
            "Nothing. They did not open the chat.",
            "- [them] send it",
        ],
    ),
    Persona(
        name="engineer-quiet",
        profession="engineering",
        needs=[OnboardingNeed.ENGINEERING_PRS, OnboardingNeed.ENGINEERING_NOTIFICATIONS],
        integrations=["GitHub"],
        days=[
            "Nothing. GitHub connected during onboarding.",
            "Nothing.",
            "- [them] how many PRs are waiting on me",
            "Nothing.",
            "Nothing.",
        ],
    ),
]

JUDGE_PROMPT = """You are judging one day of an assistant's daily message to a new user.

Who the user is:
{who}

What the assistant already sent them on earlier days:
{earlier}

What actually happened in the last day:
{yesterday}

Today's message:
{message}

Score each 1 (yes) or 0 (no), strictly:
- specific: it could only have been written for THIS user, given what happened. A message that
  would fit any new user scores 0.
- unique: it does not reuse an earlier day's opener or repeat an earlier day's suggestion.
  If there are no earlier days, score 1.
- not_annoying: it does not nag, does not guilt, does not say it is checking in, does not
  point out that the user has been quiet.
- one_next_step: exactly one thing to do or answer. A menu of options scores 0.
- short: it reads as a text message, not an email.

Also write one short `note` naming the single biggest problem with it, or what makes it good."""

RUN_JUDGE_PROMPT = """Here are the five daily messages an assistant sent a new user, in order.

Who the user is:
{who}

The five days:
{days}

Answer `keep`: 1 to 5, how likely this person keeps this assistant texting them.
1 = they mute it. 3 = tolerable. 5 = they would miss it.
Then `note`: one sentence on why."""


class _Verdict(BaseModel):
    specific: int
    unique: int
    not_annoying: int
    one_next_step: int
    short: int
    note: str


class _RunVerdict(BaseModel):
    keep: int
    note: str


class Day(BaseModel):
    day: int
    direction: Direction
    draft: ActivationDraft | None = None
    error: str | None = None
    verdict: _Verdict | None = None


def _facts_for(persona: Persona, day: int, yesterday: str) -> Facts:
    """The facts a real run would have gathered, derived from the script."""
    replied = "[them]" in yesterday
    return Facts(
        opted_out=False,
        days_sent=day,
        account_age_days=day,
        subscription_active=True,
        has_channel=True,
        user_messaged_last_24h=replied,
        replied_to_sequence_last_24h=replied,
        connected_integrations=len(persona.integrations),
        handovers=1 if day > 0 and replied else 0,
    )


async def _run_persona(persona: Persona) -> tuple[str, list[Day], _RunVerdict | None]:
    preferences = OnboardingPreferences(
        profession=persona.profession,
        needs=persona.needs,
        other_need=persona.other_need,
        response_style="casual",
        custom_instructions=None,
    )
    who = format_who_block(preferences)
    integrations = (
        "Connected: " + ", ".join(persona.integrations)
        if persona.integrations
        else "Nothing connected."
    )
    sent: list[Day] = []
    earlier: list[tuple[str, str]] = []
    already = "Nothing yet. This is the first message."

    for day in range(SEQUENCE_LENGTH):
        yesterday = persona.days[day]
        today = direction(_facts_for(persona, day, yesterday))
        print(f"... {persona.name} day {day} ({today})", flush=True)
        row = Day(day=day, direction=today)
        try:
            row.draft = await draft_message(
                day=day,
                direction=today,
                who_block=who,
                integrations_block=integrations,
                yesterday_block=yesterday,
                already_sent_block=already,
                earlier=earlier,
            )
            earlier.append((row.draft.bubbles[0], row.draft.suggestion))
            already = "\n\n".join(
                f"Day {d.day} ({d.direction}):\n"
                + "\n".join(d.draft.bubbles)
                + f"\n(suggestion: {d.draft.suggestion})"
                for d in [*sent, row]
                if d.draft
            )
        except ActivationCopyError as e:
            row.error = str(e)
        sent.append(row)

    for row in sent:
        if row.draft is None:
            continue
        row.verdict = await ainvoke_llm(
            background_structured_runnable(_Verdict, temperature=0.0),
            JUDGE_PROMPT.format(
                who=who,
                earlier="\n".join(f"- {b}" for b, _ in earlier[: row.day]) or "Nothing yet.",
                yesterday=persona.days[row.day],
                message="\n".join(row.draft.bubbles),
            ),
            label="activation_judge",
            options=LLMInvokeOptions(max_attempts=2, timeout=JUDGE_TIMEOUT_SECONDS),
        )

    run_verdict = await ainvoke_llm(
        background_structured_runnable(_RunVerdict, temperature=0.0),
        RUN_JUDGE_PROMPT.format(
            who=who,
            days="\n\n".join(
                f"Day {d.day}: " + ("\n".join(d.draft.bubbles) if d.draft else "(skipped)")
                for d in sent
            ),
        ),
        label="activation_run_judge",
        options=LLMInvokeOptions(max_attempts=2, timeout=JUDGE_TIMEOUT_SECONDS),
    )
    return who, sent, run_verdict


def _report(name: str, who: str, days: list[Day], run_verdict: _RunVerdict | None) -> None:
    cols = ("specific", "unique", "not_annoying", "one_next_step", "short")
    print(f"\n======== {name}\n{who}\n")
    print(f"{'day':<5} {'direction':<16} " + " ".join(f"{c[:10]:>11}" for c in cols))
    for row in days:
        scores = [getattr(row.verdict, c) if row.verdict else 0 for c in cols]
        print(f"{row.day:<5} {row.direction:<16} " + " ".join(f"{s:>11}" for s in scores))
    if run_verdict:
        print(f"\nwould keep this bot: {run_verdict.keep}/5 — {run_verdict.note}")
    print("\n---- messages\n")
    for row in days:
        print(f"Day {row.day} [{row.direction}]")
        if row.draft is None:
            print(f"  SKIPPED: {row.error}\n")
            continue
        for bubble in row.draft.bubbles:
            print("  | " + bubble.replace("\n", "\n  | "))
        print(f"  (suggestion: {row.draft.suggestion})")
        if row.verdict:
            print(f"  judge: {row.verdict.note}")
        print()


async def run(count: int) -> None:
    print(f"activation sequence simulator — clock frozen at {FROZEN_NOW.isoformat()}")
    for persona in PERSONAS[:count]:
        who, days, run_verdict = await _run_persona(persona)
        _report(persona.name, who, days, run_verdict)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--users", type=int, default=len(PERSONAS))
    args = parser.parse_args()
    asyncio.run(run(args.users))


if __name__ == "__main__":
    main()
