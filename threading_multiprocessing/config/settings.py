from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    stock_price_lookback_minutes: int = 5
    stock_price_forward_minutes: int = 1
    stock_price_interval: str = "1m"

    model_config = SettingsConfigDict(
        env_file="config/.env",
        extra="ignore",
    )


settings = Settings()