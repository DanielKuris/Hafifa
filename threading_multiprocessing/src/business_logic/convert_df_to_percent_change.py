import pandas as pd

from src.config.logger import get_logger
from src.config.metrics import timed
from src.config.settings import settings

logger = get_logger(__name__)


def convert_hour_column_to_utc(stock_prices: pd.DataFrame) -> pd.DataFrame:
    stock_prices = stock_prices.copy()
    stock_prices["hour"] = pd.to_datetime(stock_prices["hour"], utc=True)

    return stock_prices


def is_price_too_old(
    current_hour: pd.Series,
    previous_hour: pd.Series,
) -> pd.Series:
    previous_price_age = current_hour - previous_hour

    return previous_price_age > pd.Timedelta(
        minutes=settings.PREVIOUS_PRICE_MAX_AGE_MINUTES
    )


def find_previous_prices(stock_prices: pd.DataFrame) -> pd.DataFrame:
    stock_prices = convert_hour_column_to_utc(stock_prices)
    stock_prices = stock_prices.sort_values(["stock_type", "hour"]).copy()

    grouped_prices = stock_prices.groupby("stock_type")
    
    stock_prices["previous_price"] = grouped_prices["current_price"].shift(1)
    stock_prices["previous_hour"] = grouped_prices["hour"].shift(1)

    too_old = is_price_too_old(
        stock_prices["hour"],
        stock_prices["previous_hour"],
    )
    stock_prices.loc[too_old, "previous_price"] = float("nan")

    return stock_prices


def remove_invalid_previous_prices(
    stock_prices: pd.DataFrame,
) -> pd.DataFrame:
    missing_previous_prices = stock_prices["previous_price"].isna()
    zero_previous_prices = stock_prices["previous_price"] == 0
    invalid_previous_prices = missing_previous_prices | zero_previous_prices

    for _, row in stock_prices[invalid_previous_prices].iterrows():
        reason = (
            "no previous price within the allowed time window"
            if pd.isna(row["previous_price"])
            else "previous price is zero"
        )

        logger.error(
            f"Cannot calculate percentage change for {row['stock_type']} "
            f"at {row['hour']}: {reason}"
        )

    return stock_prices[~invalid_previous_prices].copy()


def calculate_percentage_changes(
    stock_prices: pd.DataFrame,
) -> pd.DataFrame:
    stock_prices = stock_prices.copy()
    stock_prices["percentage_change"] = (
        (stock_prices["current_price"] - stock_prices["previous_price"])
        / stock_prices["previous_price"]
        * 100
    )

    return stock_prices[["hour", "stock_type", "percentage_change"]]

@timed
def convert_stock_prices_to_percent_change(
    stock_prices: pd.DataFrame,
) -> pd.DataFrame:
    stock_prices = find_previous_prices(stock_prices)
    stock_prices = remove_invalid_previous_prices(stock_prices)

    percentage_changes = calculate_percentage_changes(stock_prices)

    return percentage_changes.sort_values(
        ["stock_type", "hour"],
        ascending=[True, False],
    ).reset_index(drop=True)