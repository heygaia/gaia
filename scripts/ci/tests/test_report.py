"""regression-proof-verdict: what counts as proof that a bug existed on base.

The verdict reads JUnit, and JUnit records a skip as neither a failure nor an
error — so "not failed and not errored" quietly swept skips in with the passes.
The lane then told the author their fix was not needed and their test did not
exercise the bug it names, about a test that never ran at all. Every contract
test skips without ``USE_REAL_SERVICES=1``, so that is not a corner case.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
_SPEC = importlib.util.spec_from_file_location("report", REPO_ROOT / "scripts" / "ci" / "report.py")
assert _SPEC is not None and _SPEC.loader is not None
report = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(report)


def _junit(tmp_path: Path, name: str, inner: str) -> str:
    path = tmp_path / "junit.xml"
    path.write_text(
        f'<testsuites><testsuite name="pytest"><testcase classname="tests.contracts.test_x" '
        f'name="{name}">{inner}</testcase></testsuite></testsuites>'
    )
    return str(path)


def test_a_skipped_test_is_not_proof(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    junit = _junit(tmp_path, "test_bug", '<skipped message="needs real Mongo"/>')

    assert report.cmd_regression_proof_verdict([junit]) == 1

    out = capsys.readouterr().out
    assert "SKIPPED on base" in out
    assert "PASS on base" not in out


def test_a_failure_on_base_is_proof(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    junit = _junit(tmp_path, "test_bug", '<failure message="assert False"/>')

    assert report.cmd_regression_proof_verdict([junit]) == 0
    assert "fail on base as required" in capsys.readouterr().out


def test_a_pass_on_base_still_fails_the_lane(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    junit = _junit(tmp_path, "test_bug", "")

    assert report.cmd_regression_proof_verdict([junit]) == 1
    assert "PASS on base" in capsys.readouterr().out
