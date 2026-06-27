from pydantic_settings import BaseSettings
from pydantic import Field, model_validator
from typing import Optional


class Settings(BaseSettings):
    BOT_TOKEN: str
    WEBHOOK_URL: str = ""
    WEBHOOK_SECRET: str = "guardian_x_secret"
    WEBHOOK_PORT: int = 8080
    WEBHOOK_PATH: str = "/webhook"

    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"

    BOT_OWNER_ID: int = 0
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "production"

    SENTRY_DSN: Optional[str] = None
    MAX_CONNECTIONS: int = 10
    POOL_SIZE: int = 5

    DAILY_REWARD: int = 100
    WEEKLY_REWARD: int = 500
    MONTHLY_REWARD: int = 2000
    REFERRAL_REWARD: int = 150
    ACTIVITY_XP_PER_MSG: int = 2
    MAX_WARN_COUNT: int = 3
    FLOOD_LIMIT: int = 5
    FLOOD_WINDOW: int = 10

    SUPPORTED_LANGUAGES: list[str] = ["en", "fa", "ar", "tr", "ru", "es", "fr", "de"]
    DEFAULT_LANGUAGE: str = "en"

    @model_validator(mode="after")
    def fix_database_url(self) -> "Settings":
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = "postgresql+asyncpg://" + url[len("postgres://"):]
        elif url.startswith("postgresql://"):
            url = "postgresql+asyncpg://" + url[len("postgresql://"):]
        self.DATABASE_URL = url
        return self

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
