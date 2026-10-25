from pathlib import Path

import pandas as pd


def write_dataframe_to_csv(
    dataframe: pd.DataFrame,
    destination_file: Path,
) -> None:
    destination_file.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(destination_file, index=False)