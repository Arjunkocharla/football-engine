"""Application dependency container."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    app_name: str = "football-engine"
    app_env: str = "development"
    api_prefix: str = "/api/v1"
    log_level: str = "INFO"
    database_url: str = "sqlite:///./football_engine.db"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@dataclass(frozen=True)
class AppContainer:
    settings: AppSettings
    session_factory: object  # sessionmaker[Session]


def build_container() -> AppContainer:
    from football_engine.infrastructure.db.session import create_session_factory

    settings = AppSettings()
    session_factory = create_session_factory(settings.database_url)
    return AppContainer(settings=settings, session_factory=session_factory)
