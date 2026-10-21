import re
from collections.abc import Iterator
from pathlib import Path
from urllib.parse import urlparse

from config import INPUT_FILE


def extract_url(line: str) -> str:
    markdown_match = re.search(
        r"\[[^\]]*\]\((https?://[^)\s]+)\)",
        line,
    )

    if markdown_match:
        return markdown_match.group(1)

    plain_match = re.search(r"https?://\S+", line)

    if not plain_match:
        raise ValueError(f"No URL found in line: {line!r}")

    return plain_match.group(0).rstrip(".,;)")


def validate_url(url: str) -> str:
    parsed = urlparse(url)

    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
    ):
        raise ValueError(f"Invalid URL: {url!r}")

    return url


def extract_and_validate_url(line: str) -> str:
    return validate_url(extract_url(line))


def iter_urls(path: Path = INPUT_FILE) -> Iterator[str]:
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            try:
                yield extract_and_validate_url(line)
            except ValueError as exc:
                raise ValueError(
                    f"Invalid input on line {line_number} "
                    f"of {path.name}: {line!r}"
                ) from exc
