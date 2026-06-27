from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from typing import Union
import structlog

logger = structlog.get_logger()


class AdminFilter(BaseFilter):
    async def __call__(self, event: Union[Message, CallbackQuery]) -> bool:
        if isinstance(event, Message):
            message = event
        elif isinstance(event, CallbackQuery):
            message = event.message
        else:
            return False

        if not message or not message.chat:
            return False

        if message.chat.type == "private":
            return True

        try:
            user_id = event.from_user.id if event.from_user else None
            if not user_id:
                return False
            member = await message.chat.get_member(user_id)
            return member.status in ("administrator", "creator")
        except Exception as e:
            logger.warning("Admin check failed", error=str(e))
            return False


class OwnerFilter(BaseFilter):
    def __init__(self, owner_id: int):
        self.owner_id = owner_id

    async def __call__(self, event: Union[Message, CallbackQuery]) -> bool:
        user = event.from_user
        return user is not None and user.id == self.owner_id


class GroupFilter(BaseFilter):
    async def __call__(self, event: Union[Message, CallbackQuery]) -> bool:
        if isinstance(event, Message):
            return event.chat.type in ("group", "supergroup")
        elif isinstance(event, CallbackQuery) and event.message:
            return event.message.chat.type in ("group", "supergroup")
        return False
