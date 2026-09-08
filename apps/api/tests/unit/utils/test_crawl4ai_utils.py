"""Unit tests for app.utils.crawl4ai_utils."""

import asyncio
from collections.abc import Awaitable
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from crawl4ai import BrowserConfig
import pytest

from app.config.settings import settings
from app.constants.browser import BrowserEngine


def _pin_engine(monkeypatch: pytest.MonkeyPatch, engine: BrowserEngine) -> None:
    monkeypatch.setattr(settings, "BROWSER_ENGINE", engine)


def _record_wait_for_timeouts(monkeypatch: pytest.MonkeyPatch) -> list[float | None]:
    """Record every deadline the module hands ``asyncio.wait_for``.

    The per-crawl recovery deadline never reaches an error message or a return
    value, so the timeout argument itself is the only place the computed
    deadline is observable without waiting out ten real seconds.
    """
    recorded: list[float | None] = []
    real_wait_for = asyncio.wait_for

    async def spy(awaitable: Awaitable[Any], timeout: float | None = None) -> Any:
        recorded.append(timeout)
        return await real_wait_for(awaitable, timeout)

    monkeypatch.setattr(asyncio, "wait_for", spy)
    return recorded


def _stub_crawler(mock_crawler_cls: MagicMock) -> AsyncMock:
    crawler_inst = AsyncMock()
    crawler_inst.__aenter__ = AsyncMock(return_value=crawler_inst)
    crawler_inst.__aexit__ = AsyncMock(return_value=False)
    mock_crawler_cls.return_value = crawler_inst
    return crawler_inst


