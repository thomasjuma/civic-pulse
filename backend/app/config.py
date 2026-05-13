from functools import lru_cache
from pathlib import Path

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    whatsapp_access_token: str | None = Field(default=None, alias="WHATSAPP_ACCESS_TOKEN")
    whatsapp_phone_number_id: str | None = Field(default=None, alias="WHATSAPP_PHONE_NUMBER_ID")
    whatsapp_api_version: str = Field(default="v20.0", alias="WHATSAPP_API_VERSION")
    database_path: Path = Field(default=Path("civic_pulse.db"), alias="DATABASE_PATH")
    summary_job_interval_minutes: int = Field(default=1440, alias="SUMMARY_JOB_INTERVAL_MINUTES")
    summary_job_run_on_startup: bool = Field(default=False, alias="SUMMARY_JOB_RUN_ON_STARTUP")
    source_urls: tuple[AnyHttpUrl, ...] = (
        "https://www.oagkenya.go.ke",
        "https://www.parliament.go.ke/the-national-assembly/house-business/bills",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
