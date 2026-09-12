import os

from latitude_telemetry import Latitude
from openinference.instrumentation.langchain import LangChainInstrumentor

from app.config.settings import settings
from app.core.lazy_loader import MissingKeyStrategy, lazy_provider
from shared.py.wide_events import log

_client: Latitude | None = None


@lazy_provider(
    name="latitude",
    required_keys=[settings.LATITUDE_API_KEY],
    auto_initialize=True,
    is_global_context=True,
    strategy=MissingKeyStrategy.SILENT,
)
def init_latitude() -> bool:
    """Initialize Latitude telemetry once per process.

    Spans come from OpenInference's LangChain instrumentor (maintained against
    LangChain 1.x — the OTel-contrib one latitude-telemetry bundles no longer
    patches current internals, verified: zero LLM spans), registered against
    Latitude's own provider so spans ship to Latitude and nowhere else.
    No-op when LATITUDE_API_KEY is unset.
    """
    # The SDK reads this at import time; settings is the source of truth when
    # the process env does not already define it (e.g. local .env files).
    endpoint = os.environ.setdefault("LATITUDE_TELEMETRY_URL", settings.LATITUDE_TELEMETRY_URL)

    latitude = Latitude(
        api_key=settings.LATITUDE_API_KEY or "",
        project=settings.LATITUDE_PROJECT,
    )
    LangChainInstrumentor().instrument(tracer_provider=latitude.provider)
    global _client
    _client = latitude
    log.info(
        "latitude_ready",
        project=settings.LATITUDE_PROJECT,
        endpoint=endpoint,
    )
    return True


async def flush_latitude() -> None:
    """Flush queued Latitude spans on shutdown so a restart loses no traces."""
    if _client is None:
        return
    try:
        _client.flush()
    except Exception as exc:
        log.warning(
            "latitude_flush_failed",
            error=str(exc),
            error_type=type(exc).__name__,
        )