class TestBatchFetchWithCrawl4ai:
    """The Chromium path: one crawler + ``arun_many`` with result matching."""

    @patch("app.utils.crawl4ai_utils.AsyncWebCrawler")
    async def test_matches_redirected_results_to_requested_urls(
        self, mock_crawler_cls: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _pin_engine(monkeypatch, BrowserEngine.CHROMIUM)
        result_example = MagicMock()
        result_example.success = True
        result_example.markdown = "example content"
        result_example.url = "https://example.com"
        result_example.redirected_url = "https://example.com/"

        result_httpbin = MagicMock()
        result_httpbin.success = True
        result_httpbin.markdown = "httpbin content"
        result_httpbin.url = "https://httpbin.org/redirect-to?url=https://example.com/"
        result_httpbin.redirected_url = "https://example.com/"

        # Deliberately reversed order to validate URL-based matching.
        crawler_inst = AsyncMock()
        crawler_inst.__aenter__ = AsyncMock(return_value=crawler_inst)
        crawler_inst.__aexit__ = AsyncMock(return_value=False)
        crawler_inst.arun_many = AsyncMock(return_value=[result_httpbin, result_example])
        mock_crawler_cls.return_value = crawler_inst

        from app.utils.crawl4ai_utils import CrawlBatchParams, batch_fetch_with_crawl4ai

        urls = [
            "https://example.com",
            "https://httpbin.org/redirect-to?url=https://example.com/",
        ]
        contents, errors = await batch_fetch_with_crawl4ai(
            urls,
            CrawlBatchParams(
                page_timeout_ms=30_000,
                total_timeout_seconds=60.0,
                semaphore_count=3,
                context_name="test",
            ),
        )

        assert errors == {}
        assert contents["https://example.com"] == "example content"
        assert (
            contents["https://httpbin.org/redirect-to?url=https://example.com/"]
            == "httpbin content"
        )

    @patch("app.utils.crawl4ai_utils.AsyncWebCrawler")
    async def test_batch_timeout_recovers_per_url(
        self, mock_crawler_cls: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _pin_engine(monkeypatch, BrowserEngine.CHROMIUM)
        success_result = MagicMock()
        success_result.success = True
        success_result.markdown = "ok"
        success_result.error_message = ""

        fail_result = MagicMock()
        fail_result.success = False
        fail_result.markdown = ""
        fail_result.error_message = "blocked"

        crawler_inst = AsyncMock()
        crawler_inst.__aenter__ = AsyncMock(return_value=crawler_inst)
        crawler_inst.__aexit__ = AsyncMock(return_value=False)
        crawler_inst.arun_many = AsyncMock(
            side_effect=[TimeoutError(), [success_result], [fail_result]]
        )
        mock_crawler_cls.return_value = crawler_inst

        from app.utils.crawl4ai_utils import CrawlBatchParams, batch_fetch_with_crawl4ai

        urls = ["https://good.example", "https://bad.example"]
        contents, errors = await batch_fetch_with_crawl4ai(
            urls,
            CrawlBatchParams(
                page_timeout_ms=30_000,
                total_timeout_seconds=20.0,
                semaphore_count=5,
                context_name="test",
            ),
        )

        assert contents["https://good.example"] == "ok"
        assert errors["https://bad.example"] == "blocked"


class TestBatchFetchObscura:
    """The Obscura path: one crawler+context per URL (arun), never ``arun_many``."""

    @patch(
        "app.utils.crawl4ai_utils.ensure_crawl_obscura",
        new_callable=AsyncMock,
        return_value="http://127.0.0.1:9223",
    )
    @patch("app.utils.crawl4ai_utils.AsyncWebCrawler")
    async def test_obscura_fans_out_per_url(
        self,
        mock_crawler_cls: MagicMock,
        mock_ensure: AsyncMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _pin_engine(monkeypatch, BrowserEngine.OBSCURA)

        def make_result(url: str) -> MagicMock:
            r = MagicMock()
            r.success = True
            r.markdown = f"content-{url}"
            r.error_message = ""
            return r

        crawler_inst = AsyncMock()
        crawler_inst.__aenter__ = AsyncMock(return_value=crawler_inst)
        crawler_inst.__aexit__ = AsyncMock(return_value=False)
        crawler_inst.arun = AsyncMock(side_effect=lambda url, config: make_result(url))
        mock_crawler_cls.return_value = crawler_inst

        from app.utils.crawl4ai_utils import CrawlBatchParams, batch_fetch_with_crawl4ai

        urls = ["https://a.example", "https://b.example", "https://c.example"]
        contents, errors = await batch_fetch_with_crawl4ai(
            urls,
            CrawlBatchParams(
                page_timeout_ms=20_000,
                total_timeout_seconds=30.0,
                semaphore_count=3,
                context_name="test",
            ),
        )

        assert errors == {}
        assert contents == {u: f"content-{u}" for u in urls}
        # Obscura engine resolved (per-URL fanout), and arun_many was never used.
        mock_ensure.assert_awaited()
        crawler_inst.arun_many.assert_not_called()

    @patch(
        "app.utils.crawl4ai_utils.ensure_crawl_obscura",
        new_callable=AsyncMock,
        return_value="http://127.0.0.1:9223",
    )
    @patch("app.utils.crawl4ai_utils.AsyncWebCrawler")
    async def test_obscura_one_url_failure_does_not_sink_the_batch(
        self,
        mock_crawler_cls: MagicMock,
        mock_ensure: AsyncMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _pin_engine(monkeypatch, BrowserEngine.OBSCURA)

        async def arun(url: str, config: object) -> MagicMock:
            r = MagicMock()
            if url == "https://bad.example":
                r.success = False
                r.markdown = ""
                r.error_message = "blocked"
            else:
                r.success = True
                r.markdown = "ok"
                r.error_message = ""
            return r

        crawler_inst = AsyncMock()
        crawler_inst.__aenter__ = AsyncMock(return_value=crawler_inst)
        crawler_inst.__aexit__ = AsyncMock(return_value=False)
        crawler_inst.arun = AsyncMock(side_effect=arun)
        mock_crawler_cls.return_value = crawler_inst

        from app.utils.crawl4ai_utils import CrawlBatchParams, batch_fetch_with_crawl4ai

        contents, errors = await batch_fetch_with_crawl4ai(
            ["https://good.example", "https://bad.example"],
            CrawlBatchParams(
                page_timeout_ms=20_000,
                total_timeout_seconds=30.0,
                semaphore_count=3,
                context_name="test",
            ),
        )

        assert contents["https://good.example"] == "ok"
        assert errors["https://bad.example"] == "blocked"
        assert "https://good.example" not in errors


class TestBuildBrowserConfig:
    """The engine decides the whole browser config, field by field."""

    @patch(
        "app.utils.crawl4ai_utils.ensure_crawl_obscura",
        new_callable=AsyncMock,
        return_value="http://127.0.0.1:9223",
    )
    async def test_obscura_connects_over_cdp_without_closing_the_shared_engine(
        self, mock_ensure: AsyncMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _pin_engine(monkeypatch, BrowserEngine.OBSCURA)
        from app.utils.crawl4ai_utils import _build_browser_config

        config = await _build_browser_config()

        assert config.browser_mode == "cdp"
        assert config.cdp_url == "http://127.0.0.1:9223"
        assert config.headless is True
        assert config.verbose is False
        # A crawler's teardown must never close the shared crawl engine out
        # from under a concurrent crawl.
        assert config.cdp_cleanup_on_close is False

    async def test_chromium_launches_its_own_dedicated_browser(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _pin_engine(monkeypatch, BrowserEngine.CHROMIUM)
        from app.utils.crawl4ai_utils import _build_browser_config

        config = await _build_browser_config()

        assert config.browser_mode == "dedicated"
        assert config.headless is True
        assert config.verbose is False
        assert config.cdp_url is None


class TestBuildRunConfig:
    """A content query is what switches the markdown generator to BM25 ranking."""

    def test_content_query_is_threaded_into_the_bm25_filter(self) -> None:
        from app.utils.crawl4ai_utils import CrawlBatchParams, _build_run_config

        config = _build_run_config(
            CrawlBatchParams(
                page_timeout_ms=30_000,
                total_timeout_seconds=60.0,
                semaphore_count=3,
                content_query="quantum error correction",
            )
        )

        assert config.markdown_generator.content_filter.user_query == "quantum error correction"

    def test_no_content_query_keeps_the_full_raw_markdown(self) -> None:
        from app.utils.crawl4ai_utils import CrawlBatchParams, _build_run_config

        config = _build_run_config(
            CrawlBatchParams(page_timeout_ms=30_000, total_timeout_seconds=60.0, semaphore_count=3)
        )

        assert config.markdown_generator.content_filter is None


class TestManagedCrawler:
    """The caller's config wins; without one the engine's default is built."""

    @patch("app.utils.crawl4ai_utils.AsyncWebCrawler")
    async def test_explicit_config_is_the_one_the_crawler_runs_on(
        self, mock_crawler_cls: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _pin_engine(monkeypatch, BrowserEngine.CHROMIUM)
        _stub_crawler(mock_crawler_cls)
        from app.utils.crawl4ai_utils import managed_crawler

        explicit = BrowserConfig(headless=False, browser_mode="dedicated", verbose=True)
        async with managed_crawler(explicit, context_name="test"):
            pass

        assert mock_crawler_cls.call_args.kwargs["config"] is explicit

    @patch("app.utils.crawl4ai_utils.AsyncWebCrawler")
    async def test_no_config_falls_back_to_the_engine_default(
        self, mock_crawler_cls: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _pin_engine(monkeypatch, BrowserEngine.CHROMIUM)
        _stub_crawler(mock_crawler_cls)
        from app.utils.crawl4ai_utils import managed_crawler

        async with managed_crawler(context_name="test"):
            pass

        config = mock_crawler_cls.call_args.kwargs["config"]
        assert isinstance(config, BrowserConfig)
        assert config.browser_mode == "dedicated"


class TestRecoveryAfterBatchTimeout:
    """The per-URL recovery pass: its own deadline, its own single-URL config."""

    @staticmethod
    def _timed_out_batch(mock_crawler_cls: MagicMock) -> AsyncMock:
        crawler_inst = _stub_crawler(mock_crawler_cls)
        # Batch times out, then every recovery crawl comes back empty-handed.
        crawler_inst.arun_many = AsyncMock(side_effect=[TimeoutError(), []])
        return crawler_inst

    @pytest.mark.parametrize(
        ("page_timeout_ms", "total_timeout_seconds", "expected_recovery_timeout"),
        [
            # Floor: a total budget under 10s still gives each recovery crawl 10s.
            (1_000, 5.0, 10.0),
            # Page-derived: page timeout + the processing margin, under the total.
            (600_000, 1_000.0, 645.0),
        ],
    )
    @patch("app.utils.crawl4ai_utils.AsyncWebCrawler")
    async def test_recovery_crawls_get_a_page_derived_deadline(
        self,
        mock_crawler_cls: MagicMock,
        page_timeout_ms: int,
        total_timeout_seconds: float,
        expected_recovery_timeout: float,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _pin_engine(monkeypatch, BrowserEngine.CHROMIUM)
        self._timed_out_batch(mock_crawler_cls)
        recorded = _record_wait_for_timeouts(monkeypatch)
        from app.utils.crawl4ai_utils import CrawlBatchParams, batch_fetch_with_crawl4ai

        await batch_fetch_with_crawl4ai(
            ["https://good.example"],
            CrawlBatchParams(
                page_timeout_ms=page_timeout_ms,
                total_timeout_seconds=total_timeout_seconds,
                semaphore_count=5,
                context_name="test",
            ),
        )

        assert expected_recovery_timeout in recorded

    @patch("app.utils.crawl4ai_utils.AsyncWebCrawler")
    async def test_recovery_errors_name_the_calling_context(
        self, mock_crawler_cls: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _pin_engine(monkeypatch, BrowserEngine.CHROMIUM)
        self._timed_out_batch(mock_crawler_cls)
        from app.utils.crawl4ai_utils import CrawlBatchParams, batch_fetch_with_crawl4ai

        contents, errors = await batch_fetch_with_crawl4ai(
            ["https://good.example"],
            CrawlBatchParams(
                page_timeout_ms=30_000,
                total_timeout_seconds=60.0,
                semaphore_count=5,
                context_name="deep_research",
            ),
        )

        assert contents == {}
        assert errors == {"https://good.example": "deep_research returned no result"}

    @patch("app.utils.crawl4ai_utils.AsyncWebCrawler")
    async def test_recovery_crawls_one_url_at_a_time(
        self, mock_crawler_cls: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _pin_engine(monkeypatch, BrowserEngine.CHROMIUM)
        crawler_inst = self._timed_out_batch(mock_crawler_cls)
        from app.utils.crawl4ai_utils import CrawlBatchParams, batch_fetch_with_crawl4ai

        await batch_fetch_with_crawl4ai(
            ["https://good.example"],
            CrawlBatchParams(
                page_timeout_ms=30_000,
                total_timeout_seconds=60.0,
                semaphore_count=5,
                context_name="test",
            ),
        )

        recovery_call = crawler_inst.arun_many.await_args_list[-1]
        assert recovery_call.kwargs["urls"] == ["https://good.example"]
        assert recovery_call.kwargs["config"].semaphore_count == 1


class TestPerUrlTimeout:
    """The Obscura path's per-URL deadline, as reported to the caller."""

    @pytest.mark.parametrize(
        ("page_timeout_ms", "total_timeout_seconds", "expected_message"),
        [
            # Floor: a total budget under 10s still gives each URL 10s.
            (1_000, 5.0, "test timed out after 10s"),
            # Page-derived: page timeout + the processing margin, under the total.
            (600_000, 1_000.0, "test timed out after 645s"),
            # Capped by the total budget when the page timeout exceeds it.
            (600_000, 100.0, "test timed out after 100s"),
        ],
    )
    @patch(
        "app.utils.crawl4ai_utils.ensure_crawl_obscura",
        new_callable=AsyncMock,
        return_value="http://127.0.0.1:9223",
    )
    @patch("app.utils.crawl4ai_utils.AsyncWebCrawler")
    async def test_per_url_timeout_is_reported_in_the_error(
        self,
        mock_crawler_cls: MagicMock,
        mock_ensure: AsyncMock,
        page_timeout_ms: int,
        total_timeout_seconds: float,
        expected_message: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _pin_engine(monkeypatch, BrowserEngine.OBSCURA)
        crawler_inst = _stub_crawler(mock_crawler_cls)
        crawler_inst.arun = AsyncMock(side_effect=TimeoutError())
        from app.utils.crawl4ai_utils import CrawlBatchParams, batch_fetch_with_crawl4ai

        contents, errors = await batch_fetch_with_crawl4ai(
            ["https://slow.example"],
            CrawlBatchParams(
                page_timeout_ms=page_timeout_ms,
                total_timeout_seconds=total_timeout_seconds,
                semaphore_count=3,
                context_name="test",
            ),
        )

        assert contents == {}
        assert errors == {"https://slow.example": expected_message}
