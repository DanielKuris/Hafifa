from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="config/.env",
        extra="ignore",
    )

    DATABASE_URL: PostgresDsn = (
        "postgresql+psycopg://postgres:postgres@localhost:5433/air_quality_db"
    )
    TEST_DATABASE_URL: PostgresDsn | None = None
    AQI_ALERT_THRESHOLD: float = 300.0
    DB_FLUSH_BATCH_SIZE: int = Field(default=500, gt=0)


settings = Settings()
