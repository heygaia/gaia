"""Every harness test runs against a CPU-slot pool of its own.

The scripts under test source `lib/cpu-slots.sh`, and `mutation.sh shard` and
`pytest.sh slice` take nproc-2 host tokens before their first real step. Run on
the self-hosted box with the pool inherited, each sandboxed shard in this suite
queued behind the real mutation shards for the semaphore's full 600 s fail-open
wait, and the harness lane died at its cap with the last tests never reached
(job 103243166187) — invisible locally, where the governor is a no-op. A private
pool with room for any request keeps the semaphore code path live and the tests
off the host's budget.
"""

from __future__ import annotations

from pathlib import Path
import shutil

import pytest

# More than any lane requests (nproc-2 on the 16-core box), so a test only
# waits when it deliberately makes a smaller pool of its own.
PRIVATE_POOL_TOKENS = "64"


@pytest.fixture(autouse=True)
def _private_cpu_slot_pool(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GAIA_CPU_SLOTS_DIR", str(tmp_path / "cpu-slots"))
    monkeypatch.setenv("GAIA_CPU_TOKENS", PRIVATE_POOL_TOKENS)


@pytest.fixture
def flock() -> str:
    """The semaphore's atomicity primitive. Absent on a stock macOS dev box,
    where acquire fails open before it touches any pool — so a proof that
    needs the pool to be used skips here and runs on every Linux runner."""
    path = shutil.which("flock")
    if path is None:
        pytest.skip("flock absent (governor is Linux-box-only)")
    return path
