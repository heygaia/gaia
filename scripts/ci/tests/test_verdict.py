"""regression-proof-verdict: what counts as proof that a bug existed on base.

The verdict reads JUnit, and JUnit records a skip as neither a failure nor an
error — so "not failed and not errored" quietly swept skips in with the passes.
The lane then told the author their fix was not needed and their test did not
exercise the bug it names, about a test that never ran at all. Every contract
test skips without ``USE_REAL_SERVICES=1``, so that is not a corner case.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
_SPEC = importlib.util.spec_from_file_location(
    "verdict", REPO_ROOT / "scripts" / "ci" / "verdict.py"
)
assert _SPEC is not None and _SPEC.loader is not None
verdict = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(verdict)


def _junit(tmp_path: Path, name: str, inner: str) -> str:
    path = tmp_path / "junit.xml"
    path.write_text(
        f'<testsuites><testsuite name="pytest"><testcase classname="tests.contracts.test_x" '
        f'file="tests/contracts/test_x.py" line="41" name="{name}">{inner}</testcase>'
        "</testsuite></testsuites>"
    )
    return str(path)


def test_a_skipped_test_is_not_proof(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    junit = _junit(tmp_path, "test_bug", '<skipped message="needs real Mongo"/>')

    assert verdict.cmd_regression_proof_verdict([junit, "--out", str(tmp_path / "v")]) == 1

    out = capsys.readouterr().out
    assert "SKIPPED on base" in out
    assert "PASS on base" not in out


def test_a_failure_on_base_is_proof(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    junit = _junit(tmp_path, "test_bug", '<failure message="assert False"/>')

    assert verdict.cmd_regression_proof_verdict([junit, "--out", str(tmp_path / "v")]) == 0
    assert "fail on base as required" in capsys.readouterr().out


def test_a_pass_on_base_still_fails_the_lane(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    junit = _junit(tmp_path, "test_bug", "")

    assert verdict.cmd_regression_proof_verdict([junit, "--out", str(tmp_path / "v")]) == 1
    assert "PASS on base" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# The verdict contract: emit writes all three at once, consolidate reads them.
# ---------------------------------------------------------------------------


def _emit(tmp_path: Path, *args: str) -> int:
    return verdict.cmd_emit(["--out", str(tmp_path / "v"), *args])


def _read(tmp_path: Path, lane: str) -> dict[str, Any]:
    loaded: dict[str, Any] = json.loads((tmp_path / "v" / f"{lane}.json").read_text())
    return loaded


def test_emit_writes_the_json_the_annotation_and_the_summary_together(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    # All three or none: they were three things a lane could forget separately,
    # and this is the assertion that they now come from one call.
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))

    _emit(
        tmp_path,
        "--lane",
        "biome",
        "--status",
        "fail",
        "--summary",
        "1 file did not pass",
        "--finding",
        "apps/web/src/a.tsx:12:lint/style/noVar: use const",
        "--advice",
        "pnpm run quality:lint --write",
    )

    doc = _read(tmp_path, "biome")
    assert doc["status"] == "fail"
    assert doc["findings"] == [
        {"file": "apps/web/src/a.tsx", "line": 12, "message": "lint/style/noVar: use const"}
    ]
    assert doc["advice"] == ["pnpm run quality:lint --write"]

    captured = capsys.readouterr()
    assert "::error file=apps/web/src/a.tsx,line=12::lint/style/noVar: use const" in captured.out
    assert "biome: FAIL — 1 file did not pass" in captured.err
    assert "apps/web/src/a.tsx:12" in summary.read_text()


def test_a_finding_message_may_contain_colons(tmp_path: Path) -> None:
    # Splitting on every colon would truncate exactly the messages worth
    # reading — tool codes and assertions are full of them.
    _emit(
        tmp_path,
        "--lane",
        "mypy",
        "--status",
        "fail",
        "--summary",
        "1 error",
        "--finding",
        "app/x.py:9:error: Incompatible return value type (got: int)",
    )
    (found,) = _read(tmp_path, "mypy")["findings"]
    assert found["message"] == "error: Incompatible return value type (got: int)"


def test_a_detail_file_attaches_to_the_finding_it_follows(tmp_path: Path) -> None:
    first, second = tmp_path / "a.txt", tmp_path / "b.txt"
    first.write_text("assert 1 == 2")
    second.write_text("KeyError: 'x'")

    _emit(
        tmp_path,
        "--lane",
        "test-python/unit-a",
        "--status",
        "fail",
        "--summary",
        "2 failed",
        "--finding",
        "t/a.py:1:FAILED test_a",
        "--detail-file",
        str(first),
        "--finding",
        "t/b.py:2:ERROR test_b",
        "--detail-file",
        str(second),
    )

    findings = _read(tmp_path, "test-python/unit-a")["findings"]
    assert [f["detail"] for f in findings] == ["assert 1 == 2", "KeyError: 'x'"]


def test_a_skip_annotates_as_a_warning_not_an_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # A skipped lane is not a red PR. Annotating it `::error` is how a lane
    # that legitimately had nothing to do reads as a failure.
    _emit(
        tmp_path,
        "--lane",
        "python-mypy",
        "--status",
        "skip",
        "--summary",
        "no Python changed",
        "--finding",
        "a.py:1:nothing to do",
    )
    captured = capsys.readouterr()
    assert "::warning file=a.py,line=1::nothing to do" in captured.out
    assert "::error" not in captured.out


def test_emit_reports_but_does_not_decide(tmp_path: Path) -> None:
    # It exits 0 on a failure on purpose: it is called from `if: always()`
    # steps, and the dying belongs at the call site (`ci_verdict_die`).
    assert _emit(tmp_path, "--lane", "x", "--status", "fail", "--summary", "no") == 0


def test_only_if_missing_never_overwrites_a_real_verdict(tmp_path: Path) -> None:
    # The timeout step in the upload-verdict composite runs after the lane; a
    # lane that DID report must keep its own findings.
    _emit(tmp_path, "--lane", "x", "--status", "fail", "--summary", "the real one")
    _emit(
        tmp_path,
        "--lane",
        "x",
        "--status",
        "timed_out",
        "--summary",
        "guessed",
        "--only-if-missing",
    )
    assert _read(tmp_path, "x")["summary"] == "the real one"


def _consolidate(tmp_path: Path, expect: str) -> int:
    return verdict.cmd_consolidate([str(tmp_path / "v"), "--expect", expect])


def test_consolidate_fails_a_lane_that_never_reported(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # The enforcement. A lane that stops running looks exactly like a lane with
    # no failures, and this is the only thing that can tell them apart.
    _emit(tmp_path, "--lane", "biome", "--status", "pass", "--summary", "ok")

    assert _consolidate(tmp_path, "biome=success,dead-code=success") == 1
    assert "NO VERDICT" in capsys.readouterr().out


def test_consolidate_lets_a_skipped_lane_report_nothing(tmp_path: Path) -> None:
    # A lane the `changes` job proved untouched runs no steps at all, so it
    # CANNOT write a verdict. Demanding one would red every TS-only PR.
    _emit(tmp_path, "--lane", "biome", "--status", "pass", "--summary", "ok")

    assert _consolidate(tmp_path, "biome=success,python-mypy=skipped") == 0


def test_a_timed_out_lane_is_not_reported_as_a_failure(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # The bug this replaces: the gate printed "failure" for a lane that merely
    # ran out of clock, sending readers to hunt a finding nobody had written.
    _emit(tmp_path, "--lane", "test-mutation", "--status", "timed_out", "--summary", "ran out")

    assert _consolidate(tmp_path, "test-mutation=success") == 1
    out = capsys.readouterr().out
    assert "TIMED_OUT" in out
    assert "FAIL" not in out


def test_a_cancelled_lane_with_no_verdict_reads_as_timed_out(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "v").mkdir()
    assert _consolidate(tmp_path, "semgrep=cancelled") == 1
    assert "timed_out" in capsys.readouterr().out


def test_consolidate_reports_the_worst_status_it_saw(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _emit(tmp_path, "--lane", "a", "--status", "pass", "--summary", "ok")
    _emit(tmp_path, "--lane", "b", "--status", "timed_out", "--summary", "clock")
    _emit(tmp_path, "--lane", "c", "--status", "fail", "--summary", "broken")

    assert _consolidate(tmp_path, "a=success,b=failure,c=failure") == 1
    # fail outranks timed_out: a real finding is what the reader should open
    # first, and a headline of TIMED_OUT would send them to the wrong place.
    assert "quality-gate: FAIL" in capsys.readouterr().out


def test_a_family_of_sub_unit_verdicts_satisfies_one_expected_lane(tmp_path: Path) -> None:
    # How many mutation shards or test-python slices exist is decided at
    # runtime, so the gate expects the family and each sub-unit reports itself.
    _emit(tmp_path, "--lane", "test-mutation/shard-0", "--status", "pass", "--summary", "ok")
    _emit(tmp_path, "--lane", "test-mutation/shard-1", "--status", "pass", "--summary", "ok")

    assert _consolidate(tmp_path, "test-mutation=success") == 0


def test_one_red_sub_unit_reds_the_family(tmp_path: Path) -> None:
    _emit(tmp_path, "--lane", "test-mutation/shard-0", "--status", "pass", "--summary", "ok")
    _emit(tmp_path, "--lane", "test-mutation/shard-1", "--status", "fail", "--summary", "survivor")

    assert _consolidate(tmp_path, "test-mutation=success") == 1


def test_a_verdict_nobody_expected_is_still_read(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # Otherwise a lane could go quiet just by renaming itself, and the mutation
    # gate's per-module verdicts would be dropped from the table.
    _emit(
        tmp_path, "--lane", "mutation/app-services-x", "--status", "fail", "--summary", "survivor"
    )

    assert _consolidate(tmp_path, "biome=skipped") == 1
    assert "mutation/app-services-x" in capsys.readouterr().out


def test_pytest_verdict_points_at_the_failing_test(tmp_path: Path) -> None:
    junit = _junit(
        tmp_path, "test_bug", '<failure message="assert 1 == 2">E  assert 1 == 2</failure>'
    )

    verdict.cmd_pytest_verdict(
        [
            junit,
            "--lane",
            "test-python/unit-a",
            "--path-prefix",
            "apps/api/",
            "--out",
            str(tmp_path / "v"),
        ]
    )

    (found,) = _read(tmp_path, "test-python/unit-a")["findings"]
    assert found["file"] == "apps/api/tests/contracts/test_x.py"
    # JUnit's `line` is 0-based, GitHub annotations are 1-based.
    assert found["line"] == 42
    assert "FAILED" in found["message"]


def test_a_green_pytest_run_that_exited_nonzero_is_not_a_pass(tmp_path: Path) -> None:
    # The flake gate and the coverage threshold both fail the step with every
    # test green; a verdict of `pass` over a red step is worse than none.
    junit = _junit(tmp_path, "test_ok", "")

    verdict.cmd_pytest_verdict(
        [junit, "--lane", "slice", "--exit-code", "1", "--out", str(tmp_path / "v")]
    )

    assert _read(tmp_path, "slice")["status"] == "fail"


def test_a_real_xunit2_report_still_lands_on_the_failing_line(tmp_path: Path) -> None:
    # Verified against a real `pytest --junitxml` run, not invented: pytest's
    # DEFAULT family (xunit2) writes no file/line attributes at all. Reading
    # only the attributes annotated every failure at `<prefix>/` line 1, which
    # renders nowhere — and no hand-written fixture would have shown it.
    junit = tmp_path / "real.xml"
    junit.write_text(
        '<?xml version="1.0" encoding="utf-8"?><testsuites name="pytest tests">'
        '<testsuite name="pytest" errors="0" failures="1" skipped="0" tests="2">'
        '<testcase classname="tests.unit.test_real" name="test_breaks" time="0.08">'
        '<failure message="assert 0 == 2">def test_breaks():\n'
        "        items = []\n"
        "&gt;       assert len(items) == 2\n"
        "E       assert 0 == 2\n\n"
        "tests/unit/test_real.py:7: AssertionError</failure></testcase>"
        '<testcase classname="tests.unit.test_real" name="test_passes" time="0.001" />'
        "</testsuite></testsuites>"
    )

    verdict.cmd_pytest_verdict(
        [
            str(junit),
            "--lane",
            "slice",
            "--path-prefix",
            "apps/api/",
            "--out",
            str(tmp_path / "v"),
        ]
    )

    (found,) = _read(tmp_path, "slice")["findings"]
    assert (found["file"], found["line"]) == ("apps/api/tests/unit/test_real.py", 7)


def test_only_if_missing_matches_by_lane_id_not_by_file_name(tmp_path: Path) -> None:
    # The mutation gate writes lane `mutation/shard-2` to `mutation/_shard-2.json`,
    # while `verdict_path` would look for `mutation/shard-2.json`. Checking the
    # path alone let the composite's status-derived fallback claim a lane id
    # that already had a real, finding-carrying verdict.
    theirs = tmp_path / "v" / "mutation" / "_shard-2.json"
    theirs.parent.mkdir(parents=True)
    theirs.write_text(
        json.dumps(
            {
                "lane": "mutation/shard-2",
                "status": "fail",
                "summary": "1 survivor",
                "findings": [],
                "advice": [],
            }
        )
    )

    _emit(
        tmp_path,
        "--lane",
        "mutation/shard-2",
        "--status",
        "pass",
        "--summary",
        "passed",
        "--only-if-missing",
    )

    assert not (tmp_path / "v" / "mutation" / "shard-2.json").exists()
    assert _consolidate(tmp_path, "test-mutation@mutation=success") == 1


def test_an_expect_entry_may_name_a_family_other_than_the_job(tmp_path: Path) -> None:
    # The gate's needs entry is `test-mutation`; the lanes it produces are
    # `mutation/<module>`, one per mutated module, and how many there are is
    # only known at runtime.
    _emit(tmp_path, "--lane", "mutation/app-services-budget", "--status", "pass", "--summary", "ok")
    _emit(tmp_path, "--lane", "mutation/app-agents-tools", "--status", "pass", "--summary", "ok")

    assert _consolidate(tmp_path, "test-mutation@mutation=success") == 0


def test_a_family_with_no_members_at_all_is_still_NO_VERDICT(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # The enforcement has to survive the aliasing: a mutation job that ran and
    # produced nothing is the case this contract exists for.
    (tmp_path / "v").mkdir()

    assert _consolidate(tmp_path, "test-mutation@mutation=success") == 1
    out = capsys.readouterr().out
    assert "NO VERDICT" in out
    # Reported under the JOB name, which is what the reader sees in the checks
    # list — not under the family, which names no job.
    assert "test-mutation" in out


def test_a_result_only_lane_passes_without_any_verdict(tmp_path: Path) -> None:
    # `select-runner` checks out the default branch and `probe` never checks
    # out, so neither can run the local upload composite. Demanding a verdict
    # from them reds every run; dropping them from the list un-enforces them.
    (tmp_path / "v").mkdir()

    assert _consolidate(tmp_path, "select-runner@result-only=success") == 0


def test_a_result_only_lane_still_reds_the_gate_when_its_job_failed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "v").mkdir()

    assert _consolidate(tmp_path, "select-runner@result-only=failure") == 1
    assert "fail" in capsys.readouterr().out


def test_a_result_only_lane_that_was_cancelled_reads_as_timed_out(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "v").mkdir()

    assert _consolidate(tmp_path, "probe@result-only=cancelled") == 1
    assert "timed_out" in capsys.readouterr().out


def test_result_only_is_opt_in_never_the_default_for_silence(tmp_path: Path) -> None:
    # The control for the three above: an ordinary lane that reports nothing is
    # still a failure. If `result-only` ever leaked into the default path, this
    # is what would notice.
    (tmp_path / "v").mkdir()

    assert _consolidate(tmp_path, "biome=success") == 1
