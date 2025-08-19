from app.config.settings import settings
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


checkpointer_manager = CheckpointerManager(settings.POSTGRES_URL)
checkpointer_manager_shallow = CheckpointerManager(settings.POSTGRES_URL, shallow=True)
