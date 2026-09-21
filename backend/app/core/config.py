"""
Application settings, read entirely from environment variables (.env).

Nothing country- or currency-specific lives here — that's the point. If you
find yourself wanting to add e.g. `DEFAULT_CURRENCY = "USD"`, don't: that's a
per-user choice made at signup, not a global constant.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str
    # Managed Postgres (Supabase, RDS, etc.) requires TLS; a local dev
    # instance typically doesn't expose it at all.
    db_ssl_require: bool = False

    # Auth
    secret_key: str
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30
    algorithm: str = "HS256"

    # CORS — comma-separated origins, e.g. "https://app.example.com,https://staging.example.com".
    # "*" is fine for local dev but should be the real frontend origin(s) in production.
    cors_origins: str = "*"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    # Email
    email_provider: str = "smtp"  # smtp | sendgrid | resend
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    email_from_address: str = "alerts@example.com"
    sendgrid_api_key: str | None = None
    resend_api_key: str | None = None

    # Reminder job
    reminder_check_hour_utc: int = 8
    default_reminder_days_before: int = 3


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
