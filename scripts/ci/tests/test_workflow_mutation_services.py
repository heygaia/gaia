"""The mutation shard job must bring up the services its mapped tests need.

The contract tier is in the mutation test set, and its fixtures skip without
USE_REAL_SERVICES=1 and live Mongo/Redis — or, worse, error on connect if the
variable is set and the services are not there, and an erroring test kills
every mutant it touches. The composite is what makes both impossible: it
starts the services for this runner instance and exports the variable. And a
lane that takes the shared box's service namespace has to hand it back.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
CODE_QUALITY_YML = REPO_ROOT / ".github" / "workflows" / "code-quality.yml"


@pytest.fixture(scope="module")
def shard_steps() -> list[dict[str, Any]]:
    workflow = yaml.safe_load(CODE_QUALITY_YML.read_text())
    return workflow["jobs"]["test-mutation"]["steps"]


def test_the_shard_installs_through_the_composite_that_starts_services(
    shard_steps: list[dict[str, Any]],
) -> None:
    uses = [step.get("uses", "") for step in shard_steps]
    assert "./.github/actions/setup-python-test-env" in uses
    assert "./.github/actions/setup-uv" not in uses, "the composite owns the install"
    assert not any("uv sync" in step.get("run", "") for step in shard_steps), (
        "a hand-rolled uv sync bypasses the composite's caches and its services"
    )


def test_the_shard_releases_the_services_it_took(shard_steps: list[dict[str, Any]]) -> None:
    always = [step for step in shard_steps if step.get("if") == "always()"]
    runs = [step.get("run", "") for step in always]
    assert any("test-services.sh down" in run for run in runs)
    assert any("embedding-sidecar.sh stop" in run for run in runs)
