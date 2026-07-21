from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "NeuroSOC"
    environment: str = "development"
    database_url: str = "sqlite:///./neurosoc.db"
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 60 * 24
    ai_provider: Literal["mock", "openai"] = "mock"
    upload_dir: str = "./uploads"
    rate_limit: int = 60
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATABASE_PATH = BASE_DIR / "neurosoc.db"
