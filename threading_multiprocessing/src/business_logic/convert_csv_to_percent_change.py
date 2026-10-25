from pathlib import Path

import pandas as pd

from config.logger import get_logger
from config.settings import settings
from src.data.csv_writer import write_dataframe_to_csv

logger = get_logger(__name__)


def read_stock_prices_from_csv(source_file: Path) -> pd.DataFrame:
    return pd.read_csv(source_file, parse_dates=["hour"])


def sort_stock_prices_by_hour(stock_prices: pd.DataFrame) -> pd.DataFrame:
    stock_prices = stock_prices.copy()
    stock_prices["hour"] = pd.to_datetime(
        stock_prices["hour"],
        utc=True,
    )

    return stock_prices.sort_values(["hour", "stock_type"])


def find_previous_prices(stock_prices: pd.DataFrame) -> pd.DataFrame:
    current_prices = stock_prices.sort_values("hour").copy()
    previous_prices = stock_prices[["hour", "stock_type", "current_price"]].copy()

    previous_prices = previous_prices.rename(
        columns={
            "hour": "previous_hour",
            "current_price": "previous_price",
        }
    )

    current_prices = pd.merge_asof(
        current_prices,
        previous_prices.sort_values("previous_hour"),
        left_on="hour",
        right_on="previous_hour",
        by="stock_type",
        direction="backward",
        tolerance=pd.Timedelta(minutes=settings.PREVIOUS_PRICE_MAX_AGE_MINUTES),
        allow_exact_matches=False,
    )

    return current_prices


def remove_invalid_previous_prices(
    stock_prices: pd.DataFrame,
) -> pd.DataFrame:
    missing_previous_prices = stock_prices["previous_price"].isna()
    zero_previous_prices = stock_prices["previous_price"] == 0

    for _, row in stock_prices[
        missing_previous_prices | zero_previous_prices
    ].iterrows():
        reason = (
            "no previous price within the allowed time window"
            if pd.isna(row["previous_price"])
            else "previous price is zero"
        )

        logger.error(
            f"Cannot calculate percentage change for {row['stock_type']} "
            f"at {row['hour']}: {reason}"
        )

    return stock_prices[~missing_previous_prices & ~zero_previous_prices].copy()


def calculate_percentage_changes(
    stock_prices: pd.DataFrame,
) -> pd.DataFrame:
    stock_prices["percentage_change"] = (
        (stock_prices["current_price"] - stock_prices["previous_price"])
        / stock_prices["previous_price"]
        * settings.PERCENTAGE_DENOMINATOR
    )

    return stock_prices[["hour", "stock_type", "percentage_change"]]


def sort_by_stock_type_and_hour(
    percentage_changes: pd.DataFrame,
) -> pd.DataFrame:
    return percentage_changes.sort_values(
        ["stock_type", "hour"],
        ascending=[True, False],
    ).reset_index(drop=True)


def convert_df_to_sorted_percent_change(
    stock_prices: pd.DataFrame,
) -> pd.DataFrame:
    stock_prices = sort_stock_prices_by_hour(stock_prices)
    stock_prices = find_previous_prices(stock_prices)
    stock_prices = remove_invalid_previous_prices(stock_prices)

    percentage_changes = calculate_percentage_changes(stock_prices)
    return sort_by_stock_type_and_hour(percentage_changes)


def convert_csv_to_percent_change(
    source_file: Path,
    destination_file: Path,
) -> None:
    logger.info(f"Reading stock prices from {source_file}")
    stock_prices = read_stock_prices_from_csv(source_file)

    percentage_changes = convert_df_to_sorted_percent_change(stock_prices)

    write_dataframe_to_csv(percentage_changes, destination_file)
    logger.info(f"Wrote percentage changes to {destination_file}")
