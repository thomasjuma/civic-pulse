from functools import lru_cache
from pathlib import Path

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
    )

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    whatsapp_access_token: str | None = Field(default=None, alias="WHATSAPP_ACCESS_TOKEN")
    whatsapp_phone_number_id: str | None = Field(default=None, alias="WHATSAPP_PHONE_NUMBER_ID")
    whatsapp_api_version: str = Field(default="v20.0", alias="WHATSAPP_API_VERSION")
    whatsapp_verify_token: str | None = Field(default=None, alias="WHATSAPP_VERIFY_TOKEN")
    database_path: Path = Field(default=BACKEND_ROOT / "civic_pulse.db", alias="DATABASE_PATH")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    summary_job_interval_minutes: int = Field(default=10, alias="SUMMARY_JOB_INTERVAL_MINUTES")
    summary_job_run_on_startup: bool = Field(default=False, alias="SUMMARY_JOB_RUN_ON_STARTUP")
    source_urls: tuple[AnyHttpUrl, ...] = (
        "https://www.oagkenya.go.ke",
        "https://www.parliament.go.ke/the-national-assembly/house-business/bills",
    )

    @field_validator("database_path")
    @classmethod
    def resolve_database_path(cls, value: Path) -> Path:
        if str(value) == ":memory:" or value.is_absolute():
            return value
        return BACKEND_ROOT / value


@lru_cache
def get_settings() -> Settings:
    return Settings()
