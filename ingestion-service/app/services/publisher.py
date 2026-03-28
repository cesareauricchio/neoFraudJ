from __future__ import annotations

import json

import redis.asyncio as aioredis

from app.config import get_settings


class RedisPublisher:
    """Lifecycle-managed Redis Streams publisher."""

    def __init__(self) -> None:
        self._client: aioredis.Redis | None = None

    async def connect(self, url: str) -> None:
        self._client = await aioredis.from_url(url, decode_responses=True)

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()

    async def publish_transaction(self, payload_dict: dict) -> str:
        """
        XADD neofraudj:transactions MAXLEN ~ <maxlen> * data <json>
        Returns the Redis stream entry ID.
        """
        settings = get_settings()
        entry_id: str = await self._client.xadd(
            name=settings.redis_stream_name,
            fields={"data": json.dumps(payload_dict, default=str)},
            maxlen=settings.redis_stream_maxlen,
            approximate=True,  # '~' prefix — trim lazily for performance
        )
        return entry_id
