from functools import lru_cache

from pydantic import EmailStr, Field, field_validator
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

    # ----- Auth & RBAC -----
    JWT_SECRET: str = Field(min_length=16)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_TTL_MINUTES: int = 15
    REFRESH_TOKEN_TTL_DAYS: int = 7

    # ----- Seed admin -----
    SEED_ADMIN_EMAIL: EmailStr | None = None
    SEED_ADMIN_PASSWORD: str | None = None

    # ----- CORS -----
    # por defecto (dev local).
    CORS_ORIGINS: str = "http://localhost:5173"

    @field_validator("JWT_SECRET")
    @classmethod
    def _no_placeholder_secret(cls, value: str) -> str:
        if value.strip().lower() in {"changeme", "secret", "todo"}:
            raise ValueError("JWT_SECRET no puede ser un placeholder")
        return value

    @property
    def cors_origins_list(self) -> list[str]:
        raw = (self.CORS_ORIGINS or "").strip()
        if not raw:
            return ["http://localhost:5173"]
        return [origin.strip() for origin in raw.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
