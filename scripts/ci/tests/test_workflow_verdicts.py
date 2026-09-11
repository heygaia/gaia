"""Every gated lane reports through the verdict contract, and the gate reads it.

A lane's verdict used to be the last hundred lines of a 20k-190k line log, and
whether it produced an `::error file=,line=` annotation at all was per-lane
folklore: `python-static` did, `test-python` and `regression-proof` did not.
The contract (scripts/ci/verdict.py) fixes that only for as long as every gated
job actually goes through it — and a job can stop doing so by deleting four
lines of YAML, which is invisible in review and produces no failure anywhere.

So: for both gate workflows, every job the gate NEEDS uploads its verdicts, and
the gate expects exactly that set. A lane can then only go quiet by editing
this list, which a reviewer sees.
"""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
WORKFLOWS = {
    "main.yml": REPO_ROOT / ".github" / "workflows" / "main.yml",
    "code-quality.yml": REPO_ROOT / ".github" / "workflows" / "code-quality.yml",
}
UPLOAD_VERDICT = "./.github/actions/upload-verdict"


@pytest.fixture(scope="module", params=sorted(WORKFLOWS))
def workflow(request: pytest.FixtureRequest) -> dict[str, Any]:
    return yaml.safe_load(WORKFLOWS[request.param].read_text())


def _gate(workflow: dict[str, Any]) -> dict[str, Any]:
    return workflow["jobs"]["quality-gate"]


def _gated_jobs(workflow: dict[str, Any]) -> list[str]:
    # A reusable-workflow caller (`uses:`) has no steps of its own to add one
    # to; nothing in either gate's needs is one today, and this keeps the
    # failure message about the real case if one ever is.
    return [j for j in _gate(workflow)["needs"] if "steps" in workflow["jobs"][j]]


def _expect_arg(workflow: dict[str, Any]) -> str:
    for step in _gate(workflow)["steps"]:
        env = step.get("env", {})
        if "EXPECT" in env:
            return str(env["EXPECT"])
    raise AssertionError("the quality-gate job passes no EXPECT to `verdict.py consolidate`")


def test_every_gated_job_uploads_its_verdict(workflow: dict[str, Any]) -> None:
    for name in _gated_jobs(workflow):
        steps = [s for s in workflow["jobs"][name]["steps"] if s.get("uses") == UPLOAD_VERDICT]
        assert steps, (
            f"job '{name}' is in quality-gate.needs but never runs {UPLOAD_VERDICT} — "
            "its verdict cannot reach the gate, and the gate will read it as NO VERDICT"
        )


def test_the_upload_runs_even_when_the_lane_failed(workflow: dict[str, Any]) -> None:
    # The whole point is the red lane. Without always() the upload is skipped
    # exactly when its findings matter.
    for name in _gated_jobs(workflow):
        for step in workflow["jobs"][name]["steps"]:
            if step.get("uses") == UPLOAD_VERDICT:
                assert "always()" in str(step.get("if", "")), (
                    f"job '{name}': the verdict upload must be `if: always()` — "
                    "a failed lane is the one whose verdict is worth reading"
                )


def test_verdict_artifact_names_are_unique(workflow: dict[str, Any]) -> None:
    # upload-artifact refuses a duplicate name, so a matrix job that does not
    # fold its matrix value into the name fails its own upload — after the
    # lane has already passed, where nobody looks.
    names: list[str] = []
    for name in _gated_jobs(workflow):
        job = workflow["jobs"][name]
        for step in job["steps"]:
            if step.get("uses") != UPLOAD_VERDICT:
                continue
            given = str(step["with"]["name"])
            if "strategy" in job:
                assert "matrix." in given or "strategy.job-index" in given, (
                    f"job '{name}' is a matrix job: its verdict artifact name {given!r} "
                    "must include the matrix value or the shards collide"
                )
            names.append(given)
    assert len(names) == len(set(names)), f"duplicate verdict artifact names: {names}"


def test_the_gate_consolidates_instead_of_printing_results(workflow: dict[str, Any]) -> None:
    runs = " ".join(str(s.get("run", "")) for s in _gate(workflow)["steps"])
    assert "verdict.py consolidate" in runs, (
        "the quality gate must reach its verdict through `verdict.py consolidate` — "
        "a hand-rolled result loop cannot tell a timeout from a failure, and sees "
        "nothing a lane actually found"
    )


def test_the_gate_expects_exactly_the_lanes_it_needs(workflow: dict[str, Any]) -> None:
    # `<job>@<family>` — the job name is what has to match `needs`; the family
    # is which lane ids satisfy it (see `verdict.py consolidate --help`).
    expected = {
        entry.partition("=")[0].partition("@")[0].strip()
        for entry in _expect_arg(workflow).split(",")
    }
    expected.discard("")
    assert expected == set(_gate(workflow)["needs"]), (
        "quality-gate's --expect list and its needs list have drifted; a lane missing "
        "from --expect can stop reporting without the gate noticing"
    )


def test_the_gate_passes_each_lanes_job_result(workflow: dict[str, Any]) -> None:
    # Without the result, consolidate cannot tell the two silences apart: a
    # SKIPPED lane legitimately writes no verdict (the changes job proved its
    # language untouched), while a successful lane that wrote none has lost its
    # reporting. Conflating them either reds every TS-only PR or hides the bug
    # this whole contract exists to catch.
    for entry in _expect_arg(workflow).split(","):
        job, _, result = entry.strip().partition("=")
        lane = job.partition("@")[0]
        if not lane:
            continue
        assert re.fullmatch(r"\$\{\{\s*needs\." + re.escape(lane) + r"\.result\s*\}\}", result), (
            f"lane '{lane}' in --expect carries {result!r}, not its needs.<job>.result"
        )
