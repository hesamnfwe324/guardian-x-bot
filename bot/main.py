import asyncio
import structlog
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import settings
from bot.utils.logger import setup_logging
from bot.middlewares import I18nMiddleware, DatabaseMiddleware, load_translations
from bot.database.connection import create_tables, close_db
from bot.handlers import get_main_router
from bot.services.achievement_service import seed_achievements

logger = structlog.get_logger()


async def on_startup(bot: Bot) -> None:
    logger.info("Bot starting up", environment=settings.ENVIRONMENT)
    load_translations()
    await create_tables()

    from bot.database.connection import async_session_maker
    async with async_session_maker() as session:
        await seed_achievements(session)

    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Polling mode — webhook cleared")


async def on_shutdown(bot: Bot) -> None:
    logger.info("Bot shutting down")
    await close_db()
    logger.info("Shutdown complete")


async def main() -> None:
    setup_logging()

    if settings.SENTRY_DSN:
        import sentry_sdk
        sentry_sdk.init(dsn=settings.SENTRY_DSN, environment=settings.ENVIRONMENT)
        logger.info("Sentry initialized")

    storage = MemoryStorage()
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=storage)

    dp.include_router(get_main_router())
    dp.update.outer_middleware(DatabaseMiddleware())
    dp.update.outer_middleware(I18nMiddleware())

    await on_startup(bot)

    logger.info("Starting polling")
    try:
        await dp.start_polling(
            bot,
            allowed_updates=["message", "callback_query", "chat_member", "my_chat_member"],
        )
    except asyncio.CancelledError:
        pass

    await on_shutdown(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")
