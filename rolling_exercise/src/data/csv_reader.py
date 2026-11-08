import csv
from collections.abc import Iterator
from io import TextIOWrapper
from typing import BinaryIO


def read_csv_rows(
    file: BinaryIO,
) -> Iterator[dict[str | None, str | None]]:
    text_stream = TextIOWrapper(
        file,
        encoding="utf-8-sig",
        newline="",
    )

    try:
        yield from csv.DictReader(text_stream)
    finally:
        text_stream.detach()
