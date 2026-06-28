import asyncio
import os
import structlog
from aiohttp import web
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
from bot.admin_api import setup_admin_routes

logger = structlog.get_logger()


async def health_handler(request):
    return web.Response(text="OK", status=200)


async def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    app = web.Application()
    app.router.add_get("/health", health_handler)
    app.router.add_get("/", health_handler)
    setup_admin_routes(app)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port, reuse_port=True)
    await site.start()
    logger.info("Health check server started", port=port)
    return runner


async def setup_database_with_retry(retries=5, delay=3):
    for attempt in range(1, retries + 1):
        try:
            await create_tables()
            logger.info("Database tables created successfully")
            return True
        except Exception as e:
            logger.warning(f"DB setup attempt {attempt}/{retries} failed", error=str(e))
            if attempt < retries:
                await asyncio.sleep(delay)
    logger.error("All DB setup attempts failed — bot will run without DB")
    return False


async def on_startup(bot: Bot) -> None:
    logger.info("Bot starting up", environment=settings.ENVIRONMENT)

    try:
        load_translations()
        logger.info("Translations loaded")
    except Exception as e:
        logger.error("Failed to load translations", error=str(e))

    db_ok = await setup_database_with_retry()

    if db_ok:
        try:
            from bot.database.connection import async_session_maker
            async with async_session_maker() as session:
                await seed_achievements(session)
            logger.info("Achievements seeded")
        except Exception as e:
            logger.warning("Could not seed achievements", error=str(e))

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Polling mode — webhook cleared")
    except Exception as e:
        logger.error("Failed to clear webhook", error=str(e))

    logger.info("Bot startup complete", db_ready=db_ok)


async def on_shutdown(bot: Bot, runner) -> None:
    logger.info("Bot shutting down")
    try:
        await close_db()
    except Exception:
        pass
    await runner.cleanup()
    logger.info("Shutdown complete")


async def main() -> None:
    setup_logging()

    if settings.SENTRY_DSN:
        import sentry_sdk
        sentry_sdk.init(dsn=settings.SENTRY_DSN, environment=settings.ENVIRONMENT)

    runner = await run_health_server()

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
    except Exception as e:
        logger.error("Polling crashed", error=str(e))

    await on_shutdown(bot, runner)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")
