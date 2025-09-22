# Auto-generated unit tests for utils.exceptions
# Testing framework: pytest

import pytest
from pathlib import Path
import importlib.util

def _import_exceptions():
    """
    Try multiple import strategies so tests work across various project layouts:
    1) Standard module paths (backend.utils.exceptions or utils.exceptions)
    2) Fallback: dynamically locate exceptions.py nearby and import via importlib
    """
    # 1) Direct imports
    try:
        from backend.utils.exceptions import FetchError, InfisicalConfigError, ConfigurationError  # type: ignore
        return FetchError, InfisicalConfigError, ConfigurationError
    except Exception:
        pass
    try:
        from utils.exceptions import FetchError, InfisicalConfigError, ConfigurationError  # type: ignore
        return FetchError, InfisicalConfigError, ConfigurationError
    except Exception:
        pass

    # 2) Dynamic discovery/import
    candidates = [
        "backend/utils/exceptions.py",
        "utils/exceptions.py",
        "src/utils/exceptions.py",
        "app/utils/exceptions.py",
        "backend/common/utils/exceptions.py",
    ]
    start = Path(__file__).resolve()
    for base in [start.parent] + list(start.parents):
        for rel in candidates:
            p = base / rel
            if p.exists():
                spec = importlib.util.spec_from_file_location("temp_exceptions", str(p))
                mod = importlib.util.module_from_spec(spec)
                assert spec and spec.loader
                spec.loader.exec_module(mod)  # type: ignore[attr-defined]
                return mod.FetchError, mod.InfisicalConfigError, mod.ConfigurationError
    raise ImportError("Could not locate exceptions module")

try:
    FetchError, InfisicalConfigError, ConfigurationError = _import_exceptions()
except Exception as e:
    pytest.skip(f"Skipping exceptions tests: {e\!r}", allow_module_level=True)


def test_fetch_error_message_only_str_and_args():
    e = FetchError("Network failure")
    assert isinstance(e, Exception)
    assert getattr(e, "message", None) == "Network failure"
    assert e.status_code is None
    assert e.url is None
    assert str(e) == "Network failure"
    assert e.args == ("Network failure",)


def test_fetch_error_with_status_code_and_url_str_format():
    e = FetchError("Timeout", status_code=504, url="https://api.example.com/endpoint")
    assert e.status_code == 504
    assert e.url == "https://api.example.com/endpoint"
    assert str(e) == "Timeout (Status code: 504) - URL: https://api.example.com/endpoint"


def test_fetch_error_with_status_code_only_str_format():
    e = FetchError("Bad Request", status_code=400)
    assert str(e) == "Bad Request (Status code: 400)"


def test_fetch_error_with_url_only_str_format():
    e = FetchError("Not Found", url="http://example.test/resource")
    assert str(e) == "Not Found - URL: http://example.test/resource"


def test_fetch_error_zero_status_and_empty_url_are_not_appended():
    # Edge case: falsy values should not be appended per current implementation
    e = FetchError("Weird", status_code=0, url="")
    assert str(e) == "Weird"


def test_fetch_error_raises_and_preserves_context():
    with pytest.raises(FetchError) as excinfo:
        raise FetchError("Boom", status_code=500, url="https://service.invalid/op")
    msg = str(excinfo.value)
    assert "Boom" in msg
    assert "(Status code: 500)" in msg
    assert "URL: https://service.invalid/op" in msg
    assert excinfo.value.status_code == 500
    assert excinfo.value.url == "https://service.invalid/op"


def test_infisical_config_error_basic():
    with pytest.raises(InfisicalConfigError) as excinfo:
        raise InfisicalConfigError("Missing INFISICAL token")
    e = excinfo.value
    assert isinstance(e, Exception)
    assert getattr(e, "message", None) == "Missing INFISICAL token"
    assert str(e) == "Missing INFISICAL token"
    assert e.args == ("Missing INFISICAL token",)


def test_configuration_error_basic():
    with pytest.raises(ConfigurationError) as excinfo:
        raise ConfigurationError("Missing API key")
    e = excinfo.value
    assert isinstance(e, Exception)
    assert getattr(e, "message", None) == "Missing API key"
    assert str(e) == "Missing API key"
    assert e.args == ("Missing API key",)