"""A mutation shard must run where its mapped tests can actually connect.

The contract tier is in the mutation test set, and its fixtures skip without
USE_REAL_SERVICES=1 and live Mongo/Redis — or, worse, error on connect if the
variable is set and the services are not there, and an erroring test kills
every mutant it touches.

The composite that starts those services cannot run on the lint pool, and that
is arithmetic rather than policy: those runner instances are numbered 13-20 and
`test-services.sh prepare` serves lanes 0-12 (MAX_LANE — Redis is provisioned
for 13 stripes), so it rejects the lane and the job dies in setup. All six
mutation shards died that way on run 34584038269, the first run after the
composite was added to the whole job.

So the lane is split by pool: `mutation.sh plan` marks each shard, a second
runner selection exists for the services pool, `runs-on` picks between them,
and every services-only step is conditioned on the same marker. These tests pin
all four halves, because any one of them alone puts the shards back on a runner
that cannot serve them.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
CODE_QUALITY_YML = REPO_ROOT / ".github" / "workflows" / "code-quality.yml"

SERVICES_POOL = "matrix.pool == 'services'"
LINT_POOL = "matrix.pool != 'services'"
SERVICES_SELECTION = "select-runner-services"
# The pool main.yml's service-backed lanes already use; the only one whose
# instances test-services.sh will serve.
SERVICES_LABEL = "gaia-home"


@pytest.fixture(scope="module")
def workflow() -> dict[str, Any]:
    return yaml.safe_load(CODE_QUALITY_YML.read_text())


@pytest.fixture(scope="module")
def shard(workflow: dict[str, Any]) -> dict[str, Any]:
    return workflow["jobs"]["test-mutation"]


@pytest.fixture(scope="module")
def shard_steps(shard: dict[str, Any]) -> list[dict[str, Any]]:
    return shard["steps"]


def _step(steps: list[dict[str, Any]], key: str, value: str) -> dict[str, Any]:
    for step in steps:
        if value in str(step.get(key, "")):
            return step
    raise AssertionError(f"no step whose {key} contains {value!r}")


def test_a_second_selection_exists_for_the_services_pool(workflow: dict[str, Any]) -> None:
    job = workflow["jobs"][SERVICES_SELECTION]
    pick = _step(job["steps"], "uses", "./.github/actions/select-runner")

    assert pick["with"]["runner-label"] == SERVICES_LABEL, (
        "the services selection must probe the pool that can serve test-services "
        f"lanes, not {pick['with']['runner-label']!r}"
    )


def test_the_services_selection_keeps_the_secret_off_the_pr_head(
    workflow: dict[str, Any],
) -> None:
    # It hands HOMELAB_GH_PAT to a script from the checkout, exactly as
    # select-runner does, so it checks out the DEFAULT BRANCH rather than code
    # the PR author controls.
    checkout = _step(workflow["jobs"][SERVICES_SELECTION]["steps"], "uses", "actions/checkout@")

    assert checkout["with"]["ref"] == "${{ github.event.repository.default_branch }}"
    assert checkout["with"]["persist-credentials"] is False


def test_the_shard_picks_its_runner_from_the_pool_the_plan_assigned(
    shard: dict[str, Any],
) -> None:
    runs_on = shard["runs-on"]

    assert "matrix.pool" in runs_on, "the shard runs on one fixed pool, whatever it maps"
    assert f"needs.{SERVICES_SELECTION}.outputs.runner" in runs_on
    assert "needs.select-runner.outputs.runner" in runs_on


def test_both_selections_are_declared_as_needs(shard: dict[str, Any]) -> None:
    # `runs-on` is resolved before the job starts; an output from a job not in
    # `needs` evaluates to empty and the shard lands on a nameless runner.
    assert SERVICES_SELECTION in shard["needs"]
    assert "select-runner" in shard["needs"]


def test_only_a_services_shard_starts_the_services(shard_steps: list[dict[str, Any]]) -> None:
    composite = _step(shard_steps, "uses", "./.github/actions/setup-python-test-env")

    assert composite.get("if") == SERVICES_POOL, (
        "unconditional, this composite runs on the lint pool too — where "
        "test-services.sh rejects the lane number and the job dies in setup"
    )


def test_a_lint_shard_still_gets_a_python_environment(
    shard_steps: list[dict[str, Any]],
) -> None:
    # It cannot use the services composite, so it installs the way every other
    # Python lane on that pool does — and it must still install SOMETHING:
    # mutmut and pytest come from the project venv.
    setup_uv = _step(shard_steps, "uses", "./.github/actions/setup-uv")
    sync = _step(shard_steps, "run", "uv sync")

    assert setup_uv.get("if") == LINT_POOL
    assert sync.get("if") == LINT_POOL


def test_only_a_services_shard_hands_the_namespace_back(
    shard_steps: list[dict[str, Any]],
) -> None:
    # Both halves matter: a services shard that keeps its lane leaks it until
    # the janitor runs, and a lint shard that releases one calls
    # test-services.sh with a lane it rejects — teardown failing is how a lane
    # goes red having passed.
    for fragment in ("test-services.sh down", "embedding-sidecar.sh stop"):
        step = _step(shard_steps, "run", fragment)
        assert step.get("if") == f"always() && {SERVICES_POOL}", (
            f"{fragment} runs on {step.get('if')!r}; it belongs to the services pool only"
        )


def test_the_gate_fails_when_the_services_selection_does(workflow: dict[str, Any]) -> None:
    # Without this, a failed services selection skips every contract-mapped
    # shard, and `consolidate` reads a skipped lane as a legitimate skip — a
    # green gate with the repository modules unmutated.
    assert SERVICES_SELECTION in workflow["jobs"]["quality-gate"]["needs"]
