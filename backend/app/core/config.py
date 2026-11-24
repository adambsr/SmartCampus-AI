import json
from functools import lru_cache
from typing import Annotated

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SmartCampus API"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    environment: str = "development"
    debug: bool = Field(default=False, validation_alias="APP_DEBUG")
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:3000"]
    # PostgreSQL connection string (Neon). Never commit the real value.
    database_url: str | None = None
    visitor_session_secret: SecretStr | None = None
    visitor_session_idle_minutes: int = Field(default=30, gt=0)
    visitor_session_max_hours: int = Field(default=24, gt=0)
    visitor_session_access_token_minutes: int = Field(default=15, gt=0)
    visitor_session_creations_per_hour: int = Field(default=5, gt=0)
    account_jwt_secret: SecretStr | None = None
    account_refresh_days: int = Field(default=7, gt=0)
    account_invite_hours: int = Field(default=24, gt=0)
    # Production must keep this true. A loopback-only HTTP dev deployment may override it.
    auth_cookie_secure: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.startswith("["):
                value = json.loads(stripped)
                if not isinstance(value, list):
                    raise ValueError("CORS_ORIGINS must be a JSON list or comma-separated string")
            else:
                value = value.split(",")
        if not isinstance(value, list) or any(not isinstance(origin, str) for origin in value):
            raise ValueError("CORS_ORIGINS must contain strings")
        return [origin.strip() for origin in value if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
