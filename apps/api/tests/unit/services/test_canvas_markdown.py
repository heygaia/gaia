"""Unit tests for canvas_markdown — section extraction and the legacy split."""

from datetime import UTC, datetime

import pytest

from app.services.canvas_markdown import (
    _extract_entries,
    _line_timestamp,
    _remove_section,
    section_body,
    split_legacy_canvas,
)

LEGACY = """# Fix the thing

## Key Details
- Thread: 18f3a2b
- Email: rahul@example.com

## Current State
Waiting on reply.

## Activity Log
### 2026-08-20
- **Gmail agent**: sent email. Tools: GMAIL_SEND.

## Timeline
- 2026-08-21T09:00:00+00:00 ✓ scheduled run finished
- 2026-08-20T09:00:00+00:00 ▶ scheduled run started

## Context
Some accumulated context.

## Learnings
"""


class TestSectionBody:
    def test_returns_body_up_to_next_heading(self):
        assert section_body(LEGACY, "Current State") == "Waiting on reply."

    def test_none_when_missing(self):
        assert section_body(LEGACY, "Nope") is None

    def test_exact_heading_only(self):
        """'Current' must not match inside '## Current State'."""
        assert section_body(LEGACY, "Current") is None

    def test_first_line_heading(self):
        assert section_body("## Key Details\nx\n", "Key Details") == "x"

    def test_last_section_runs_to_end(self):
        assert section_body("## A\n1\n\n## B\n2\n3\n", "B") == "2\n3"


