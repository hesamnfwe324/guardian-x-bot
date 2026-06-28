import asyncio
  import os
  import traceback
  import structlog
  from aiohttp import web
  from pathlib import Path

  logger = structlog.get_logger()
  _last_error = None  # stores last crash reason, shown by /health

  PANEL_DIR = Path(__file__).resolve().parent.parent / "panel"


  async def health_handler(request):
      global _last_error
      if _last_error:
          return web.Response(
              text=f'DEGRADED: {_last_error}',
              status=200,  # still 200 so Render doesn't restart
              content_type='text/plain',
          )
      return web.Response(text='OK', status=200)


  async def panel_index_handler(request):
      """Serve the glassmorphism admin panel."""
      index_path = PANEL_DIR / "index.html"
      if not index_path.exists():
          return web.Response(text='Panel not found', status=404)
      return web.FileResponse(index_path)


  async def panel_static_handler(request):
      """Serve static files for the admin panel (CSS, JS, images)."""
      filename = request.match_info.get('filename', '')
      filepath = PANEL_DIR / filename
      if not filepath.exists():
          return web.Response(text='File not found', status=404)
      return web.FileResponse(filepath)


  async def run_health_server():
      port = int(os.environ.get('PORT', 8080))
      app = web.Application()
      app.router.add_get('/health', health_handler)
      app.router.add_get('/', health_handler)

      # Glassmorphism Admin Panel routes
      app.router.add_get('/panel', panel_index_handler)
      app.router.add_get('/panel/{filename}', panel_static_handler)

      try:
          from bot.admin_api import setup_admin_routes
          setup_admin_routes(app)
      except Exception as e:
          logger.warning('Admin routes not loaded', error=str(e))

      runner = web.AppRunner(app)
      await runner.setup()
      site = web.TCPSite(runner, '0.0.0.0', port, reuse_port=True)
      await site.start()
      logger.info('Health check server started', port=port)
      return runner


  async def setup_database_with_retry(retries=5, delay=3):
      for attempt in range(1, retries + 1):
          try:
              from bot.database.connection import create_tables
              await create_tables()
              logger.info('Database tables created successfully')
              return True
          except BaseException as e:
              logger.warning(f'DB setup attempt {attempt}/{retries} failed', error=str(e))
              if attempt < retries:
                  await asyncio.sleep(delay)
      logger.error('All DB setup attempts failed — bot will run without DB')
      return False


  async def on_startup(bot) -> None:
      from bot.config import settings
      logger.info('Bot starting up', environment=settings.ENVIRONMENT)

      try:
          from bot.middlewares import load_translations
          load_translations()
          logger.info('Translations loaded')
      except Exception as e:
          logger.error('Failed to load translations', error=str(e))

      db_ok = await setup_database_with_retry()

      if db_ok:
          try:
              from bot.database.connection import async_session_maker
              from bot.services.achievement_service import seed_achievements
              async with async_session_maker() as session:
                  await seed_achievements(session)
              logger.info('Achievements seeded')
          except Exception as e:
              logger.warning('Could not seed achievements', error=str(e))

      try:
          await bot.delete_webhook(drop_pending_updates=True)
          logger.info('Polling mode — webhook cleared')
      except Exception as e:
          logger.error('Failed to clear webhook', error=str(e))

      logger.info('Bot startup complete', db_ready=db_ok)


  async def on_shutdown(bot, runner) -> None:
      logger.info('Bot shutting down')
      try:
          from bot.database.connection import close_db
          await close_db()
      except Exception:
          pass
      try:
          await runner.cleanup()
      except Exception:
          pass
      logger.info('Shutdown complete')


  async def run_bot(bot, dp, runner):
      """Run the bot polling loop. Returns when polling ends."""
      global _last_error
      try:
          await on_startup(bot)
      except BaseException as e:
          tb = traceback.format_exc()
          _last_error = f'on_startup failed: {e}\n{tb}'
          logger.error('Bot startup failed', error=str(e), traceback=tb)
          return

      logger.info('Starting polling')
      try:
          await dp.start_polling(
              bot,
              allowed_updates=['message', 'callback_query', 'chat_member', 'my_chat_member'],
          )
      except asyncio.CancelledError:
          pass
      except BaseException as e:
          tb = traceback.format_exc()
          _last_error = f'Polling crashed: {e}\n{tb}'
          logger.error('Polling crashed', error=str(e), traceback=tb)

      await on_shutdown(bot, runner)


  async def main() -> None:
      global _last_error
      runner = await run_health_server()

      try:
          from bot.utils.logger import setup_logging
          setup_logging()
      except Exception as e:
          logger.warning('Could not set up structured logging', error=str(e))

      try:
          from bot.config import settings
      except BaseException as e:
          tb = traceback.format_exc()
          _last_error = f'Config load failed: {e}\n{tb}'
          logger.error('Failed to load config', error=str(e), traceback=tb)
          await asyncio.Event().wait()
          return

      if not settings.is_configured:
          _last_error = 'BOT_TOKEN or DATABASE_URL is missing'
          logger.error(
              'BOT_TOKEN or DATABASE_URL is not set. '
              'Please add these environment variables in your Render service dashboard. '
              'The health server is running but the bot is NOT active.'
          )
          try:
              await asyncio.Event().wait()
          except asyncio.CancelledError:
              pass
          await runner.cleanup()
          return

      if settings.SENTRY_DSN:
          try:
              import sentry_sdk
              sentry_sdk.init(dsn=settings.SENTRY_DSN, environment=settings.ENVIRONMENT)
          except Exception as e:
              logger.warning('Sentry init failed', error=str(e))

      try:
          from aiogram import Bot, Dispatcher
          from aiogram.client.default import DefaultBotProperties
          from aiogram.enums import ParseMode
          from aiogram.fsm.storage.memory import MemoryStorage
          from bot.handlers import get_main_router
          from bot.middlewares import DatabaseMiddleware, I18nMiddleware, CallbackLoggingMiddleware
      except BaseException as e:
          tb = traceback.format_exc()
          _last_error = f'Import failed: {e}\n{tb}'
          logger.error('Critical import failed', error=str(e), traceback=tb)
          await asyncio.Event().wait()
          return

      storage = MemoryStorage()
      bot = Bot(
          token=settings.BOT_TOKEN,
          default=DefaultBotProperties(parse_mode=ParseMode.HTML),
      )
      dp = Dispatcher(storage=storage)
      dp.include_router(get_main_router())

      # IMPORTANT: Middleware registration order in aiogram 3.
      # outer_middleware uses LIFO — last registered runs FIRST.
      # Desired: CallbackLogging → Database → I18n → handler
      # Register in reverse: I18n first, Database second, CallbackLogging last.
      dp.update.outer_middleware(I18nMiddleware())
      dp.update.outer_middleware(DatabaseMiddleware())
      dp.update.outer_middleware(CallbackLoggingMiddleware())

      # Run bot (handles own errors, never raises)
      await run_bot(bot, dp, runner)

      # If bot stops, keep health server alive so Render doesn't restart us
      if _last_error:
          logger.error('Bot stopped with error — keeping health server alive for diagnostics')
          try:
              await asyncio.Event().wait()
          except asyncio.CancelledError:
              pass


  if __name__ == '__main__':
      try:
          asyncio.run(main())
      except (KeyboardInterrupt, SystemExit):
          logger.info('Bot stopped')
      except BaseException as e:
          logger.error('Unexpected fatal error', error=str(e), traceback=traceback.format_exc())
          raise
  