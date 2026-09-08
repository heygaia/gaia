"""Unit tests for app/agents/tools/research_tool.py — deep_research tool.

Covers:
- User auth check (no user_id)
- Invalid depth
- Cache hit path
- No sources found
- Successful research with fetch fallback chains
- Exception in main try block
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

MODULE = "app.agents.tools.research_tool"


def _make_config(user_id: str | None = "user-123") -> dict[str, Any]:
    """Build a minimal RunnableConfig-like dict."""
    return {"configurable": {"user_id": user_id}}


def _no_user_config() -> dict[str, Any]:
    return {"configurable": {}}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _patch_stream_writer():
    """Patch get_stream_writer so the tool can call writer() without LangGraph context."""
    writer = MagicMock()
    with patch(f"{MODULE}.get_stream_writer", return_value=writer):
        yield writer


@pytest.fixture(autouse=True)
def _patch_log():
    with patch(f"{MODULE}.log"):
        yield


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestDeepResearch:
    """Tests for the deep_research tool function."""

    @pytest.mark.asyncio
    @patch(f"{MODULE}.get_user_id_from_config", return_value=None)
    async def test_no_user_returns_error(self, _mock_uid: MagicMock) -> None:
        from app.agents.tools.research_tool import deep_research

        result = await deep_research.ainvoke(
            {"query": "test", "scope": "", "depth": 2, "focus_areas": None},
            config=_no_user_config(),
        )
        assert result["error"] == "User authentication required"
        assert result["data"] is None

    @pytest.mark.asyncio
    @patch(f"{MODULE}.get_user_id_from_config", return_value="user-123")
    async def test_invalid_depth_returns_error(self, _mock_uid: MagicMock) -> None:
        from app.agents.tools.research_tool import deep_research

        result = await deep_research.ainvoke(
            {"query": "test", "scope": "", "depth": 5, "focus_areas": None},
            config=_make_config(),
        )
        assert "Invalid depth" in result["error"]
        assert result["data"] is None

    @pytest.mark.asyncio
    @patch(f"{MODULE}.get_user_id_from_config", return_value="user-123")
    @patch(f"{MODULE}.build_research_cache_key", return_value="cache:key")
    @patch(f"{MODULE}.get_cache")
    async def test_cache_hit(
        self,
        mock_get_cache: AsyncMock,
        _mock_cache_key: MagicMock,
        _mock_uid: MagicMock,
        _patch_stream_writer: MagicMock,
    ) -> None:
        cached = {
            "query": "test",
            "sources": [{"url": "https://a.com"}],
            "source_count": 1,
        }
        mock_get_cache.return_value = cached

        from app.agents.tools.research_tool import deep_research

        result = await deep_research.ainvoke(
            {"query": "test", "scope": "", "depth": 2, "focus_areas": None},
            config=_make_config(),
        )
        assert result["cached"] is True
        assert result["query"] == "test"
        _patch_stream_writer.assert_any_call({"progress": "Loaded research from cache!"})

    @pytest.mark.asyncio
    @patch(f"{MODULE}.get_user_id_from_config", return_value="user-123")
    @patch(f"{MODULE}.build_research_cache_key", return_value="cache:key")
    @patch(f"{MODULE}.get_cache", new_callable=AsyncMock, return_value=None)
    @patch(f"{MODULE}.decompose_research_queries", new_callable=AsyncMock)
    @patch(f"{MODULE}.search_for_research", new_callable=AsyncMock)
    @patch(f"{MODULE}.rank_and_deduplicate_urls")
    async def test_no_sources_found(
        self,
        mock_rank: MagicMock,
        mock_ddg: AsyncMock,
        mock_decompose: AsyncMock,
        _mock_cache: AsyncMock,
        _mock_cache_key: MagicMock,
        _mock_uid: MagicMock,
    ) -> None:
        mock_decompose.return_value = ["sub-q1"]
        mock_ddg.return_value = {"results": []}
        mock_rank.return_value = []

        from app.agents.tools.research_tool import deep_research

        result = await deep_research.ainvoke(
            {"query": "obscure topic", "scope": "", "depth": 1, "focus_areas": None},
            config=_make_config(),
        )
        # Pinned whole: an empty search is exactly when a model invents links,
        # so the refusal has to name the ban rather than only report the miss.
        assert result["error"] == (
            "Search returned no results for the given query. "
            "No URLs were found: do not fabricate links. "
            "Try broadening the search or inform the user that no sources were found."
        )
        assert result["data"] is None

    @pytest.mark.asyncio
    @patch(f"{MODULE}.get_user_id_from_config", return_value="user-123")
    @patch(f"{MODULE}.build_research_cache_key", return_value="cache:key")
    @patch(f"{MODULE}.get_cache", new_callable=AsyncMock, return_value=None)
    @patch(f"{MODULE}.set_cache", new_callable=AsyncMock)
    @patch(f"{MODULE}.decompose_research_queries", new_callable=AsyncMock)
    @patch(f"{MODULE}.search_for_research", new_callable=AsyncMock)
    @patch(f"{MODULE}.rank_and_deduplicate_urls")
    @patch(f"{MODULE}.batch_fetch_with_crawl4ai", new_callable=AsyncMock)
    async def test_successful_research_crawl4ai(
        self,
        mock_batch_crawl4ai: AsyncMock,
        mock_rank: MagicMock,
        mock_ddg: AsyncMock,
        mock_decompose: AsyncMock,
        mock_set_cache: AsyncMock,
        _mock_cache: AsyncMock,
        _mock_cache_key: MagicMock,
        _mock_uid: MagicMock,
        _patch_stream_writer: MagicMock,
    ) -> None:
        mock_decompose.return_value = ["sub-q1", "sub-q2"]
        mock_ddg.return_value = {"results": [{"url": "https://example.com"}]}
        mock_rank.return_value = [
            {"url": "https://example.com", "snippet": "A snippet"},
            {"url": "https://example2.com", "snippet": "Another snippet"},
        ]
        mock_batch_crawl4ai.return_value = (
            {
                "https://example.com": "Full page content",
                "https://example2.com": "Full page content",
            },
            {},
        )

        from app.agents.tools.research_tool import deep_research

        result = await deep_research.ainvoke(
            {
                "query": "AI trends",
                "scope": "technical",
                "depth": 1,
                "focus_areas": ["performance"],
            },
            config=_make_config(),
        )
        assert result["error"] is None
        assert result["cached"] is False
        assert result["source_count"] == 2
        assert len(result["sources"]) == 2
        assert result["query"] == "AI trends"
        assert result["scope"] == "technical"
        # The integrity note is what stops a research answer citing plausible
        # URLs the search never returned — the whole reason the source list is
        # handed over separately.
        assert result["integrity_note"] == (
            "All URLs in `sources` and `authoritative_urls` were returned by real search "
            "queries. Only cite URLs from this list; never invent or guess URLs."
        )
        # The progress frame is keyed "progress"; the UI reads that key and
        # nothing else, so a renamed key is a silently blank progress line.
        progress = [
            call.args[0]["progress"]
            for call in _patch_stream_writer.call_args_list
            if isinstance(call.args[0], dict) and "progress" in call.args[0]
        ]
        assert "Found 2 unique sources, fetching full content..." in progress
        mock_set_cache.assert_awaited_once()

    @pytest.mark.asyncio
    @patch(f"{MODULE}.get_user_id_from_config", return_value="user-123")
    @patch(f"{MODULE}.build_research_cache_key", return_value="cache:key")
    @patch(f"{MODULE}.get_cache", new_callable=AsyncMock, return_value=None)
    @patch(f"{MODULE}.set_cache", new_callable=AsyncMock)
    @patch(f"{MODULE}.decompose_research_queries", new_callable=AsyncMock)
    @patch(f"{MODULE}.search_for_research", new_callable=AsyncMock)
    @patch(f"{MODULE}.rank_and_deduplicate_urls")
    @patch(
        f"{MODULE}.batch_fetch_with_crawl4ai",
        new_callable=AsyncMock,
    )
    @patch(f"{MODULE}.fetch_with_httpx", new_callable=AsyncMock)
    async def test_crawl4ai_fails_falls_back_to_httpx(
        self,
        mock_httpx: AsyncMock,
        mock_batch_crawl4ai: AsyncMock,
        mock_rank: MagicMock,
        mock_ddg: AsyncMock,
        mock_decompose: AsyncMock,
        mock_set_cache: AsyncMock,
        _mock_cache: AsyncMock,
        _mock_cache_key: MagicMock,
        _mock_uid: MagicMock,
    ) -> None:
        mock_decompose.return_value = ["sub-q1"]
        mock_ddg.return_value = {"results": [{"url": "https://a.com"}]}
        mock_rank.return_value = [{"url": "https://a.com", "snippet": "snip"}]
        mock_batch_crawl4ai.return_value = ({}, {"https://a.com": "crawl fail"})
        mock_httpx.return_value = "httpx content"

        from app.agents.tools.research_tool import deep_research

        result = await deep_research.ainvoke(
            {"query": "test", "scope": "", "depth": 1, "focus_areas": None},
            config=_make_config(),
        )
        assert result["error"] is None
        assert result["sources"][0]["content"] == "httpx content"

    @pytest.mark.asyncio
    @patch(f"{MODULE}.get_user_id_from_config", return_value="user-123")
    @patch(f"{MODULE}.build_research_cache_key", return_value="cache:key")
    @patch(f"{MODULE}.get_cache", new_callable=AsyncMock, return_value=None)
    @patch(f"{MODULE}.set_cache", new_callable=AsyncMock)
    @patch(f"{MODULE}.decompose_research_queries", new_callable=AsyncMock)
    @patch(f"{MODULE}.search_for_research", new_callable=AsyncMock)
    @patch(f"{MODULE}.rank_and_deduplicate_urls")
    @patch(
        f"{MODULE}.batch_fetch_with_crawl4ai",
        new_callable=AsyncMock,
    )
    @patch(
        f"{MODULE}.fetch_with_httpx",
        new_callable=AsyncMock,
        side_effect=Exception("fail"),
    )
    async def test_all_fetchers_fail_uses_snippet(
        self,
        mock_httpx: AsyncMock,
        mock_batch_crawl4ai: AsyncMock,
        mock_rank: MagicMock,
        mock_ddg: AsyncMock,
        mock_decompose: AsyncMock,
        mock_set_cache: AsyncMock,
        _mock_cache: AsyncMock,
        _mock_cache_key: MagicMock,
        _mock_uid: MagicMock,
    ) -> None:
        mock_decompose.return_value = ["sub-q1"]
        mock_ddg.return_value = {"results": [{"url": "https://a.com"}]}
        mock_rank.return_value = [{"url": "https://a.com", "snippet": "Search snippet text"}]
        mock_batch_crawl4ai.return_value = ({}, {"https://a.com": "fail"})

        from app.agents.tools.research_tool import deep_research

        result = await deep_research.ainvoke(
            {"query": "test", "scope": "", "depth": 1, "focus_areas": None},
            config=_make_config(),
        )
        assert result["error"] is None
        assert "Snippet only" in result["sources"][0]["content"]
        assert result["sources"][0]["fetch_error"] is not None

    @pytest.mark.asyncio
    @patch(f"{MODULE}.get_user_id_from_config", return_value="user-123")
    @patch(f"{MODULE}.build_research_cache_key", return_value="cache:key")
    @patch(f"{MODULE}.get_cache", new_callable=AsyncMock, return_value=None)
    @patch(f"{MODULE}.set_cache", new_callable=AsyncMock)
    @patch(f"{MODULE}.decompose_research_queries", new_callable=AsyncMock)
    @patch(f"{MODULE}.search_for_research", new_callable=AsyncMock)
    @patch(f"{MODULE}.rank_and_deduplicate_urls")
    @patch(
        f"{MODULE}.batch_fetch_with_crawl4ai",
        new_callable=AsyncMock,
    )
    @patch(
        f"{MODULE}.fetch_with_httpx",
        new_callable=AsyncMock,
        side_effect=Exception("fail"),
    )
    async def test_all_fetchers_fail_no_snippet_returns_null_content(
        self,
        mock_httpx: AsyncMock,
        mock_batch_crawl4ai: AsyncMock,
        mock_rank: MagicMock,
        mock_ddg: AsyncMock,
        mock_decompose: AsyncMock,
        mock_set_cache: AsyncMock,
        _mock_cache: AsyncMock,
        _mock_cache_key: MagicMock,
        _mock_uid: MagicMock,
    ) -> None:
        mock_decompose.return_value = ["sub-q1"]
        mock_ddg.return_value = {"results": [{"url": "https://a.com"}]}
        mock_rank.return_value = [{"url": "https://a.com", "snippet": ""}]
        mock_batch_crawl4ai.return_value = ({}, {"https://a.com": "fail"})

        from app.agents.tools.research_tool import deep_research

        result = await deep_research.ainvoke(
            {"query": "test", "scope": "", "depth": 1, "focus_areas": None},
            config=_make_config(),
        )
        # No valid sources (content is None), so source_count = 0
        assert result["error"] is None
        assert result["source_count"] == 0
        # No valid sources means cache is NOT set
        mock_set_cache.assert_not_awaited()

    @pytest.mark.asyncio
    @patch(f"{MODULE}.get_user_id_from_config", return_value="user-123")
    @patch(f"{MODULE}.build_research_cache_key", return_value="cache:key")
    @patch(f"{MODULE}.get_cache", new_callable=AsyncMock, return_value=None)
    @patch(
        f"{MODULE}.decompose_research_queries",
        new_callable=AsyncMock,
        side_effect=RuntimeError("boom"),
    )
    async def test_exception_in_main_try_block(
        self,
        mock_decompose: AsyncMock,
        _mock_cache: AsyncMock,
        _mock_cache_key: MagicMock,
        _mock_uid: MagicMock,
    ) -> None:
        from app.agents.tools.research_tool import deep_research

        result = await deep_research.ainvoke(
            {"query": "test", "scope": "", "depth": 2, "focus_areas": None},
            config=_make_config(),
        )
        assert result["error"] == "boom"
        assert result["data"] is None

    @pytest.mark.asyncio
    @patch(f"{MODULE}.get_user_id_from_config", return_value="user-123")
    @patch(f"{MODULE}.build_research_cache_key", return_value="cache:key")
    @patch(f"{MODULE}.get_cache", new_callable=AsyncMock, return_value=None)
    @patch(f"{MODULE}.set_cache", new_callable=AsyncMock)
    @patch(f"{MODULE}.decompose_research_queries", new_callable=AsyncMock)
    @patch(f"{MODULE}.search_for_research", new_callable=AsyncMock)
    @patch(f"{MODULE}.rank_and_deduplicate_urls")
    @patch(f"{MODULE}.batch_fetch_with_crawl4ai", new_callable=AsyncMock)
    async def test_depth_3_max_sources(
        self,
        mock_batch_crawl4ai: AsyncMock,
        mock_rank: MagicMock,
        mock_ddg: AsyncMock,
        mock_decompose: AsyncMock,
        mock_set_cache: AsyncMock,
        _mock_cache: AsyncMock,
        _mock_cache_key: MagicMock,
        _mock_uid: MagicMock,
    ) -> None:
        """Depth 3 should pass max_urls=20 to rank_and_deduplicate_urls."""
        mock_decompose.return_value = ["q1"]
        mock_ddg.return_value = {"results": [{"url": "https://a.com"}]}
        mock_rank.return_value = [{"url": "https://a.com", "snippet": "s"}]
        mock_batch_crawl4ai.return_value = ({"https://a.com": "content"}, {})

        from app.agents.tools.research_tool import deep_research

        await deep_research.ainvoke(
            {"query": "test", "scope": "", "depth": 3, "focus_areas": None},
            config=_make_config(),
        )
        mock_rank.assert_called_once()
        _, kwargs = mock_rank.call_args
        assert kwargs.get("max_urls") == 20 or mock_rank.call_args[0][1] == 20

    @pytest.mark.asyncio
    @patch(f"{MODULE}.get_user_id_from_config", return_value="user-123")
    @patch(f"{MODULE}.build_research_cache_key", return_value="cache:key")
    @patch(f"{MODULE}.get_cache", new_callable=AsyncMock, return_value=None)
    @patch(f"{MODULE}.set_cache", new_callable=AsyncMock)
    @patch(f"{MODULE}.decompose_research_queries", new_callable=AsyncMock)
    @patch(f"{MODULE}.search_for_research", new_callable=AsyncMock)
    @patch(f"{MODULE}.rank_and_deduplicate_urls")
    @patch(f"{MODULE}.batch_fetch_with_crawl4ai", new_callable=AsyncMock)
    async def test_search_exceptions_counted_correctly(
        self,
        mock_batch_crawl4ai: AsyncMock,
        mock_rank: MagicMock,
        mock_ddg: AsyncMock,
        mock_decompose: AsyncMock,
        mock_set_cache: AsyncMock,
        _mock_cache: AsyncMock,
        _mock_cache_key: MagicMock,
        _mock_uid: MagicMock,
        _patch_stream_writer: MagicMock,
    ) -> None:
        """When some searches raise exceptions, successful_searches count is correct."""
        mock_decompose.return_value = ["q1", "q2", "q3"]
        mock_ddg.side_effect = [
            {"results": [{"url": "https://a.com"}]},
            RuntimeError("search failed"),
            {"results": []},
        ]
        mock_rank.return_value = [{"url": "https://a.com", "snippet": "s"}]
        mock_batch_crawl4ai.return_value = ({"https://a.com": "content"}, {})

        from app.agents.tools.research_tool import deep_research

        result = await deep_research.ainvoke(
            {"query": "test", "scope": "", "depth": 1, "focus_areas": None},
            config=_make_config(),
        )
        assert result["error"] is None
        # Check progress message: 1/3 searches returned results
        progress_calls = [
            call.args[0]
            for call in _patch_stream_writer.call_args_list
            if isinstance(call.args[0], dict) and "progress" in call.args[0]
        ]
        found = any("1/3" in p.get("progress", "") for p in progress_calls)
        assert found, (
            f"Expected '1/3 searches returned results' in progress calls: {progress_calls}"
        )


# ---------------------------------------------------------------------------
# _fetch_source_contents — the three-tier resolution of a ranked URL
# ---------------------------------------------------------------------------


class TestFetchSourceContents:
    """The tiering itself: crawl4ai batch → httpx → search snippet, and the
    progress frames the UI counts sources with."""

    @staticmethod
    def _writer_frames(writer: MagicMock) -> list[dict[str, Any]]:
        return [call.args[0] for call in writer.call_args_list]

    @pytest.mark.asyncio
    async def test_batch_content_wins_and_reports_progress(self) -> None:
        from app.agents.tools.research_tool import _fetch_source_contents

        writer = MagicMock()
        with patch(f"{MODULE}.fetch_with_httpx", new_callable=AsyncMock) as httpx:
            sources = await _fetch_source_contents(
                [{"url": "https://a.com", "snippet": "s"}],
                {"https://a.com": "page body"},
                {},
                writer,
            )

        httpx.assert_not_awaited()
        assert sources == [
            {
                "url": "https://a.com",
                "snippet": "s",
                "content": "page body",
                "fetch_error": None,
            }
        ]
        assert self._writer_frames(writer) == [{"progress": "Fetched source 1/1..."}]

    @pytest.mark.asyncio
    async def test_blank_batch_content_falls_through_to_httpx(self) -> None:
        """crawl4ai returning whitespace is a miss, not a hit -- a blank page
        must not be handed to the model as the source's content."""
        from app.agents.tools.research_tool import _fetch_source_contents

        writer = MagicMock()
        with patch(
            f"{MODULE}.fetch_with_httpx", new_callable=AsyncMock, return_value="real body"
        ) as httpx:
            sources = await _fetch_source_contents(
                [{"url": "https://a.com", "snippet": "s"}], {"https://a.com": "   "}, {}, writer
            )

        httpx.assert_awaited_once_with("https://a.com")
        assert sources[0]["content"] == "real body"
        assert sources[0]["fetch_error"] is None
        assert self._writer_frames(writer) == [{"progress": "Fetched source 1/1..."}]

    @pytest.mark.asyncio
    async def test_progress_counts_each_source_once_over_the_total(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The counter is what the UI renders as "2/3 fetched" -- it has to
        advance by exactly one per resolved source and be bounded by the total."""
        monkeypatch.setattr(f"{MODULE}.DEEP_RESEARCH_FALLBACK_SEMAPHORE_COUNT", 1)
        from app.agents.tools.research_tool import _fetch_source_contents

        writer = MagicMock()
        ranked = [{"url": f"https://{n}.com", "snippet": "s"} for n in "abc"]
        with patch(f"{MODULE}.fetch_with_httpx", new_callable=AsyncMock, return_value="via httpx"):
            await _fetch_source_contents(
                ranked, {"https://a.com": "batched"}, {"https://c.com": "boom"}, writer
            )

        assert self._writer_frames(writer) == [
            {"progress": "Fetched source 1/3..."},
            {"progress": "Fetched source 2/3..."},
            {"progress": "Fetched source 3/3..."},
        ]

    @pytest.mark.asyncio
    async def test_snippet_fallback_still_advances_the_counter(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A source that only yields a snippet is still a resolved source: it
        emits no frame of its own, but the source after it must be numbered
        3/3 rather than repeating the number the snippet consumed."""
        monkeypatch.setattr(f"{MODULE}.DEEP_RESEARCH_FALLBACK_SEMAPHORE_COUNT", 1)
        from app.agents.tools.research_tool import _fetch_source_contents

        writer = MagicMock()
        with patch(
            f"{MODULE}.fetch_with_httpx", new_callable=AsyncMock, side_effect=Exception("down")
        ):
            await _fetch_source_contents(
                [
                    {"url": "https://a.com"},
                    {"url": "https://b.com", "snippet": "only a snippet"},
                    {"url": "https://c.com"},
                ],
                {"https://a.com": "batched", "https://c.com": "batched"},
                {},
                writer,
            )

        assert self._writer_frames(writer) == [
            {"progress": "Fetched source 1/3..."},
            {"progress": "Fetched source 3/3..."},
        ]

    @pytest.mark.asyncio
    async def test_snippet_fallback_reports_every_tier_that_failed(self) -> None:
        """``fetch_error`` is the only record of why the full page is missing --
        both tiers' reasons, joined, or a silent snippet looks like a real fetch."""
        from app.agents.tools.research_tool import _fetch_source_contents

        with patch(
            f"{MODULE}.fetch_with_httpx", new_callable=AsyncMock, side_effect=Exception("timeout")
        ):
            (source,) = await _fetch_source_contents(
                [{"url": "https://a.com", "snippet": "the snippet"}],
                {},
                {"https://a.com": "403 blocked"},
                MagicMock(),
            )

        assert source["content"] == "[Snippet only: full page unavailable]\n\nthe snippet"
        assert source["fetch_error"] == "crawl4ai: 403 blocked; httpx: timeout"

    @pytest.mark.asyncio
    async def test_missing_crawl_error_is_reported_as_no_content(self) -> None:
        from app.agents.tools.research_tool import _fetch_source_contents

        with patch(
            f"{MODULE}.fetch_with_httpx", new_callable=AsyncMock, side_effect=Exception("timeout")
        ):
            (source,) = await _fetch_source_contents(
                [{"url": "https://a.com", "snippet": "the snippet"}], {}, {}, MagicMock()
            )

        assert source["fetch_error"] == "crawl4ai: returned no content; httpx: timeout"

    @pytest.mark.asyncio
    async def test_no_snippet_at_all_yields_null_content(self) -> None:
        """A source with no snippet key must resolve to ``content: None`` -- the
        caller drops those, and a placeholder would be cited as if it were real."""
        from app.agents.tools.research_tool import _fetch_source_contents

        with patch(
            f"{MODULE}.fetch_with_httpx", new_callable=AsyncMock, side_effect=Exception("timeout")
        ):
            (source,) = await _fetch_source_contents(
                [{"url": "https://a.com"}], {}, {"https://a.com": "403"}, MagicMock()
            )

        assert source == {
            "url": "https://a.com",
            "content": None,
            "fetch_error": "crawl4ai: 403; httpx: timeout",
        }

    @pytest.mark.asyncio
    async def test_whitespace_only_snippet_yields_null_content(self) -> None:
        from app.agents.tools.research_tool import _fetch_source_contents

        with patch(
            f"{MODULE}.fetch_with_httpx", new_callable=AsyncMock, side_effect=Exception("timeout")
        ):
            (source,) = await _fetch_source_contents(
                [{"url": "https://a.com", "snippet": "   "}], {}, {}, MagicMock()
            )

        assert source["content"] is None

    @pytest.mark.asyncio
    async def test_snippet_fallback_is_logged_against_the_url(self) -> None:
        """The wide event is the only place a degraded source shows up, so the
        warning has to name both the fallback and which URL took it."""
        from app.agents.tools.research_tool import _fetch_source_contents

        with (
            patch(f"{MODULE}.log") as mock_log,
            patch(f"{MODULE}.fetch_with_httpx", new_callable=AsyncMock, side_effect=Exception("x")),
        ):
            await _fetch_source_contents(
                [{"url": "https://a.com", "snippet": "s"}], {}, {}, MagicMock()
            )

        mock_log.warning.assert_called_once()
        message, kwargs = mock_log.warning.call_args
        assert "All fetchers failed, using search snippet" in message[0]
        assert kwargs == {"url": "https://a.com"}
