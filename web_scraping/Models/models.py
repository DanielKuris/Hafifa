from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class OperationResult(Generic[T]):
    url: str
    success: bool
    data: T | None = None
    error: str | None = None


@dataclass
class PageData:
    title: str
    html: str
    resources: set[str]


@dataclass
class ScreenshotData:
    path: str
    format: str = "png"


@dataclass
class PageDataScrapeOperationResult(OperationResult[PageData]):
    pass


@dataclass
class ScreenshotOperationResult(OperationResult[ScreenshotData]):
    pass
