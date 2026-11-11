from typing import BinaryIO

import pandas as pd


def read_csv(file: BinaryIO) -> pd.DataFrame:
    return pd.read_csv(
        file,
        encoding="utf-8-sig",
    )
