from dataclasses import dataclass

from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from ..infrastructure.config import Settings


@dataclass(slots=True)
class InfrastructureResources:
    database: AsyncEngine
    redis: Redis

    @classmethod
    def create(cls, settings: Settings) -> "InfrastructureResources":
        return cls(
            database=create_async_engine(settings.database_url, pool_pre_ping=True),
            redis=Redis.from_url(settings.redis_url, decode_responses=True),
        )

    async def database_is_ready(self) -> bool:
        try:
            async with self.database.connect() as connection:
                await connection.execute(text("SELECT 1"))
        except Exception:
            return False
        return True

    async def redis_is_ready(self) -> bool:
        try:
            return bool(await self.redis.ping())
        except Exception:
            return False

    async def close(self) -> None:
        await self.redis.aclose()
        await self.database.dispose()
