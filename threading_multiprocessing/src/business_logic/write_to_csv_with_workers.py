from collections.abc import Iterator
from concurrent.futures import (
    FIRST_COMPLETED,
    Future,
    ThreadPoolExecutor,
    wait,
)
from datetime import datetime
from pathlib import Path

from config.logger import get_logger
from config.settings import settings
from src.business_logic.stock_price_fetcher import fetch_stock_data
from src.data.csv_writer import write_stock_fetch_results_to_csv
from src.models.stock_data import StockFetchResult

logger = get_logger(__name__)

StockPriceTask = tuple[str, datetime]


def create_stock_price_tasks(
    stock_timestamps: dict[str, list[datetime]],
) -> Iterator[StockPriceTask]:
    for stock_type, hours in stock_timestamps.items():
        for hour in hours:
            yield stock_type, hour


def _submit_next_task(
    executor: ThreadPoolExecutor,
    tasks: Iterator[StockPriceTask],
    pending: set[Future[StockFetchResult]],
) -> bool:
    try:
        stock_type, hour = next(tasks)
    except StopIteration:
        
        return False

    pending.add(executor.submit(fetch_stock_data, stock_type, hour))

    return True


def _iter_completed_stock_prices(
    executor: ThreadPoolExecutor,
    tasks: Iterator[StockPriceTask],
) -> Iterator[StockFetchResult]:
    pending: set[Future[StockFetchResult]] = set()

    for _ in range(settings.MAX_WORKERS):
        if not _submit_next_task(executor, tasks, pending):
            break

    while pending:
        completed, pending = wait(
            pending,
            
            return_when=FIRST_COMPLETED,
        )

        for future in completed:
            yield future.result()
            _submit_next_task(executor, tasks, pending)


def write_stock_prices_concurrently(
    stock_timestamps: dict[str, list[datetime]],
    destination_file: Path,
) -> None:
    tasks = create_stock_price_tasks(stock_timestamps)

    with ThreadPoolExecutor(
        max_workers=settings.MAX_WORKERS,
    ) as executor:
        results = _iter_completed_stock_prices(executor, tasks)
        write_stock_fetch_results_to_csv(results, destination_file)
