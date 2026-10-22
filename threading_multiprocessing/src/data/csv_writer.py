import csv
from collections.abc import Iterable
from dataclasses import fields
from pathlib import Path
from typing import TextIO

import pandas as pd

from src.models.stock_data import StockData, StockFetchResult


def write_dataframe_to_csv(
    dataframe: pd.DataFrame,
    destination_file: Path,
) -> None:
    destination_file.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(destination_file, index=False)


def create_stock_fetch_csv_writer(
    file: TextIO,
) -> csv.DictWriter:
    writer = csv.DictWriter(
        file,
        fieldnames=[
            field.name
            for field in fields(StockFetchResult)
            if field.name != "result"
        ]
        + [
            field.name
            for field in fields(StockData)
            if field.name not in {"hour", "stock_type"}
        ],
    )
    writer.writeheader()

    return writer


def stock_fetch_result_to_row(
    result: StockFetchResult,
) -> dict[str, str | float | bool | None]:
    row = {
        field.name: getattr(result, field.name)
        for field in fields(StockFetchResult)
        if field.name != "result"
    }

    if result.result is not None:
        row.update(
            {
                field.name: getattr(result.result, field.name)
                for field in fields(StockData)
                if field.name not in {"hour", "stock_type"}
            }
        )

    row["hour"] = result.hour.isoformat()
    row["error"] = result.error or ""

    return row


def write_stock_fetch_results_to_csv(
    results: Iterable[StockFetchResult],
    destination_file: Path,
) -> None:
    destination_file.parent.mkdir(parents=True, exist_ok=True)

    with destination_file.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = create_stock_fetch_csv_writer(file)

        for result in results:
            writer.writerow(stock_fetch_result_to_row(result))
            file.flush()