from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    PROJECT_NAME: str = "Mis Eventos API"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str


@lru_cache
def get_settings() -> Settings:
    return Settings()
