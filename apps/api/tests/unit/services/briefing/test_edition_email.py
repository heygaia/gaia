"""Unit tests for the edition-as-image briefing email.

The rasterizer and the CDN upload are faked at the boundary this module imports
them from; the edition renderer is faked so the assertions pin *this* module's
contract (options, public id, link resolution, escaping, action strip) rather
than the edition template's markup.
"""

from types import SimpleNamespace
from typing import Any

import pytest

from app.constants.notifications import (
    NOTIFICATION_KIND_BRIEFING_DAILY,
    NOTIFICATION_KIND_BRIEFING_WEEKLY,
)
from app.services.briefing import edition_email
from app.services.briefing.edition_email import is_edition_kind, render_edition_email

USER_ID = "user-abc"
IMAGE_URL = "https://cdn.example.com/edition.png"
UNSUBSCRIBE_URL = "https://heygaia.io/unsubscribe?t=abc"
FRONTEND_URL = "https://app.example.com"


def make_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "date": "2026-01-10",
        "headline": "Your Friday",
        "lede": "Three things need you.",
        "sections": [],
    }
    payload.update(overrides)
    return payload


def make_item(kind: str, text: str = "Send the invoice", link: str | None = None) -> dict[str, Any]:
    return {"kind": kind, "text": text, "link": link}


class Harness:
    def __init__(self) -> None:
        self.image = b"edition-png-bytes"
        self.image_url = IMAGE_URL
        self.render_calls: list[dict[str, Any]] = []
        self.image_calls: list[dict[str, Any]] = []
        self.upload_calls: list[dict[str, Any]] = []
        self.family_renderer: Any = None
        self.render_error: Exception | None = None
        self.upload_error: Exception | None = None


@pytest.fixture
def harness(monkeypatch: pytest.MonkeyPatch) -> Harness:
    h = Harness()

    def fake_render_edition(payload: dict[str, Any], **kwargs: Any) -> str:
        h.render_calls.append({"renderer": "classic", "payload": payload, **kwargs})
        return "<edition>classic</edition>"

    def fake_renderer_for(family: str | None) -> Any:
        return h.family_renderer

    async def fake_render_html_to_image(html: str, options: Any) -> bytes:
        h.image_calls.append({"html": html, "options": options})
        if h.render_error is not None:
            raise h.render_error
        return h.image

    def fake_upload(public_id: str, file_data: bytes | None = None, **kwargs: Any) -> str:
        h.upload_calls.append({"public_id": public_id, "file_data": file_data})
        if h.upload_error is not None:
            raise h.upload_error
        return h.image_url

    monkeypatch.setattr(edition_email, "render_edition", fake_render_edition)
    monkeypatch.setattr(edition_email, "renderer_for", fake_renderer_for)
    monkeypatch.setattr(edition_email, "render_html_to_image", fake_render_html_to_image)
    monkeypatch.setattr(edition_email, "upload_file_to_cloudinary", fake_upload)
    monkeypatch.setattr(edition_email, "settings", SimpleNamespace(FRONTEND_URL=FRONTEND_URL))
    return h


async def render(payload: dict[str, Any], **overrides: Any) -> str:
    kwargs: dict[str, Any] = {
        "kind": NOTIFICATION_KIND_BRIEFING_DAILY,
        "user_id": USER_ID,
        "generated_local": "8:00 AM",
        "tz_label": "IST",
        "unsubscribe_url": UNSUBSCRIBE_URL,
    }
    kwargs.update(overrides)
    return await render_edition_email(payload, **kwargs)


@pytest.mark.unit
class TestEditionRendering:
    async def test_classic_renderer_receives_the_edition_number_and_locale_labels(
        self, harness: Harness
    ) -> None:
        await render(make_payload(date="2026-01-10"))

        assert harness.render_calls == [
            {
                "renderer": "classic",
                "payload": make_payload(date="2026-01-10"),
                "edition_no": 10,
                "generated_local": "8:00 AM",
                "tz_label": "IST",
            }
        ]

    async def test_family_renderer_is_used_when_the_rotation_assigns_one(
        self, harness: Harness
    ) -> None:
        seen: list[dict[str, Any]] = []

        def family(payload: dict[str, Any], **kwargs: Any) -> str:
            seen.append({"payload": payload, **kwargs})
            return "<edition>family</edition>"

        harness.family_renderer = family

        await render(make_payload(template_family="dispatch"))

        assert harness.render_calls == []
        assert len(seen) == 1
        assert seen[0]["edition_no"] == 10
        assert harness.image_calls[0]["html"] == "<edition>family</edition>"

    async def test_edition_epoch_makes_the_first_of_january_2026_edition_one(
        self, harness: Harness
    ) -> None:
        await render(make_payload(date="2026-01-01"))

        assert harness.render_calls[0]["edition_no"] == 1

    async def test_unparseable_date_falls_back_to_edition_one(self, harness: Harness) -> None:
        await render(make_payload(date="not-a-date"))

        assert harness.render_calls[0]["edition_no"] == 1

    async def test_missing_date_falls_back_to_edition_one(self, harness: Harness) -> None:
        payload = make_payload()
        del payload["date"]

        await render(payload)

        assert harness.render_calls[0]["edition_no"] == 1


