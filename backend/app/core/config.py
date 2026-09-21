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

    # Auth
    secret_key: str
    access_token_expire_minutes: int = 60
    algorithm: str = "HS256"

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
