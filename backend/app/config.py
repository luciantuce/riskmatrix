import ipaddress
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings

from app.logging import log


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

    # --- IP allowlist (private beta gate) -----------------------------------
    # Comma-separated list of IPs / CIDRs allowed to reach the API.
    # Empty (default) disables the gate entirely (fail-open). Examples:
    #   ALLOWED_IPS=86.55.123.45
    #   ALLOWED_IPS=86.55.123.45,212.45.0.0/24,2a02:1234::/32
    # /health is exempted so Railway healthchecks always pass.
    allowed_ips: str = ""

    # --- Clerk Auth ---------------------------------------------------------
    # Set by Railway (Sprint 1). Empty string = auth middleware disabled
    # (only acceptable for local dev without Clerk configured).
    clerk_secret_key: str = ""
    clerk_webhook_secret: str = ""
    clerk_jwks_url: str = ""
    bootstrap_super_admin_email: str = ""

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
    def allowed_networks(self) -> list:
        """
        Parse ALLOWED_IPS into a list of ip_network objects.
        Empty list = no restriction (fail-open).
        Invalid entries are logged and skipped, not raised.
        """
        out = []
        for raw in self.allowed_ips.split(","):
            entry = raw.strip()
            if not entry:
                continue
            try:
                # ip_network accepts both single IPs (auto /32 or /128) and CIDR
                out.append(ipaddress.ip_network(entry, strict=False))
            except ValueError:
                log.warning("allowed_ips_invalid_entry", entry=entry)
        return out

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


settings = Settings()
