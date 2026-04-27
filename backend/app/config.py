from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    All runtime config comes from environment variables.
    Defaults are safe for local dev; production values are injected by Railway.
    """

    app_name: str = "Kit Platform V3"
    environment: str = "development"  # development | staging | production

    # --- Database -----------------------------------------------------------
    # Railway provisions Postgres and injects DATABASE_URL automatically.
    # Accepts both postgres:// (legacy) and postgresql:// — we normalize below.
    database_url: str = "sqlite:///./kit_platform_v3.db"

    # --- CORS ---------------------------------------------------------------
    # Comma-separated list of allowed origins. Example:
    #   CORS_ORIGINS=https://app.example.com,https://admin.example.com
    cors_origins: str = "http://localhost:3010"

    # --- Admin Basic Auth (temporary, until real auth is added) -------------
    # Protects /api/admin/* endpoints. Required in production.
    admin_username: str = "admin"
    admin_password: str = "change-me-in-production"

    # --- Misc ---------------------------------------------------------------
    # Whether to run the auto-seeder on startup. Disable in production once
    # the DB is seeded, to avoid overwriting admin edits.
    seed_on_startup: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = False

    # ------------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------------
    @field_validator("database_url")
    @classmethod
    def _normalize_database_url(cls, value: str) -> str:
        # Railway / Heroku style "postgres://" is deprecated in SQLAlchemy 2.x.
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql://", 1)
        return value

    # ------------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------------
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


settings = Settings()
