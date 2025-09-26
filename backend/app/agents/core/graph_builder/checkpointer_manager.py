"""LangGraph checkpointing backed by Postgres, lazily provided.

Flow
- Requires `POSTGRES_URL` from `app.config.settings`.
- `@lazy_provider` registers two providers: full and shallow checkpointers.
- First `providers.aget(...)` creates an async pool and checkpointer, then reuses it.
- Use helpers `get_checkpointer_manager()` / `get_shallow_checkpointer_manager()`.

Add/change config
- Set `POSTGRES_URL` in settings; in dev it can be Optional.
- To alter pool size/shallow mode, adjust `CheckpointerManager` init params.
"""

from app.config.settings import settings
from app.core.lazy_loader import MissingKeyStrategy, lazy_provider, providers
from langgraph.checkpoint.postgres.aio import (
    AsyncPostgresSaver,
    AsyncShallowPostgresSaver,
)
from psycopg_pool import AsyncConnectionPool


class CheckpointerManager:
    """
    A manager class to handle checkpointer initialization and lifecycle.
    """

    def __init__(self, conninfo: str, max_pool_size: int = 20, shallow: bool = False):
        self.conninfo = conninfo
        self.max_pool_size = max_pool_size
        self.pool = None
        self.checkpointer = None
        self.shallow = shallow

    async def setup(self):
        """
        Initialize the connection pool and checkpointer.
        """
        self.pool = AsyncConnectionPool(
            conninfo=self.conninfo, max_size=self.max_pool_size, open=False, timeout=5
        )
        await self.pool.open(wait=True, timeout=5)

        if self.shallow:
            self.checkpointer = AsyncShallowPostgresSaver(conn=self.pool)  # type: ignore
        else:
            self.checkpointer = AsyncPostgresSaver(conn=self.pool)  # type: ignore

        try:
            await self.checkpointer.setup()
        except Exception as e:
            print(f"Error setting up checkpointer: {e}")
            await self.close()
            raise e
        return self

    async def close(self):
        """
        Close the connection pool and cleanup resources.
        """
        if self.pool:
            await self.pool.close()

    def get_checkpointer(self):
        """
        Get the initialized checkpointer.
        """
        if not self.checkpointer:
            raise RuntimeError(
                "Checkpointer has not been initialized. Call setup() first."
            )
        return self.checkpointer


@lazy_provider(
    name="checkpointer_manager",
    required_keys=[settings.POSTGRES_URL],
    strategy=MissingKeyStrategy.WARN,
    auto_initialize=False,
    warning_message="PostgreSQL URL not configured. Langraph checkpointing features will be disabled. Langraph graph persistence will not work.",
)
async def init_checkpointer_manager() -> CheckpointerManager:
    """
    Initialize the main checkpointer manager.

    Returns:
        CheckpointerManager: The main checkpointer manager
    """
    conninfo: str = settings.POSTGRES_URL  # type: ignore
    manager = CheckpointerManager(conninfo=conninfo, shallow=False)
    await manager.setup()
    return manager


@lazy_provider(
    name="shallow_checkpointer_manager",
    required_keys=[settings.POSTGRES_URL],
    strategy=MissingKeyStrategy.WARN,
    auto_initialize=False,
    warning_message="PostgreSQL URL not configured. Langraph checkpointing features will be disabled. Langraph graph persistence will not work.",
)
async def init_shallow_checkpointer_manager() -> CheckpointerManager:
    """
    Initialize the shallow checkpointer manager.

    Returns:
        CheckpointerManager: The shallow checkpointer manager
    """
    conninfo: str = settings.POSTGRES_URL  # type: ignore
    manager = CheckpointerManager(conninfo=conninfo, shallow=True)
    await manager.setup()
    return manager


async def get_checkpointer_manager() -> CheckpointerManager:
    """
    Get the main checkpointer manager instance.

    Returns:
        CheckpointerManager: The main checkpointer manager
    """
    manager = await providers.aget("checkpointer_manager")
    if not manager:
        raise RuntimeError("Checkpointer manager is not available")
    return manager


async def get_shallow_checkpointer_manager() -> CheckpointerManager:
    """
    Get the shallow checkpointer manager instance.

    Returns:
        CheckpointerManager: The shallow checkpointer manager
    """
    manager = await providers.aget("shallow_checkpointer_manager")
    if not manager:
        raise RuntimeError("Shallow checkpointer manager is not available")
    return manager


def init_checkpointer_managers():
    """
    Eagerly initialize both checkpointer managers.
    """
    init_checkpointer_manager()
    init_shallow_checkpointer_manager()
