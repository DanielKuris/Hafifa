import pandas as pd
from typing import BinaryIO
from logic.exceptions import InvalidCSVError , NoValidRowsError

def read_csv(file: BinaryIO) -> pd.DataFrame:
    try:
        return pd.read_csv(
            file,
            encoding="utf-8-sig",
        )
    except pd.errors.ParserError as exc:
        raise InvalidCSVError("CSV file could not be parsed") from exc
    except pd.errors.EmptyDataError as exc:
        raise NoValidRowsError("CSV file contains no data rows") from exc