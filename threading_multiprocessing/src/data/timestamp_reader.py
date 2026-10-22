from datetime import datetime
from pathlib import Path


def read_timestamps(input_file: Path) -> list[datetime]:
    with input_file.open("r", encoding="utf-8") as file:
        timestamps = [
            datetime.fromisoformat(line.strip())
            for line in file
            if line.strip()
        ]

    return timestamps