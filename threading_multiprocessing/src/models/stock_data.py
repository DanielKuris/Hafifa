from dataclasses import dataclass
from datetime import datetime


@dataclass
class StockData:
    hour: datetime
    stock_type: str
    current_price: float


@dataclass
class StockFetchResult:
    hour: datetime
    stock_type: str
    success: bool
    result: StockData | None = None
    percentage_change: float | None = None
    error: str | None = None