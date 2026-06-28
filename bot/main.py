import asyncio
  import os
  import structlog
  from aiohttp import web

  logger = structlog.get_logger()


  async def health_handler(request):
      return web.Response(text="OK", status=200)


  async def run_health_server():
      """Start the HTTP health/admin server FIRST — before any other imports.
      This ensures Render sees the port bound even if bot config is incomplete."""
      port = int(os.environ.get("PORT", 8080))
      app = web.Application()
      app.router.add_get("/health", health_handler)
      app.router.add_get("/", health_handler)

      # Lazy-import admin routes so config errors don't prevent port binding
      try:
          from bot.admin_api import setup_admin_routes
          setup_admin_routes(app)
      except Exception as e:
          logger.warning("Admin routes not loaded", error=str(e))

      runner = web.AppRunner(app)
      await runner.setup()
      site = web.TCPSite(runner, "0.0.0.0", port, reuse_port=True)
      await site.start()
      logger.info("Health check server started", port=port)
      return runner


  async def setup_database_with_retry(retries=5, delay=3):
      from bot.database.connection import create_tables
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


  async def on_startup(bot) -> None:
      from bot.config import settings
      from bot.middlewares import load_translations
      from bot.services.achievement_service import seed_achievements

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


  async def on_shutdown(bot, runner) -> None:
      logger.info("Bot shutting down")
      try:
          from bot.database.connection import close_db
          await close_db()
      except Exception:
          pass
      await runner.cleanup()
      logger.info("Shutdown complete")


  async def main() -> None:
      # Bind the port FIRST so Render health checks pass immediately
      runner = await run_health_server()

      # Now import the rest — any config/import error here won't block the port
      try:
          from bot.utils.logger import setup_logging
          setup_logging()
      except Exception as e:
          logger.warning("Could not set up structured logging", error=str(e))

      from bot.config import settings

      if not settings.is_configured:
          logger.error(
              "BOT_TOKEN or DATABASE_URL is not set. "
              "Please add these environment variables in your Render service dashboard. "
              "The health server is running but the bot is NOT active."
          )
          # Keep health server alive so Render marks the deploy as live
          try:
              await asyncio.Event().wait()
          except asyncio.CancelledError:
              pass
          await runner.cleanup()
          return

      if settings.SENTRY_DSN:
          import sentry_sdk
          sentry_sdk.init(dsn=settings.SENTRY_DSN, environment=settings.ENVIRONMENT)

      from aiogram import Bot, Dispatcher
      from aiogram.client.default import DefaultBotProperties
      from aiogram.enums import ParseMode
      from aiogram.fsm.storage.memory import MemoryStorage
      from bot.handlers import get_main_router
      from bot.middlewares import DatabaseMiddleware, I18nMiddleware, CallbackLoggingMiddleware

      storage = MemoryStorage()
      bot = Bot(
          token=settings.BOT_TOKEN,
          default=DefaultBotProperties(parse_mode=ParseMode.HTML),
      )
      dp = Dispatcher(storage=storage)

      dp.include_router(get_main_router())

      # IMPORTANT: Middleware registration order matters in aiogram 3.
      # outer_middleware uses a LIFO stack — last registered runs FIRST.
      # Desired execution order: CallbackLogging → Database → I18n → handler
      # So we register in reverse: I18n first, then Database, then CallbackLogging last.
      dp.update.outer_middleware(I18nMiddleware())        # registered 1st → runs LAST (closest to handler)
      dp.update.outer_middleware(DatabaseMiddleware())    # registered 2nd → runs SECOND (provides db_user to I18n)
      dp.update.outer_middleware(CallbackLoggingMiddleware())  # registered 3rd → runs FIRST (logs raw button press)

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
  