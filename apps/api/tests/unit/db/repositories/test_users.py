"""Hermetic unit tests for ``UserRepository``'s write-miss cache eviction.

A user document deleted from Mongo while its entity cache entry was still live
kept authenticating: reads were served from cache while every write matched no
document (``PATCH /onboarding/preferences`` answered 404 "user not found"). The
base raw-update seam now evicts the targeted entity key when the write matches
nothing, so the next auth read misses, re-reads Mongo and 401s honestly. The
driver is mocked at ``app.db.repositories.base.get_async_collection``, the single
seam every read and write in the base repository goes through.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from bson import ObjectId
import pytest

from app.constants.cache import REPO_GLOBAL_SCOPE
from app.db.repositories.users import UserRepository
from app.models.user_models import OnboardingPreferences

USER_ID = "68d1f8a2c3b4a5d6e7f80912"
NOW = datetime(2026, 9, 2, 9, 0, tzinfo=UTC)


def _raw() -> dict[str, Any]:
    return {
        "_id": ObjectId(USER_ID),
        "email": "deleted@example.com",
        "created_at": NOW,
        "updated_at": NOW,
    }


@pytest.fixture
def collection() -> Iterator[MagicMock]:
    mock = MagicMock()
    mock.find_one_and_update = AsyncMock(return_value=None)
    with patch("app.db.repositories.base.get_async_collection", return_value=mock):
        yield mock


@pytest.fixture
def repo() -> UserRepository:
    return UserRepository()


def _evict_spy(repo: UserRepository) -> list[tuple[str, str]]:
    calls: list[tuple[str, str]] = []

    async def _cache_evict(scope: str, doc_id: str) -> None:
        calls.append((scope, doc_id))

    repo._cache_evict = _cache_evict  # type: ignore[method-assign]  # test observes the invalidation seam
    return calls


class TestUpdateOnboardingPreferences:
    async def test_a_write_matching_no_user_evicts_that_user_s_cache_entry(
        self, repo: UserRepository, collection: MagicMock
    ) -> None:
        evictions = _evict_spy(repo)

        result = await repo.update_onboarding_preferences(
            USER_ID, OnboardingPreferences(profession="engineer")
        )

        assert result is None
        assert evictions == [(REPO_GLOBAL_SCOPE, USER_ID)]

    async def test_a_matching_write_does_not_evict_the_entity_key(
        self, repo: UserRepository, collection: MagicMock
    ) -> None:
        collection.find_one_and_update = AsyncMock(return_value=_raw())
        evictions = _evict_spy(repo)

        result = await repo.update_onboarding_preferences(
            USER_ID, OnboardingPreferences(profession="engineer")
        )

        assert result is not None
        assert evictions == []
