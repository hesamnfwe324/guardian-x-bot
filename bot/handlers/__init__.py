from aiogram import Router
from bot.handlers import start, security, moderation, economy, games, duels, statistics, settings, help, owner, welcome, tournaments


def get_main_router() -> Router:
    router = Router()
    router.include_router(start.router)
    router.include_router(welcome.router)
    router.include_router(security.router)
    router.include_router(moderation.router)
    router.include_router(economy.router)
    router.include_router(games.router)
    router.include_router(duels.router)
    router.include_router(statistics.router)
    router.include_router(settings.router)
    router.include_router(help.router)
    router.include_router(tournaments.router)
    router.include_router(owner.router)
    return router
