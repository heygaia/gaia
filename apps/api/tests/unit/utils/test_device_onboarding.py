"""The device-onboarding card utils: the streamed card payload and the
source-category-aware agent copy (URL-free on UI, inline on text-only)."""

from unittest.mock import patch

import pytest

from app.models.chat_models import SourceCategory
from app.utils import device_onboarding as mod

_UI = SourceCategory.UI.value


def _capture():
    captured: dict = {}
    return captured, lambda payload: captured.update(payload)


@pytest.mark.unit
def test_onboarding_streams_card_and_stays_url_free_on_ui():
    captured, writer = _capture()
    with (
        patch.object(mod, "_current_source_category", return_value=_UI),
        patch.object(mod, "get_stream_writer", return_value=writer),
    ):
        ret = mod.request_device_onboarding()

    card = captured["device_onboarding_required"]
    assert card["install_commands"]["npm"] == "npm install -g @heygaia/cli"
    assert card["pair_command"] == "gaia bridge login"
    assert card["up_command"] == "gaia bridge up"
    # UI card carries the steps, so the agent copy must not leak a URL/command.
    assert "http" not in ret and "npm install" not in ret


@pytest.mark.unit
def test_onboarding_text_copy_inlines_command_and_docs_off_ui():
    with patch.object(mod, "_current_source_category", return_value=None):
        ret = mod.request_device_onboarding()
    assert "npm install -g @heygaia/cli" in ret
    assert "gaia bridge login" in ret
    assert "docs.heygaia.io" in ret


@pytest.mark.unit
def test_approval_streams_link_and_normalizes_code_on_ui():
    captured, writer = _capture()
    with (
        patch.object(mod, "_current_source_category", return_value=_UI),
        patch.object(mod, "get_stream_writer", return_value=writer),
    ):
        ret = mod.request_device_approval("ns2v-yc5s")

    card = captured["device_approval_required"]
    assert card["code"] == "NS2V-YC5S"  # normalized upper
    assert card["approve_url"].endswith("/settings/devices/approve?code=NS2V-YC5S")
    # The link rides the card, not the agent's user-facing text.
    assert "http" not in ret
    assert "NS2V-YC5S" in ret


@pytest.mark.unit
def test_approval_text_copy_inlines_the_url_off_ui():
    with patch.object(mod, "_current_source_category", return_value=None):
        ret = mod.request_device_approval("ns2v-yc5s")
    assert "/settings/devices/approve?code=NS2V-YC5S" in ret


@pytest.mark.unit
def test_no_stream_when_outside_a_runnable_context():
    """Dev direct-invocation paths have no stream; the util must not try to write."""
    captured, writer = _capture()
    with (
        patch.object(mod, "_current_source_category", return_value=None),
        patch.object(mod, "get_stream_writer", return_value=writer) as gsw,
    ):
        mod.request_device_onboarding()
    assert captured == {}
    gsw.assert_not_called()
