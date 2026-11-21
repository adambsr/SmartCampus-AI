from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SmartCampus API"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    environment: str = "development"
    debug: bool = Field(default=False, validation_alias="APP_DEBUG")
    cors_origins: list[str] = ["http://localhost:3000"]
    # PostgreSQL connection string (Neon). Never commit the real value.
    database_url: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> str | list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
