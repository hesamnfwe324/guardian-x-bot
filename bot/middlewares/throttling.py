import time
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
import redis.asyncio as aioredis
import structlog

logger = structlog.get_logger()

THROTTLE_LIMIT = 0.5


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, redis_client: aioredis.Redis, limit: float = THROTTLE_LIMIT):
        self.redis = redis_client
        self.limit = limit

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        key = f"throttle:{user.id}"
        current = await self.redis.get(key)

        if current:
            return None

        ttl_ms = max(100, int(self.limit * 1000))
        await self.redis.psetex(key, ttl_ms, "1")
        return await handler(event, data)


class FloodControlMiddleware(BaseMiddleware):
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        user = data.get("event_from_user")
        chat = getattr(event, "chat", None)
        if not user or not chat or chat.type == "private":
            return await handler(event, data)

        db_session = data.get("db_session")
        group_security = data.get("group_security")

        if group_security and group_security.anti_flood:
            limit = group_security.flood_limit or 5
            window = group_security.flood_window or 10
            key = f"flood:{chat.id}:{user.id}"

            count = await self.redis.incr(key)
            if count == 1:
                await self.redis.expire(key, window)

            if count > limit:
                data["flood_detected"] = True
                data["flood_action"] = group_security.flood_action or "mute"

        return await handler(event, data)
