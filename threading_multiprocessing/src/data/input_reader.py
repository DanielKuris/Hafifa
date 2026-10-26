from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

import yfinance as yf

from src.config.settings import settings


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


def get_timestamps_from_file(input_file: Path) -> list[datetime]:
    with input_file.open("r", encoding="utf-8") as file:
        return [datetime.fromisoformat(line.strip()) for line in file if line.strip()]


def group_timestamps_by_day(
    timestamps: list[datetime],
) -> dict[date, list[datetime]]:
    timestamps_by_day: dict[date, list[datetime]] = defaultdict(list)

    for timestamp in timestamps:
        timestamps_by_day[timestamp.date()].append(timestamp)

    return dict(timestamps_by_day)


def get_timestamps_per_stock_per_day(
    input_directory: Path,
) -> dict[str, dict[date, list[datetime]]]:
    timestamps: dict[str, dict[date, list[datetime]]] = {}

    for input_file in input_directory.glob(f"*{settings.TIMESTAMP_FILE_SUFFIX}"):
        stock_name = input_file.name.removesuffix(settings.TIMESTAMP_FILE_SUFFIX)
        stock_type = convert_name_to_stock_type(stock_name)
        stock_timestamps = get_timestamps_from_file(input_file)

        timestamps[stock_type] = group_timestamps_by_day(stock_timestamps)

    return timestamps
