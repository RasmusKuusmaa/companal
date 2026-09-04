"""Application settings, loaded from environment variables / .env.

Fails fast at import time if required values (SECRET_KEY, DATABASE_URL) are
missing or malformed, rather than surfacing a confusing error on first request.
"""

from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- App ---
    APP_NAME: str = "Cadence API"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # --- Security ---
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # --- Database ---
    DATABASE_URL: str

    # --- File storage ---
    # Relative paths resolve against the process's current working
    # directory: `backend/storage` for a local `uvicorn` run from `backend/`,
    # `/app/storage` inside the Docker image (WORKDIR /app).
    STORAGE_ROOT: str = "./storage"
    MAX_UPLOAD_SIZE_BYTES: int = 20 * 1024 * 1024

    # --- AI feedback ---
    # Unset in local dev without an API key: the feedback endpoints raise a
    # clear 503 instead of failing at import/startup time.
    ANTHROPIC_API_KEY: str | None = None
    AI_MODEL: str = "claude-opus-5"
    # Hard ceiling on estimated Claude spend across every user in the
    # current calendar month (see `billing.service`). `None` disables the
    # cap - the default, so local dev without this set never trips it.
    GLOBAL_AI_MONTHLY_SPEND_CAP_USD: float | None = None

    # --- Billing (Stripe, dormant) ---
    # Unset until the premium phase actually wires Stripe in - see
    # `billing.models`'s module docstring. The webhook route is inert
    # without it: it accepts every request and does nothing.
    STRIPE_WEBHOOK_SECRET: str | None = None

    # --- CORS ---
    # Kept as a raw string, not list[str]: pydantic-settings tries to
    # JSON-decode "complex" (list/dict) env fields *before* field
    # validators run, which breaks a plain comma-separated value like
    # "http://a,http://b". Parse it ourselves instead, via the property
    # below.
    CORS_ORIGINS: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        if not self.CORS_ORIGINS.strip():
            return []
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return value

    @field_validator("GLOBAL_AI_MONTHLY_SPEND_CAP_USD", mode="before")
    @classmethod
    def blank_spend_cap_means_no_cap(cls, value: object) -> object:
        # pydantic-settings hands a raw "" for a blank .env value straight to
        # float parsing rather than treating it as unset - coerce here so
        # leaving the setting blank actually disables the cap.
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        if not value.startswith("postgresql+asyncpg://"):
            raise ValueError(
                "DATABASE_URL must use the asyncpg driver, e.g. "
                "postgresql+asyncpg://user:pass@host:5432/dbname"
            )
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
