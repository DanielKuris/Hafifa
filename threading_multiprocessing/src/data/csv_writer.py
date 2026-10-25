import csv
from collections.abc import Iterable
from dataclasses import fields
from pathlib import Path
from typing import TextIO

import pandas as pd

from src.models.stock_data import StockData


def write_dataframe_to_csv(
    dataframe: pd.DataFrame,
    destination_file: Path,
) -> None:
    destination_file.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(destination_file, index=False)


def create_stock_data_csv_writer(
    file: TextIO,
) -> csv.DictWriter:
    writer = csv.DictWriter(
        file,
        fieldnames=[field.name for field in fields(StockData)],
    )
    writer.writeheader()

    return writer


def stock_data_to_row(
    stock_data: StockData,
) -> dict[str, str | float]:
    row = {field.name: getattr(stock_data, field.name) for field in fields(StockData)}

    row["hour"] = stock_data.hour.isoformat()

    return row


def write_stock_data_to_csv(
    stock_data_items: Iterable[StockData],
    destination_file: Path,
) -> None:
    destination_file.parent.mkdir(parents=True, exist_ok=True)

    with destination_file.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = create_stock_data_csv_writer(file)

        for stock_data in stock_data_items:
            writer.writerow(stock_data_to_row(stock_data))
            file.flush()
