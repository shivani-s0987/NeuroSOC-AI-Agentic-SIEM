from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "NeuroSOC"
    app_env: Literal["development", "testing", "production"] = "development"
    database_url: str = "sqlite:///./neurosoc.db"
    jwt_secret: str = "dev-secret-change-me"
    jwt_refresh_secret: str = "dev-refresh-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_issuer: str | None = None
    jwt_audience: str | None = None
    jwt_expiry_minutes: int = Field(default=60, ge=1, le=1440)
    refresh_expiry_days: int = Field(default=7, ge=1, le=365)
    password_reset_expiry_minutes: int = Field(default=30, ge=5, le=1440)
    auth_rate_limit_per_minute: int = Field(default=10, ge=1, le=1000)
    ai_provider: Literal["fallback", "mock", "openai", "external"] = "fallback"
    ai_api_key: str | None = None
    ai_base_url: str = "https://api.openai.com/v1"
    ai_model: str = "gpt-4o-mini"
    ai_timeout_seconds: int = Field(default=30, ge=1, le=300)
    ai_retries: int = Field(default=1, ge=0, le=3)
    ai_max_tokens: int = Field(default=1800, ge=256, le=16000)
    ai_temperature: float = Field(default=0.2, ge=0, le=2)
    ai_context_max_events: int = Field(default=50, ge=1, le=500)
    ai_max_field_chars: int = Field(default=4000, ge=100, le=20000)
    ai_enabled: bool = True
    upload_dir: Path = Path("./uploads")
    upload_max_bytes: int = Field(default=10 * 1024 * 1024, ge=1024, le=100 * 1024 * 1024)
    rate_limit: int = Field(default=60, ge=1)
    cors_origins: str = "http://localhost:5173"
    log_level: str = "INFO"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = ""
    celery_result_backend: str = ""
    worker_max_attempts: int = Field(default=5, ge=1, le=20)
    worker_poll_seconds: int = Field(default=2, ge=1, le=60)
    realtime_max_connections: int = Field(default=1000, ge=1, le=10000)
    trusted_hosts: str = "localhost,127.0.0.1,testserver"
    database_pool_size: int = Field(default=5, ge=1, le=100)
    database_max_overflow: int = Field(default=10, ge=0, le=200)
    database_pool_timeout_seconds: int = Field(default=30, ge=1, le=300)
    backup_dir: Path = Path("./backups")
    backup_retention_days: int = Field(default=30, ge=1, le=3650)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def allowed_hosts(self) -> list[str]:
        return [host.strip() for host in self.trusted_hosts.split(",") if host.strip()]

    @model_validator(mode="after")
    def validate_runtime(self) -> "Settings":
        scheme = self.database_url.split(":", 1)[0]
        if scheme not in {"sqlite", "postgresql", "postgresql+psycopg"}:
            raise ValueError("DATABASE_URL must use sqlite or PostgreSQL")
        if self.app_env == "production":
            insecure = {"dev-secret-change-me", "dev-refresh-secret-change-me", "change-me"}
            if self.jwt_secret in insecure or len(self.jwt_secret) < 32:
                raise ValueError("A secure JWT_SECRET is required in production")
            if self.jwt_refresh_secret in insecure or len(self.jwt_refresh_secret) < 32:
                raise ValueError("A secure JWT_REFRESH_SECRET is required in production")
            if self.database_url.startswith("sqlite"):
                raise ValueError("Production requires PostgreSQL; SQLite fallback is not allowed")
            if not self.database_url.startswith(("postgresql://", "postgresql+psycopg://")):
                raise ValueError("Production DATABASE_URL must be PostgreSQL")
            if "*" in self.cors_origins or "localhost" in self.cors_origins:
                raise ValueError(
                    "Production CORS_ORIGINS must not contain wildcard or localhost origins"
                )
            if (
                "change-me" in self.jwt_secret.lower()
                or "change-me" in self.jwt_refresh_secret.lower()
            ):
                raise ValueError("Development secrets are not allowed in production")
        return self


settings = Settings()
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATABASE_PATH = BASE_DIR / "neurosoc.db"
