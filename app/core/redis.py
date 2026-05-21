# app/core/redis.py

import redis.asyncio as aioredis
from typing import Optional
from app.core.settings import settings
from app.core.log_config import get_logger

logger = get_logger(__name__)


class RedisManager:

    def __init__(self) -> None:
        self._pool: Optional[aioredis.ConnectionPool] = None
        self._client: Optional[aioredis.Redis] = None


    async def connect(self) -> None:
        self._pool = aioredis.ConnectionPool(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            decode_responses=True,
        )
        self._client = aioredis.Redis(connection_pool=self._pool)
        await self._client.ping()
        logger.info(
            "redis.connected",
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
        )


    async def disconnect(self) -> None:
        if self._client:
            await self._client.aclose()
        if self._pool:
            await self._pool.aclose()
        logger.info("redis.disconnected")


    @property
    def client(self) -> aioredis.Redis:
        if not self._client:
            raise RuntimeError("Redis not connected. Call connect() on startup.")
        return self._client


    '''
    #  Pub/Sub 
    async def publish(self, channel: str, message: str) -> None:
        await self.client.publish(channel, message)

    async def subscribe(self, *channels: str) -> aioredis.client.PubSub:
        pubsub = self.client.pubsub()
        await pubsub.subscribe(*channels)
        return pubsub
    '''
 
    async def set_cache(self, key: str, value: str, ttl: int = None) -> None:
        ttl = ttl or settings.REDIS_CACHE_TTL
        await self.client.setex(key, ttl, value)


    async def get_cache(self, key: str) -> Optional[str]:
        return await self.client.get(key)


    async def xread(
        self,
        stream_key: str,
        last_id: str,
        block_ms: int,
        count: int,
    ) -> list:

        results = await self.client.xread(
            streams={stream_key: last_id},
            block=block_ms,
            count=count,
        )
        return results or []


redis_manager = RedisManager()