class TestSplitLegacyCanvas:
    def test_moves_activity_and_timeline_out(self):
        canvas, activity = split_legacy_canvas(LEGACY)

        assert "## Activity Log" not in canvas
        assert "## Timeline" not in canvas
        assert "## Key Details" in canvas
        assert "## Context" in canvas
        assert "## Learnings" in canvas
        assert activity is not None
        assert "sent email" in activity
        assert "scheduled run finished" in activity

    def test_timeline_reordered_chronologically(self):
        """Legacy Timeline inserted newest-first; activity.md is oldest-first."""
        _, activity = split_legacy_canvas(LEGACY)

        assert activity is not None
        assert activity.index("run started") < activity.index("run finished")

    def test_activity_precedes_timeline_entries(self):
        _, activity = split_legacy_canvas(LEGACY)

        assert activity is not None
        assert activity.index("sent email") < activity.index("run started")

    def test_none_when_nothing_to_move(self):
        canvas = "# T\n\n## Key Details\nx\n\n## Learnings\n"

        assert split_legacy_canvas(canvas) == (canvas, None)

    def test_empty_legacy_sections_are_dropped_without_activity(self):
        canvas = "# T\n\n## Activity Log\n\n## Timeline\n\n## Learnings\n"

        new_canvas, activity = split_legacy_canvas(canvas)

        assert activity is None
        assert "## Activity Log" not in new_canvas
        assert "## Timeline" not in new_canvas

    def test_entries_appended_after_learnings_are_rescued(self):
        """The production symptom: append mode dumped activity under Learnings."""
        canvas = (
            "# T\n\n## Key Details\nx\n\n## Learnings\n\n"
            "### 2026-08-20\n- **Gmail agent**: sent email.\n"
            "### 2026-08-21\n- **Slack agent**: posted update.\n"
        )

        new_canvas, activity = split_legacy_canvas(canvas)

        assert activity is not None
        assert "sent email" in activity and "posted update" in activity
        assert "sent email" not in new_canvas
        assert section_body(new_canvas, "Learnings") == ""

    def test_removed_section_leaves_one_blank_line_before_the_next_heading(self):
        canvas = "# T\n\n## Current State\nWaiting.\n\n## Timeline\n- x\n\n## Learnings\n"

        new_canvas, _ = split_legacy_canvas(canvas)

        assert new_canvas == "# T\n\n## Current State\nWaiting.\n\n## Learnings\n"

    def test_real_learnings_are_kept(self):
        canvas = "# T\n\n## Learnings\nSarah replies in 2-3 days.\n\n## Activity Log\n- did x\n"

        new_canvas, activity = split_legacy_canvas(canvas)

        assert section_body(new_canvas, "Learnings") == "Sarah replies in 2-3 days."
        assert activity == "- did x"

    def test_interleaved_dates_merge_chronologically_across_sources(self):
        """Activity Log / Learnings / Timeline entries interleave by date, not by source."""
        canvas = (
            "# T\n\n## Key Details\nk\n\n"
            "## Activity Log\n- 2026-08-22T10:00:00+00:00 activity late\n\n"
            "## Learnings\nReal learning.\n\n### 2026-08-20\n- rescued early\n\n"
            "## Timeline\n- 2026-08-21T10:00:00+00:00 timeline middle\n"
        )

        new_canvas, activity = split_legacy_canvas(canvas)

        # Exact output, not just relative order: this pins the sort key (a
        # lambda over the timestamp) and the blank-line join separator. A
        # looser `index()` check let the sort-key and join-separator mutants
        # survive.
        assert activity == (
            "### 2026-08-20\n- rescued early\n\n"
            "- 2026-08-21T10:00:00+00:00 timeline middle\n\n"
            "- 2026-08-22T10:00:00+00:00 activity late"
        )
        assert new_canvas == "# T\n\n## Key Details\nk\n\n## Learnings\nReal learning.\n"

    def test_idempotent(self):
        once, activity = split_legacy_canvas(LEGACY)

        assert split_legacy_canvas(once) == (once, None)
        assert activity is not None

    def test_blank_section_at_start_yields_leading_newline_not_none(self):
        """A section removed with no preceding content leaves `"\\n"`, not
        `""`/`None` — pins the `before` empty check in `_remove_section`."""
        new_canvas, activity = split_legacy_canvas("## Timeline\n- a")

        assert new_canvas == "\n"
        assert activity == "- a"

    def test_undated_block_is_kept_verbatim_and_trailing_lines_join_with_newline(self):
        """A `### ` block with no date is undated; the surrounding text is
        re-joined with `\\n`, not concatenated — pins both branches."""
        dated, undated = _extract_entries("### nope\ntail one\ntail two")

        assert dated == []
        assert undated == ["### nope", "tail one", "tail two"]

    def test_naive_timestamps_are_tagged_utc(self):
        """A timeline line with no offset is assumed UTC; an aware one is kept
        as-is. Pins the `stamp.tzinfo is None` branch and the `.replace` tz."""
        assert _line_timestamp("- 2026-08-21T09:00:00 rest") == datetime(
            2026, 8, 21, 9, 0, tzinfo=UTC
        )
        assert _line_timestamp("- 2026-08-21T09:00:00+02:00 rest") == datetime.fromisoformat(
            "2026-08-21T09:00:00+02:00"
        )

    def test_root_level_section_removal_has_no_extra_blank_line(self):
        """A section that is the FIRST heading has no preceding content, so the
        blank-line preservation must not fire. Pins `before and ...` (an `or`
        would insert an extra leading newline)."""
        new_canvas, activity = split_legacy_canvas("## Timeline\n- a\n\n## B\n2\n")

        assert new_canvas == "\n## B\n2\n"
        assert activity == "- a"

    def test_multiple_dated_blocks_and_undated_text_merge(self):
        """Two dated blocks plus an undated line: `_extract_entries` returns
        them in source order (the merge sorts downstream)."""
        dated, undated = _extract_entries(
            "- 2026-08-22T10:00:00+00:00 late\nnote line\n- 2026-08-20T10:00:00+00:00 early"
        )

        assert [entry for _, entry in dated] == [
            "- 2026-08-22T10:00:00+00:00 late",
            "- 2026-08-20T10:00:00+00:00 early",
        ]
        assert undated == ["note line"]

    def test_all_dated_entries_drop_the_undated_list(self):
        """When every entry is dated the result is the sorted dated list and
        nothing else — pins the `merged if merged else None` tail."""
        _, activity = split_legacy_canvas(
            "## Activity Log\n- 2026-08-22T10:00:00+00:00 late\n- 2026-08-20T10:00:00+00:00 early\n"
        )

        assert activity == ("- 2026-08-20T10:00:00+00:00 early\n\n- 2026-08-22T10:00:00+00:00 late")

    def test_remove_section_is_a_noop_when_absent(self):
        assert _remove_section("# T\n\n## B\n2\n", "Missing") == ("# T\n\n## B\n2\n", None)


@pytest.mark.parametrize("heading", ["Activity Log", "Timeline"])
def test_split_removes_each_legacy_section_alone(heading: str):
    canvas = f"# T\n\n## Key Details\nk\n\n## {heading}\n- entry\n\n## Learnings\n"

    new_canvas, activity = split_legacy_canvas(canvas)

    assert f"## {heading}" not in new_canvas
    assert activity == "- entry"
