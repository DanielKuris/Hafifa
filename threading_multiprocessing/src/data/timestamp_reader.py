from datetime import datetime
from pathlib import Path

import yfinance as yf

from config.settings import settings


def convert_name_to_stock_type(name: str) -> str:
    results = yf.Search(
        name,
        max_results=10,
        news_count=0,
        lists_count=0,
    ).quotes

    if not results:
        raise ValueError(f"No Yahoo Finance result found for '{name}'")

    return results[0]["symbol"]


def get_timestamps_per_stock(
    input_directory: Path,
) -> dict[str, list[datetime]]:
    timestamps: dict[str, list[datetime]] = {}

    for input_file in input_directory.glob(
        f"*{settings.TIMESTAMP_FILE_SUFFIX}"
    ):
        stock_name = input_file.name.removesuffix(
            settings.TIMESTAMP_FILE_SUFFIX
        )
        stock_type = convert_name_to_stock_type(stock_name)

        with input_file.open("r", encoding="utf-8") as file:
            timestamps[stock_type] = [
                datetime.fromisoformat(line.strip())
                for line in file
                if line.strip()
            ]

    return timestamps
