from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    DATABASE_URL: PostgresDsn
    TEST_DATABASE_URL: PostgresDsn | None = None
    AQI_ALERT_THRESHOLD: float


settings = Settings()
