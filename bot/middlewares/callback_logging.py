from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update
import structlog

logger = structlog.get_logger()


class CallbackLoggingMiddleware(BaseMiddleware):
    """Logs every button press (callback query) and command message with full detail.
    
    This middleware logs:
    - callback_data: the exact data string of the pressed button
    - user_id, username, first_name: who pressed it
    - chat_id, chat_type: where it happened
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Update):
            if event.callback_query:
                cb = event.callback_query
                user = cb.from_user
                logger.info(
                    "BUTTON_PRESSED",
                    callback_data=cb.data,
                    user_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    lang=getattr(data.get("db_user"), "language", None),
                    chat_id=cb.message.chat.id if cb.message else None,
                    chat_type=cb.message.chat.type if cb.message else "private",
                )
            elif event.message:
                msg = event.message
                user = msg.from_user
                if user and not user.is_bot and msg.text:
                    logger.info(
                        "MESSAGE_RECEIVED",
                        text=msg.text[:120],
                        user_id=user.id,
                        username=user.username,
                        first_name=user.first_name,
                        chat_id=msg.chat.id,
                        chat_type=msg.chat.type,
                    )

        result = await handler(event, data)

        # Log result of callback (after handler executed)
        if isinstance(event, Update) and event.callback_query:
            cb = event.callback_query
            logger.info(
                "CALLBACK_HANDLED",
                callback_data=cb.data,
                user_id=cb.from_user.id,
            )

        return result
