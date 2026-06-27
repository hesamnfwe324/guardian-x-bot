"""
Database migration script for GUARDIAN X ULTIMATE.
Runs Alembic migrations and seeds initial data.
"""
import asyncio
import subprocess
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def run_migrations() -> None:
    from bot.utils.logger import setup_logging
    setup_logging()

    import structlog
    logger = structlog.get_logger()

    logger.info("Running database migrations...")
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    )
    if result.returncode != 0:
        logger.warning("Alembic migration output", stdout=result.stdout, stderr=result.stderr)

    logger.info("Creating tables via SQLAlchemy...")
    from bot.database.connection import create_tables, close_db, async_session_maker
    await create_tables()

    logger.info("Seeding achievements...")
    from bot.services.achievement_service import seed_achievements
    async with async_session_maker() as session:
        await seed_achievements(session)

    await close_db()
    logger.info("Migration complete!")


if __name__ == "__main__":
    asyncio.run(run_migrations())
