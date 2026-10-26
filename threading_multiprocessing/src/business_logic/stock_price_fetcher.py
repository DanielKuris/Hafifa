from datetime import UTC, datetime, timedelta

import pandas as pd
import yfinance as yf

from src.config.logger import get_logger
from src.config.settings import settings
from src.models.stock_data import StockData

logger = get_logger(__name__)


def convert_datetime_to_utc(timestamp: datetime) -> datetime:
    if timestamp.tzinfo is None:
        return timestamp.replace(tzinfo=UTC)

    return timestamp.astimezone(UTC)


def get_stock_prices(
    stock_type: str,
    requested_timestamps: list[datetime],
) -> pd.DataFrame:
    ticker = yf.Ticker(stock_type)

    target_times = [
        convert_datetime_to_utc(timestamp) for timestamp in requested_timestamps
    ]

    start = min(target_times) - timedelta(hours=1)
    end = max(target_times) + timedelta(hours=1)

    return ticker.history(
        start=start,
        end=end,
        interval=settings.STOCK_PRICE_INTERVAL,
    )


def convert_price_index_to_utc(
    prices: pd.DataFrame,
) -> pd.DataFrame:
    if prices.empty:
        logger.error("No prices returned to convert to UTC")

        return prices

    if prices.index.tz is None:
        prices.index = prices.index.tz_localize("UTC")
    else:
        prices.index = prices.index.tz_convert("UTC")

    return prices


def extract_current_price(
    prices: pd.DataFrame,
    original_timestamp: datetime,
    stock_type: str,
) -> float | None:
    if prices.empty:
        logger.error(f"No prices returned for {stock_type} at {original_timestamp}")

        return None

    target_time_utc = convert_datetime_to_utc(original_timestamp)

    available_prices = prices.loc[
        prices.index <= target_time_utc,
        "Close",
    ]

    if available_prices.empty:
        logger.error(
            f"No price available at or before {original_timestamp} for {stock_type}"
        )

        return None

    return float(available_prices.iloc[-1])


def create_stock_data(
    stock_type: str,
    original_timestamp: datetime,
    prices: pd.DataFrame,
) -> StockData | None:
    current_price = extract_current_price(
        prices,
        original_timestamp,
        stock_type,
    )

    if current_price is None:
        return None

    return StockData(
        hour=original_timestamp,
        stock_type=stock_type,
        current_price=current_price,
    )


def fetch_stock_data_for_a_day(
    stock_type: str,
    requested_timestamps: list[datetime],
) -> list[StockData]:
    if not requested_timestamps:
        return []

    try:
        prices = get_stock_prices(stock_type, requested_timestamps)
        prices = convert_price_index_to_utc(prices)

        results = [
            create_stock_data(stock_type, original_timestamp, prices)
            for original_timestamp in requested_timestamps
        ]

        return [result for result in results if result is not None]

    except (ValueError, TypeError) as error:
        logger.error(f"Failed to fetch prices for {stock_type}: {error}")

        return []
