from pathlib import Path

import pandas as pd
from codetiming import Timer

from src.config.logger import get_logger

logger = get_logger(__name__)


@Timer(
    name="write_dataframe_to_csv",
    text="{name} took {seconds:.2f} seconds",
    logger=logger.info,
)
def write_dataframe_to_csv(
    dataframe: pd.DataFrame,
    destination_file: Path,
) -> None:
    destination_file.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(destination_file, index=False)
