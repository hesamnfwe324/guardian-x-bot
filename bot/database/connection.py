import ssl
import structlog
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from bot.config import settings

logger = structlog.get_logger()


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


_db_url, _connect_args = _prepare_db_url_and_ssl(settings.DATABASE_URL)

engine = create_async_engine(
    _db_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=settings.POOL_SIZE,
    max_overflow=settings.MAX_CONNECTIONS - settings.POOL_SIZE,
    connect_args=_connect_args,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def create_tables() -> None:
    from bot.database.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ensured")


async def close_db() -> None:
    await engine.dispose()
    logger.info("Database connection pool closed")
