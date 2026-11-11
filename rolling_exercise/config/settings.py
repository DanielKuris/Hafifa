from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="config/.env",
        extra="ignore",
    )

    DATABASE_URL: PostgresDsn
    AQI_ALERT_THRESHOLD: float = 300.0
    LIMIT_BEST_CITIES: int = 3


settings = Settings()
