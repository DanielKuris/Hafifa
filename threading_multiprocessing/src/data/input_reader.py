from pathlib import Path

import pandas as pd
import yfinance as yf

from src.config.settings import settings


def convert_stock_name_to_stock_id(stock_name: str) -> str:
    results = yf.Search(
        stock_name,
        max_results=10,
        news_count=0,
        lists_count=0,
    ).quotes

    if not results:
        raise ValueError(f"No Yahoo Finance result found for '{stock_name}'")

    return results[0]["symbol"]


def get_timestamps_from_file(input_file: Path) -> list[pd.Timestamp]:
    with input_file.open("r", encoding="utf-8") as file:
        return [
            pd.Timestamp(line.strip())
            for line in file
            if line.strip()
        ]


def get_stock_data(input_directory: Path) -> pd.DataFrame:
    stock_data = []

    for input_file in input_directory.glob(
        f"*{settings.TIMESTAMP_FILE_SUFFIX}"
    ):
        stock_name = input_file.name.removesuffix(
            settings.TIMESTAMP_FILE_SUFFIX
        )
        stock_id = convert_stock_name_to_stock_id(stock_name)

        timestamps = get_timestamps_from_file(input_file)

        stock_data.extend(
            {
                "stock_id": stock_id,
                "timestamp": timestamp,
            }
            for timestamp in timestamps
        )

    return pd.DataFrame(stock_data, columns=["stock_id", "timestamp"])