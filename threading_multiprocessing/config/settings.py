from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    STOCK_PRICE_LOOKBACK_HOURS: int = 1
    STOCK_PRICE_FORWARD_HOURS: int = 1
    STOCK_PRICE_INTERVAL: str = "1h"
    PERCENTAGE_DENOMINATOR: float = 100.0
    MAX_WORKERS: int = 5
    DESTINATION_FILE_NAME: str = "percentage_changes.csv"
    TEMP_CSV_STOCK_PRICES_FILE: Path = Path("out/stock_prices.csv")
    TIMESTAMPS_FILE: Path = Path("src/input/bitcoin_dates.txt")
    OUTPUT_DIRECTORY: Path = Path("out")
    INPUT_DIRECTORY: Path = Path("src/input")
    TIMESTAMP_FILE_SUFFIX: str = "_dates.txt"
    YFINANCE_LOG_LEVEL: str = "CRITICAL"
    
    model_config = SettingsConfigDict(
        env_file="config/.env",
        extra="ignore",
    )


settings = Settings()