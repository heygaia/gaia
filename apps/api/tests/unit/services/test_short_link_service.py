"""Unit tests for short_link_service — the mint loop's DuplicateKeyError branching.

The repository is mocked at the seam. The two unique indexes the loop races
against (``slug_unique``, ``user_target_live_unique``) are enforced for real in
``tests/contracts/test_short_links_repository.py``.
"""

from unittest.mock import AsyncMock, patch

from pymongo.errors import DuplicateKeyError
import pytest

from app.db.repositories.short_links import LIVE_TARGET_UNIQUE_INDEX, SLUG_UNIQUE_INDEX
from app.models.short_link_models import ShortLink
from app.services.short_link_service import ShortLinkExhaustedError, get_or_create_short_link


def _dup(index: str) -> DuplicateKeyError:
    """A DuplicateKeyError shaped exactly like Mongo raises it for ``index``."""
    msg = f"E11000 duplicate key error collection: gaia.short_links index: {index} dup key: {{ x: 1 }}"
    return DuplicateKeyError(msg, 11000, {"errmsg": msg, "code": 11000})


def _link(slug: str) -> ShortLink:
    return ShortLink(slug=slug, user_id="u", target_type="todo_canvas", target_id="t1")


@pytest.fixture
def repo():
    with patch("app.services.short_link_service.short_link_repository") as repo:
        repo.refresh_for_target = AsyncMock(return_value=None)
        repo.create = AsyncMock()
        yield repo


class TestGetOrCreateShortLinkRaces:
    async def test_losing_a_concurrent_mint_hands_out_the_winners_slug(self, repo):
        """Two overlapping mints for one target: the loser must return the
        winner's link, never mint a second live one."""
        repo.refresh_for_target.side_effect = [None, _link("winner")]
        repo.create.side_effect = _dup(LIVE_TARGET_UNIQUE_INDEX)

        url = await get_or_create_short_link("u", "todo_canvas", "t1")

        assert url.endswith("/winner")
        assert repo.create.await_count == 1

    async def test_the_winner_revoked_before_the_reread_mints_again(self, repo):
        repo.refresh_for_target.side_effect = [None, None]
        repo.create.side_effect = [_dup(LIVE_TARGET_UNIQUE_INDEX), _link("fresh")]

        url = await get_or_create_short_link("u", "todo_canvas", "t1")

        assert url.endswith("/fresh")
        assert repo.create.await_count == 2

    async def test_a_slug_collision_draws_another_slug(self, repo):
        repo.create.side_effect = [_dup(SLUG_UNIQUE_INDEX), _link("second")]

        url = await get_or_create_short_link("u", "todo_canvas", "t1")

        assert url.endswith("/second")
        assert repo.create.await_count == 2
        assert repo.refresh_for_target.await_count == 1

    async def test_an_unrecognised_unique_violation_propagates(self, repo):
        repo.create.side_effect = _dup("some_other_index")

        with pytest.raises(DuplicateKeyError):
            await get_or_create_short_link("u", "todo_canvas", "t1")

    async def test_slug_exhaustion_fails_loudly(self, repo):
        repo.create.side_effect = _dup(SLUG_UNIQUE_INDEX)

        with pytest.raises(ShortLinkExhaustedError):
            await get_or_create_short_link("u", "todo_canvas", "t1")
