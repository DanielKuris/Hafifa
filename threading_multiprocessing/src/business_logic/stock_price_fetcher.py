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
from yfinance.exceptions import YFException

from src.config.logger import get_logger
from src.config.settings import settings
from src.models.stock_data import StockPriceTask

logger = get_logger(__name__)


def return_last_fetch_result(
    retry_state: RetryCallState,
) -> pd.DataFrame:
    logger.error(
        f"Stock price fetch failed after {retry_state.attempt_number} attempts "
        f"with exception: {retry_state.outcome.exception()}"
    )

    return pd.DataFrame()


def convert_datetime_to_utc(timestamp: datetime) -> datetime:
    if timestamp.tzinfo is None:
        return timestamp.replace(tzinfo=UTC)

    return timestamp.astimezone(UTC)


@retry(
    stop=stop_after_attempt(2),
    wait=wait_fixed(1),
    retry=retry_if_exception_type(YFException),
    retry_error_callback=return_last_fetch_result,
)
def get_stock_prices(
    stock_id: str,
    start: datetime,
    end: datetime,
) -> pd.DataFrame:
    ticker = yf.Ticker(stock_id)

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
    stock_id: str,
) -> float | None:
    if prices.empty:
        logger.error(f"No prices returned for {stock_id} at {original_timestamp}")

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
            f"minutes of {original_timestamp} for {stock_id}"
        )

        return None

    return current_price


def append_stock_data(
    results: list[dict[str, datetime | str | float]],
    stock_id: str,
    timestamp: datetime,
    prices: pd.DataFrame,
) -> None:
    current_price = extract_current_price(
        prices,
        timestamp,
        stock_id,
    )

    if current_price is None:
        return

    results.append({
        "timestamp": timestamp,
        "stock_id": stock_id,
        "current_price": current_price,
    })


def fetch_stock_data_for_group(
    task: StockPriceTask,
) -> pd.DataFrame:
    stock_id = task.stock_id
    requested_timestamps = list(task.timestamps)

    target_times = [
        convert_datetime_to_utc(timestamp)
        for timestamp in requested_timestamps
    ]

    start = min(target_times) - timedelta(hours=1)
    end = max(target_times) + timedelta(hours=1)

    prices = get_stock_prices(stock_id, start, end)
    prices = convert_price_index_to_utc(prices)

    results: list[dict[str, datetime | str | float]] = []

    for timestamp in requested_timestamps:
        append_stock_data(results, stock_id, timestamp, prices)

    return pd.DataFrame(results)