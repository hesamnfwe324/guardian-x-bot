import ssl
import structlog
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from bot.config import settings

logger = structlog.get_logger()

# Module-level singletons (lazily initialized)
_engine = None
_session_maker = None


def _prepare_db_url_and_ssl(url: str):
    """Strip sslmode from URL and return (clean_url, connect_args)."""
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)

    ssl_ctx = None
    sslmode = params.pop("sslmode", [None])[0]
    if sslmode in ("require", "verify-ca", "verify-full"):
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
    elif sslmode == "disable":
        ssl_ctx = False

    new_query = urlencode(params, doseq=True)
    clean = urlunparse(parsed._replace(query=new_query))
    connect_args = {"ssl": ssl_ctx} if ssl_ctx is not None else {"ssl": False}
    return clean, connect_args


def _init_engine():
    """Create the async engine and session maker if not already done."""
    global _engine, _session_maker
    if _engine is not None:
        return

    db_url = settings.DATABASE_URL
    if not db_url:
        raise RuntimeError("DATABASE_URL is not configured")

    clean_url, connect_args = _prepare_db_url_and_ssl(db_url)

    _engine = create_async_engine(
        clean_url,
        echo=False,
        pool_pre_ping=True,
        pool_size=settings.POOL_SIZE,
        max_overflow=settings.MAX_CONNECTIONS - settings.POOL_SIZE,
        connect_args=connect_args,
    )
    _session_maker = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    safe_url = clean_url.split("@")[-1] if "@" in clean_url else "***"
    logger.info("Database engine created", url=safe_url)


# Backward-compatible module-level attributes
# These are accessed as `from bot.database.connection import engine, async_session_maker`
# We use module __getattr__ to lazily initialize on first access


def __getattr__(name):
    if name == "engine":
        _init_engine()
        return _engine
    if name == "async_session_maker":
        _init_engine()
        return _session_maker
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    _init_engine()
    async with _session_maker() as session:
        yield session


async def create_tables() -> None:
    from bot.database.models import Base
    _init_engine()
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ensured")


async def close_db() -> None:
    global _engine, _session_maker
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_maker = None
        logger.info("Database connection pool closed")