@pytest.mark.unit
class TestImageAndUpload:
    async def test_image_is_rasterized_at_full_edition_width_and_retina_scale(
        self, harness: Harness
    ) -> None:
        await render(make_payload())

        options = harness.image_calls[0]["options"]
        assert options.width == 1180
        assert options.device_scale_factor == 2
        assert options.image_format == "png"

    async def test_upload_public_id_namespaces_the_user_kind_and_date(
        self, harness: Harness
    ) -> None:
        await render(make_payload(date="2026-02-03"), kind=NOTIFICATION_KIND_BRIEFING_WEEKLY)

        assert harness.upload_calls == [
            {
                "public_id": f"briefing/editions/{USER_ID}/briefing_weekly_2026-02-03",
                "file_data": b"edition-png-bytes",
            }
        ]

    async def test_upload_public_id_uses_latest_when_the_payload_has_no_date(
        self, harness: Harness
    ) -> None:
        payload = make_payload()
        del payload["date"]

        await render(payload)

        assert harness.upload_calls[0]["public_id"] == (
            f"briefing/editions/{USER_ID}/briefing_daily_latest"
        )

    async def test_hosted_url_is_the_image_source(self, harness: Harness) -> None:
        html = await render(make_payload())

        assert f'src="{IMAGE_URL}"' in html

    async def test_image_url_is_html_escaped(self, harness: Harness) -> None:
        harness.image_url = "https://cdn.example.com/a.png?x=1&y=2"

        html = await render(make_payload())

        assert 'src="https://cdn.example.com/a.png?x=1&amp;y=2"' in html

    async def test_render_failure_propagates_so_the_caller_can_fall_back(
        self, harness: Harness
    ) -> None:
        harness.render_error = RuntimeError("chromium died")

        with pytest.raises(RuntimeError, match="chromium died"):
            await render(make_payload())

        assert harness.upload_calls == []

    async def test_upload_failure_propagates(self, harness: Harness) -> None:
        harness.upload_error = RuntimeError("cloudinary 500")

        with pytest.raises(RuntimeError, match="cloudinary 500"):
            await render(make_payload())


@pytest.mark.unit
class TestAltText:
    async def test_alt_joins_headline_and_lede(self, harness: Harness) -> None:
        html = await render(make_payload(headline="Big day", lede="Two calls."))

        assert 'alt="Big day — Two calls."' in html

    async def test_alt_drops_the_dangling_separator_when_there_is_no_lede(
        self, harness: Harness
    ) -> None:
        html = await render(make_payload(headline="Big day", lede=""))

        assert 'alt="Big day"' in html

    async def test_alt_falls_back_when_the_payload_has_no_headline(self, harness: Harness) -> None:
        payload = make_payload(lede="")
        del payload["headline"]

        html = await render(payload)

        assert 'alt="Your GAIA brief"' in html

    async def test_alt_is_escaped(self, harness: Harness) -> None:
        html = await render(make_payload(headline="R&D <b>", lede=""))

        assert 'alt="R&amp;D &lt;b&gt;"' in html


