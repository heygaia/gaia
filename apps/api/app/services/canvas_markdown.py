"""Markdown section helpers for tracked-todo canvases.

Canvases are `## Heading` sectioned markdown. These helpers locate a section
by exact heading, and split legacy canvases (which carried activity inside
the canvas) into the canvas.md / activity.md pair.
"""

import re

LEGACY_ACTIVITY_SECTIONS = ("Activity Log", "Timeline")
_LEARNINGS_SECTION = "Learnings"
# Activity entries the old append mode dumped under Learnings: "### 2026-08-20" blocks.
_DATED_BLOCK_RE = re.compile(r"(?:^|\n)(### \d{4}-\d{2}-\d{2}.*?)(?=\n### |\Z)", re.DOTALL)
# A Timeline line: "- <iso timestamp> <text>" — sortable by the timestamp prefix.
_TIMELINE_LINE_RE = re.compile(r"^- (\d{4}-\d{2}-\d{2}T\S+) ")


def _section_span(text: str, heading: str) -> tuple[int, int, int] | None:
    """(heading_start, body_start, section_end) for an exact `## {heading}` line."""
    pattern = re.compile(rf"(?:^|(?<=\n))## {re.escape(heading)}(?=\n|\Z)")
    match = pattern.search(text)
    if match is None:
        return None
    body_start = match.end()
    next_heading = re.compile(r"\n## ").search(text, body_start)
    section_end = next_heading.start() if next_heading else len(text)
    return match.start(), body_start, section_end


def section_body(text: str, heading: str) -> str | None:
    """Body of `## {heading}` (stripped), or None when the section is absent."""
    span = _section_span(text, heading)
    if span is None:
        return None
    _, body_start, section_end = span
    return text[body_start:section_end].strip()


def _remove_section(text: str, heading: str) -> tuple[str, str | None]:
    span = _section_span(text, heading)
    if span is None:
        return text, None
    heading_start, body_start, section_end = span
    body = text[body_start:section_end].strip()
    return text[:heading_start].rstrip("\n") + text[section_end:], body


def _rescue_dated_blocks_from_learnings(text: str) -> tuple[str, list[str]]:
    span = _section_span(text, _LEARNINGS_SECTION)
    if span is None:
        return text, []
    _, body_start, section_end = span
    body = text[body_start:section_end]
    blocks = [m.group(1).strip() for m in _DATED_BLOCK_RE.finditer(body)]
    if not blocks:
        return text, []
    remaining = _DATED_BLOCK_RE.sub("", body).strip()
    rebuilt = (
        text[:body_start] + ("\n" + remaining + "\n" if remaining else "\n") + text[section_end:]
    )
    return rebuilt, blocks


def _chronological(timeline_body: str) -> str:
    """Legacy Timeline was newest-first; activity.md is oldest-first."""
    lines = [ln for ln in timeline_body.splitlines() if ln.strip()]
    stamped = [(m.group(1), ln) for ln in lines if (m := _TIMELINE_LINE_RE.match(ln))]
    if len(stamped) != len(lines):
        return "\n".join(lines)
    return "\n".join(ln for _, ln in sorted(stamped))


def split_legacy_canvas(canvas: str) -> tuple[str, str | None]:
    """Move `## Activity Log`, `## Timeline`, and dated blocks stranded under
    `## Learnings` out of the canvas. Returns (new_canvas, activity or None).
    Idempotent: a canvas with nothing to move comes back unchanged."""
    parts: list[str] = []
    text, activity = _remove_section(canvas, "Activity Log")
    if activity:
        parts.append(activity)
    text, rescued = _rescue_dated_blocks_from_learnings(text)
    parts.extend(rescued)
    text, timeline = _remove_section(text, "Timeline")
    if timeline:
        parts.append(_chronological(timeline))
    if text == canvas:
        return canvas, None
    if not text.endswith("\n"):
        text += "\n"
    return text, "\n\n".join(parts) if parts else None
