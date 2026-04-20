from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root (…/financial_portfolio_management), not process cwd — avoids wrong DB / readonly surprises.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
import os

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Portfolio API"
    sqlite_path: Path = Field(default_factory=lambda: _PROJECT_ROOT / "portfolio.db")
    api_prefix: str = "/api"
    cors_origins: list[str] = ["*"]
    # Yahoo Finance ticker suffix, e.g. ".NS" (NSE India), "" for US tickers as-is
    market_suffix: str = ".NS"

    DATABASE_NAME: str = "notify_service"
    PEPPER: str = os.getenv("PEPPER", "dhpng")

    @field_validator("sqlite_path", mode="after")
    @classmethod
    def resolve_sqlite_path(cls, v: Path) -> Path:
        if v.is_absolute():
            return v.resolve()
        return (_PROJECT_ROOT / v).resolve()

    @property
    def database_url(self) -> str:
        p = self.sqlite_path
        return f"sqlite+aiosqlite:///{p.as_posix()}"



settings = Settings()
