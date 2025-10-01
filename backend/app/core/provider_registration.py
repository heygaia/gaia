"""
Common provider registration logic shared between main app lifespan and ARQ worker startup.
"""

import warnings

from app.config.loggers import app_logger as logger
from app.core.lazy_loader import providers
from pydantic import PydanticDeprecatedSince20

# Ignore specific deprecation warnings from pydantic in langchain_core
warnings.filterwarnings(
    "ignore", category=PydanticDeprecatedSince20, module="langchain_core.tools.base"
)


def register_all_providers(context: str = "main_app") -> None:
    """
    Register all lazy providers required by both main app and ARQ worker.

    Args:
        context: Either "main_app" or "arq_worker" for logging purposes
    """
    from app.agents.core.graph_builder.build_graph import build_default_graph
    from app.agents.core.graph_builder.checkpointer_manager import (
        init_checkpointer_manager,
    )
    from app.agents.llm.client import register_llm_providers
    from app.agents.tools.core.registry import init_tool_registry
    from app.agents.tools.core.store import init_embeddings, initialize_tools_store
    from app.config.cloudinary import init_cloudinary
    from app.db.chromadb import init_chroma
    from app.db.postgresql import init_postgresql_engine
    from app.db.rabbitmq import init_rabbitmq_publisher
    from app.helpers.lifespan_helpers import setup_event_loop_policy
    from app.services.composio.composio_service import init_composio_service
    from app.services.startup_validation import validate_startup_requirements

    logger.info(f"Registering lazy providers for {context}...")

    # Core infrastructure providers
    init_postgresql_engine()
    init_rabbitmq_publisher()

    # AI/ML providers
    register_llm_providers()
    build_default_graph()
    init_chroma()
    init_checkpointer_manager()

    # Tool and agent providers
    init_tool_registry()
    init_composio_service()
    init_embeddings()
    initialize_tools_store()

    # Utility providers
    init_cloudinary()
    validate_startup_requirements()
    setup_event_loop_policy()

    logger.info(f"All lazy providers registered successfully for {context}")


async def initialize_auto_providers(context: str = "main_app") -> None:
    """
    Initialize all auto providers.

    Args:
        context: Either "main_app" or "arq_worker" for logging purposes
    """
    logger.info(f"Initializing auto providers for {context}...")
    await providers.initialize_auto_providers()
    logger.info(f"Auto providers initialized successfully for {context}")


def setup_warnings() -> None:
    """Set up common warning filters."""
    warnings.filterwarnings(
        "ignore", category=PydanticDeprecatedSince20, module="langchain_core.tools.base"
    )
