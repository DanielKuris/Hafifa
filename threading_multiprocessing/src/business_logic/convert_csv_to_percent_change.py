from pathlib import Path

import pandas as pd

from config.settings import settings
from config.logger import get_logger
from src.data.csv_writer import write_dataframe_to_csv

logger = get_logger(__name__)


def read_stock_prices_from_csv(
    source_file: Path,
) -> pd.DataFrame:
    
    return pd.read_csv(source_file, parse_dates=["hour"])


def calculate_percentage_change(
    current_price: float,
    previous_price: float,
) -> float:
    if previous_price == 0:
        raise ValueError("Previous price cannot be zero")

    return (
        (current_price - previous_price)
        / previous_price
        * settings.PERCENTAGE_DENOMINATOR
    )


def filter_successful_fetches(
    stock_prices: pd.DataFrame,
) -> pd.DataFrame:
    successful_fetches = stock_prices.loc[
        stock_prices["success"]
    ].copy()

    successful_fetches["hour"] = pd.to_datetime(
        successful_fetches["hour"],
        utc=True,
    )

    return successful_fetches


def get_previous_price(
    successful_prices: pd.DataFrame,
    stock_type: str,
    hour: pd.Timestamp,
) -> float | None:
    previous_key = (
        stock_type,
        hour - pd.Timedelta(hours=1),
    )

    if previous_key not in successful_prices.index:
        
        return None

    return float(
        successful_prices.loc[previous_key, "current_price"]
    )




def convert_df_to_percent_change(
    stock_prices: pd.DataFrame,
) -> pd.DataFrame:
    successful_prices = filter_successful_fetches(stock_prices)
    successful_prices = successful_prices.set_index(
        ["stock_type", "hour"]
    )

    results: list[dict[str, object]] = []

    for (stock_type, hour), row in successful_prices.iterrows():
        previous_price = get_previous_price(
            successful_prices,
            stock_type,
            hour,
        )

        if previous_price is None:
            continue

        if previous_price == 0:
            logger.warning(
                "Cannot calculate percentage change for %s at %s: "
                "previous price is zero",
                stock_type,
                hour,
            )
            continue

        results.append(
            {
                "hour": hour,
                "stock_type": stock_type,
                "percentage_change": calculate_percentage_change(
                    float(row["current_price"]),
                    previous_price,
                ),
            }
        )

    return pd.DataFrame(
        results,
        columns=["hour", "stock_type", "percentage_change"],
    )



def convert_csv_to_percent_change(
    source_file: Path,
    destination_file: Path,
) -> None:
    logger.info("Reading stock prices from %s", source_file)
    stock_prices = read_stock_prices_from_csv(source_file)

    percentage_changes = convert_df_to_percent_change(stock_prices)

    write_dataframe_to_csv(percentage_changes, destination_file)
    logger.info("Wrote percentage changes to %s", destination_file)