@pytest.mark.unit
class TestActionStrip:
    async def test_primary_cta_and_unsubscribe_are_always_present(self, harness: Harness) -> None:
        html = await render(make_payload())

        assert f'href="{FRONTEND_URL}"' in html
        assert "Open today&#39;s brief in GAIA" in html
        assert f'href="{UNSUBSCRIBE_URL}"' in html
        assert "Unsubscribe" in html

    async def test_no_action_items_means_no_waiting_block(self, harness: Harness) -> None:
        html = await render(make_payload(sections=[{"items": [make_item("update", "FYI only")]}]))

        assert "Waiting on your call" not in html
        assert "FYI only" not in html

    async def test_proposal_and_needs_you_items_get_review_links(self, harness: Harness) -> None:
        html = await render(
            make_payload(
                sections=[
                    {
                        "items": [
                            make_item("proposal", "Send the invoice", "todos/1"),
                            make_item("update", "Nothing to do"),
                            make_item("needs_you", "Answer Sam", "/todos/2"),
                        ]
                    }
                ]
            )
        )

        assert "Waiting on your call" in html
        assert "Send the invoice" in html
        assert "Answer Sam" in html
        assert "Nothing to do" not in html
        assert f'href="{FRONTEND_URL}/todos/1"' in html
        assert f'href="{FRONTEND_URL}/todos/2"' in html
        assert html.count("Review</a>") == 2

    async def test_items_are_collected_across_every_section(self, harness: Harness) -> None:
        html = await render(
            make_payload(
                sections=[
                    {"items": [make_item("proposal", "First", "a")]},
                    {"items": [make_item("proposal", "Second", "b")]},
                ]
            )
        )

        assert "First" in html
        assert "Second" in html
        assert html.count("Review</a>") == 2

    async def test_absolute_links_are_left_alone(self, harness: Harness) -> None:
        html = await render(
            make_payload(
                sections=[
                    {"items": [make_item("proposal", "Open Notion", "https://notion.so/page")]}
                ]
            )
        )

        assert 'href="https://notion.so/page"' in html

    async def test_item_without_a_link_falls_back_to_the_app_home(self, harness: Harness) -> None:
        html = await render(
            make_payload(sections=[{"items": [make_item("proposal", "Approve it", None)]}])
        )

        assert f'href="{FRONTEND_URL}" style="color:#00bbff' in html

    async def test_item_text_is_escaped_and_trimmed(self, harness: Harness) -> None:
        html = await render(
            make_payload(
                sections=[{"items": [make_item("proposal", "  Pay <Acme> & co  ", "todos/9")]}]
            )
        )

        assert "Pay &lt;Acme&gt; &amp; co &nbsp;" in html

    async def test_item_without_text_renders_an_empty_label(self, harness: Harness) -> None:
        html = await render(
            make_payload(sections=[{"items": [{"kind": "proposal", "link": "todos/9"}]}])
        )

        assert "Waiting on your call" in html
        assert html.count("Review</a>") == 1

    async def test_sections_without_items_are_tolerated(self, harness: Harness) -> None:
        html = await render(make_payload(sections=[{"title": "Empty"}]))

        assert "Waiting on your call" not in html

    async def test_unsubscribe_url_is_escaped(self, harness: Harness) -> None:
        html = await render(make_payload(), unsubscribe_url="https://heygaia.io/u?t=a&s=b")

        assert 'href="https://heygaia.io/u?t=a&amp;s=b"' in html


@pytest.mark.unit
class TestPublicAppUrl:
    @pytest.mark.parametrize("frontend_url", ["http://localhost:3000", "http://127.0.0.1:3000", ""])
    async def test_dev_origins_fall_back_to_the_public_app(
        self, harness: Harness, monkeypatch: pytest.MonkeyPatch, frontend_url: str
    ) -> None:
        monkeypatch.setattr(edition_email, "settings", SimpleNamespace(FRONTEND_URL=frontend_url))

        html = await render(
            make_payload(sections=[{"items": [make_item("proposal", "Do it", "todos/1")]}])
        )

        assert 'href="https://heygaia.io"' in html
        assert 'href="https://heygaia.io/todos/1"' in html

    async def test_unset_frontend_url_falls_back_to_the_public_app(
        self, harness: Harness, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(edition_email, "settings", SimpleNamespace(FRONTEND_URL=None))

        html = await render(make_payload())

        assert 'href="https://heygaia.io"' in html

    async def test_trailing_slash_is_stripped_so_links_never_double_up(
        self, harness: Harness, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            edition_email, "settings", SimpleNamespace(FRONTEND_URL="https://app.example.com/")
        )

        html = await render(
            make_payload(sections=[{"items": [make_item("proposal", "Do it", "/todos/1")]}])
        )

        assert 'href="https://app.example.com/todos/1"' in html
        assert "app.example.com//todos" not in html


@pytest.mark.unit
class TestIsEditionKind:
    @pytest.mark.parametrize(
        "kind", [NOTIFICATION_KIND_BRIEFING_DAILY, NOTIFICATION_KIND_BRIEFING_WEEKLY]
    )
    def test_briefing_kinds_render_as_editions(self, kind: str) -> None:
        assert is_edition_kind(kind) is True

    @pytest.mark.parametrize("kind", [None, "", "reminder", "briefing", "briefing_monthly"])
    def test_everything_else_does_not(self, kind: str | None) -> None:
        assert is_edition_kind(kind) is False
