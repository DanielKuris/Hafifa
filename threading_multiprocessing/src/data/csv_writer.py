from pathlib import Path

import pandas as pd

from src.models.stock_data import StockFetchResult


def convert_results_to_dataframe(results: list[StockFetchResult]) -> pd.DataFrame:
    
    return pd.DataFrame(
        [
            {
                "hour": result.hour,
                "stock_type": result.stock_type,
                "percentage_change": result.percentage_change,
                "success": result.success,
            }
            for result in results
        ],
        columns=["hour", "stock_type", "percentage_change", "success"],
    )

def write_results_to_csv(
    results: list[StockFetchResult],
    destination_file: Path,
) -> None:
    dataframe = convert_results_to_dataframe(results)
    dataframe.to_csv(destination_file, index=False)