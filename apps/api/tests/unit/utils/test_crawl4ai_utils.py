"""Unit tests for app.utils.crawl4ai_utils."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config.settings import settings
from app.constants.browser import BrowserEngine


def _pin_engine(monkeypatch: pytest.MonkeyPatch, engine: BrowserEngine) -> None:
    monkeypatch.setattr(settings, "BROWSER_ENGINE", engine)


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

        from app.utils.crawl4ai_utils import batch_fetch_with_crawl4ai

        urls = [
            "https://example.com",
            "https://httpbin.org/redirect-to?url=https://example.com/",
        ]
        contents, errors = await batch_fetch_with_crawl4ai(
            urls,
            page_timeout_ms=30_000,
            total_timeout_seconds=60.0,
            semaphore_count=3,
            context_name="test",
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

        from app.utils.crawl4ai_utils import batch_fetch_with_crawl4ai

        urls = ["https://good.example", "https://bad.example"]
        contents, errors = await batch_fetch_with_crawl4ai(
            urls,
            page_timeout_ms=30_000,
            total_timeout_seconds=20.0,
            semaphore_count=5,
            context_name="test",
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

        from app.utils.crawl4ai_utils import batch_fetch_with_crawl4ai

        urls = ["https://a.example", "https://b.example", "https://c.example"]
        contents, errors = await batch_fetch_with_crawl4ai(
            urls,
            page_timeout_ms=20_000,
            total_timeout_seconds=30.0,
            semaphore_count=3,
            context_name="test",
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

        from app.utils.crawl4ai_utils import batch_fetch_with_crawl4ai

        contents, errors = await batch_fetch_with_crawl4ai(
            ["https://good.example", "https://bad.example"],
            page_timeout_ms=20_000,
            total_timeout_seconds=30.0,
            semaphore_count=3,
            context_name="test",
        )

        assert contents["https://good.example"] == "ok"
        assert errors["https://bad.example"] == "blocked"
        assert "https://good.example" not in errors
