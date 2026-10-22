from datetime import UTC, datetime, timedelta

import pandas as pd
import yfinance as yf

from config.logger import get_logger
from config.settings import settings
from src.models.stock_data import StockData, StockFetchResult

logger = get_logger(__name__)


def convert_datetime_to_utc(hour: datetime) -> datetime:
    if hour.tzinfo is None:
        return hour.replace(tzinfo=UTC)

    return hour.astimezone(UTC)


def get_stock_price(
    stock_type: str,
    target_time: datetime,
) -> pd.DataFrame:
    ticker = yf.Ticker(stock_type)

    start = target_time - timedelta(
        hours=settings.STOCK_PRICE_LOOKBACK_HOURS
    )
    end = target_time + timedelta(
        hours=settings.STOCK_PRICE_FORWARD_HOURS
    )

    return ticker.history(
        start=start,
        end=end,
        interval=settings.STOCK_PRICE_INTERVAL,
    )


def convert_price_index_to_utc(prices: pd.DataFrame) -> pd.DataFrame:
    if prices.index.tz is None:
        prices.index = prices.index.tz_localize("UTC")
    else:
        prices.index = prices.index.tz_convert("UTC")

    return prices


def extract_current_price(
    prices: pd.DataFrame,
    target_time: datetime,
    stock_type: str,
    hour: datetime,
) -> float | None:
    if prices.empty:

        return None

    prices = convert_price_index_to_utc(prices)

    available_prices = prices.loc[
        prices.index <= target_time,
        "Close",
    ]

    if available_prices.empty:
        logger.warning(
            "No price available at or before %s for %s",
            hour,
            stock_type,
        )

        return None

    return float(available_prices.iloc[-1]) 



def fetch_stock_data(
    stock_type: str,
    hour: datetime,
) -> StockFetchResult:
    try:
        target_time = convert_datetime_to_utc(hour)
        prices = get_stock_price(stock_type, target_time)

        current_price = extract_current_price(
            prices,
            target_time,
            stock_type,
            hour,
        )

        if current_price is None:
            return StockFetchResult(
                hour=hour,
                stock_type=stock_type,
                success=False,
                error=f"No suitable price available for {stock_type} at {hour}",
            )

        stock_data = StockData(
            hour=hour,
            stock_type=stock_type,
            current_price=current_price,
        )


        return StockFetchResult(
            hour=hour,
            stock_type=stock_type,
            success=True,
            result=stock_data,
        )

    except (ValueError, TypeError, KeyError, OSError) as error:

        return StockFetchResult(
            hour=hour,
            stock_type=stock_type,
            success=False,
            error=str(error),
        )