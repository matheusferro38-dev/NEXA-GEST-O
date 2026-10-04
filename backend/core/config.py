import secrets
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_URL = f"sqlite:///{(PROJECT_ROOT / 'comerf.db').as_posix()}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    PROJECT_NAME: str = "Nexa Gestão - Gestão de Negócios Inteligente"
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    API_V1_STR: str = "/api/v1"
    API_BASE_URL: str = "/api/v1"
    DATABASE_URL: str = DEFAULT_DATABASE_URL
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    SESSION_COOKIE_NAME: str = "nexa_session"
    CSRF_COOKIE_NAME: str = "nexa_csrf"
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"
    CORS_ORIGINS: str = (
        "http://localhost:5500,http://127.0.0.1:5500,"
        "http://localhost:8000,http://127.0.0.1:8000"
    )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip().rstrip("/") for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @model_validator(mode="after")
    def validate_security_settings(self) -> "Settings":
        is_production = self.ENVIRONMENT.lower() == "production"
        if not self.SECRET_KEY:
            if is_production:
                raise ValueError("SECRET_KEY must be configured in production")
            self.SECRET_KEY = secrets.token_urlsafe(48)

        if is_production and (len(self.SECRET_KEY) < 32 or not self.COOKIE_SECURE):
            raise ValueError("Production requires a strong SECRET_KEY and secure cookies")
        if self.COOKIE_SAMESITE.lower() not in {"lax", "strict", "none"}:
            raise ValueError("COOKIE_SAMESITE must be lax, strict or none")
        if self.COOKIE_SAMESITE.lower() == "none" and not self.COOKIE_SECURE:
            raise ValueError("COOKIE_SECURE is required when COOKIE_SAMESITE is none")
        if "*" in self.cors_origins:
            raise ValueError("Wildcard CORS origins are not allowed")
        return self


settings = Settings()