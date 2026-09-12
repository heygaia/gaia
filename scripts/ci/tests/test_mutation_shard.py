"""The mutation gate's shard runner (scripts/ci/mutation.sh shard): its CPU budget.

A shard forks one mutmut worker per child. The matrix's shards share the box's
nproc-2 core budget: each claiming the whole of it serialised them on the host
governor — three idled up to its fail-open, then ran oversubscribed — and a
packed shard timed out having done a third of its work. Driven as the real
script against a module that does not exist: the budget line prints before the
per-module loop, and the loop's failure afterwards is expected.
"""

import os
from pathlib import Path
import subprocess

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
CI = REPO_ROOT / "scripts" / "ci"

_GROUP = (
    '[{"module":"app/does_not_exist.py",'
    '"testfiles":"[\\"tests/unit/test_nope.py\\"]","ranges":"[[1,2]]"}]'
)


def _run_shard(tmp_path: Path, env: dict[str, str]) -> str:
    proc = subprocess.run(
        ["bash", str(CI / "mutation.sh"), "shard"],
        env={
            "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin",
            "HOME": str(tmp_path),
            "GROUP": _GROUP,
            "SHARD_LOG": str(tmp_path / "shard.log"),
            **env,
        },
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )
    return proc.stdout + proc.stderr


def _budget_line(output: str) -> str:
    lines = [line for line in output.splitlines() if line.startswith("cpu budget: ")]
    assert len(lines) == 1, output[-2000:]
    return lines[0]


def _whole_box() -> int:
    threads = os.cpu_count() or 2
    return threads - 2 if threads > 3 else 1


@pytest.mark.parametrize("shards", [1, 4])
def test_the_budget_is_nproc_minus_two_split_across_the_shards(tmp_path: Path, shards: int) -> None:
    expected = max(1, _whole_box() // shards)

    line = _budget_line(_run_shard(tmp_path, {"SHARD_COUNT": str(shards)}))

    assert line.startswith(f"cpu budget: {expected} mutmut child(ren)"), line
    assert f"shared by {shards} shard(s)" in line


def test_an_unplanned_shard_gets_the_whole_box(tmp_path: Path) -> None:
    # `mutation.sh local` and a hand-run shard set no SHARD_COUNT.
    line = _budget_line(_run_shard(tmp_path, {}))

    assert line.startswith(f"cpu budget: {_whole_box()} mutmut child(ren)"), line


def test_an_explicit_children_override_still_wins(tmp_path: Path) -> None:
    line = _budget_line(_run_shard(tmp_path, {"SHARD_COUNT": "4", "MUTMUT_MAX_CHILDREN": "2"}))

    assert line.startswith("cpu budget: 2 mutmut child(ren)"), line
