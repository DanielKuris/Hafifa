from datetime import UTC, datetime, timedelta

import pandas as pd
import yfinance as yf
from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
)
from yfinance.exceptions import YFException, YFPricesMissingError

from src.config.logger import get_logger
from src.config.settings import settings
from src.models.stock_data import StockData

logger = get_logger(__name__)


def return_last_fetch_result(
    retry_state: RetryCallState,
) -> pd.DataFrame:
    logger.error(
        f"Stock price fetch failed after {retry_state.attempt_number} attempts with exception: {retry_state.outcome.exception()}",
    )

    if retry_state.outcome.failed:
        return pd.DataFrame()

    return retry_state.outcome.result()


def convert_datetime_to_utc(timestamp: datetime) -> datetime:
    if timestamp.tzinfo is None:
        return timestamp.replace(tzinfo=UTC)

    return timestamp.astimezone(UTC)


@retry(
    stop=stop_after_attempt(2),
    wait=wait_fixed(1),
    retry=retry_if_exception_type(YFPricesMissingError),
    retry_error_callback=return_last_fetch_result,
)
def get_stock_prices(
    stock_type: str,
    requested_timestamps: list[datetime],
) -> pd.DataFrame:
    ticker = yf.Ticker(stock_type)

    target_times = [
        convert_datetime_to_utc(timestamp) for timestamp in requested_timestamps
    ]

    start = (min(target_times) - timedelta(hours=1)).replace(microsecond=0)
    end = (max(target_times) + timedelta(hours=1)).replace(microsecond=0)

    try:
        return ticker.history(
            start=start,
            end=end,
            interval=settings.STOCK_PRICE_INTERVAL,
        )

    except YFPricesMissingError:
        raise

    except YFException as error:
        logger.error(
            f"Unexpected yfinance exception fetching prices for {stock_type}: {error}"
        )

        return pd.DataFrame()


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


def filter_prices_within_tolerance(
    prices: pd.DataFrame,
    target_time: datetime,
) -> pd.Series:
    tolerance = timedelta(minutes=settings.STOCK_PRICE_TOLERANCE_MINUTES)

    return prices.loc[
        (prices.index >= target_time - tolerance)
        & (prices.index <= target_time + tolerance),
        "Close",
    ]


def sort_prices_by_timestamp(
    available_prices: pd.Series,
) -> pd.Series:
    if available_prices.index.is_monotonic_increasing:
        return available_prices

    return available_prices.sort_index()


def find_insertion_index(
    available_prices: pd.Series,
    target_time: datetime,
) -> int:
    target_time = target_time.replace(microsecond=0)

    return available_prices.index.searchsorted(target_time)


def select_closest_price(
    available_prices: pd.Series,
    target_time: datetime,
    insertion_index: int,
) -> float:
    if insertion_index == 0:
        return float(available_prices.iloc[0])

    if insertion_index == len(available_prices):
        return float(available_prices.iloc[-1])

    previous_time = available_prices.index[insertion_index - 1]
    next_time = available_prices.index[insertion_index]

    previous_difference = target_time - previous_time
    next_difference = next_time - target_time

    if previous_difference <= next_difference:
        return float(available_prices.iloc[insertion_index - 1])

    return float(available_prices.iloc[insertion_index])


def find_closest_price(
    available_prices: pd.Series,
    target_time: datetime,
) -> float | None:
    if available_prices.empty:
        return None

    available_prices = sort_prices_by_timestamp(available_prices)
    target_time = target_time.replace(microsecond=0)

    insertion_index = find_insertion_index(
        available_prices,
        target_time,
    )

    return select_closest_price(
        available_prices,
        target_time,
        insertion_index,
    )


def extract_current_price(
    prices: pd.DataFrame,
    original_timestamp: datetime,
    stock_type: str,
) -> float | None:
    if prices.empty:
        logger.error(f"No prices returned for {stock_type} at {original_timestamp}")

        return None

    target_time_utc = convert_datetime_to_utc(original_timestamp)

    available_prices = filter_prices_within_tolerance(
        prices,
        target_time_utc,
    )

    current_price = find_closest_price(
        available_prices,
        target_time_utc,
    )

    if current_price is None:
        logger.error(
            f"No price found within {settings.STOCK_PRICE_TOLERANCE_MINUTES} "
            f"minutes of {original_timestamp} for {stock_type}"
        )

        return None

    return current_price


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

    except TypeError as error:
        logger.error(f"Failed to fetch prices for {stock_type}: {error}")

        return []
