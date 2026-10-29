from collections.abc import Iterator
from concurrent.futures import (
    FIRST_COMPLETED,
    Future,
    ThreadPoolExecutor,
    wait,
)
from dataclasses import asdict
from datetime import date, datetime

import pandas as pd
from tqdm import tqdm

from src.business_logic.stock_price_fetcher import fetch_stock_data_for_a_day
from src.config.logger import get_logger
from src.config.metrics import timed
from src.config.settings import settings
from src.models.stock_data import StockData

logger = get_logger(__name__)

StockPriceTask = tuple[str, list[datetime]]


def create_stock_price_tasks_per_day(
    stock_timestamps: dict[str, dict[date, list[datetime]]],
) -> Iterator[StockPriceTask]:
    for stock_type, timestamps_by_day in stock_timestamps.items():
        for timestamps in timestamps_by_day.values():
            yield stock_type, timestamps


def _submit_next_task(
    executor: ThreadPoolExecutor,
    tasks: Iterator[StockPriceTask],
) -> Future[list[StockData]] | None:
    try:
        stock_type, requested_timestamps = next(tasks)
    except StopIteration:
        return None

    return executor.submit(
        fetch_stock_data_for_a_day,
        stock_type,
        requested_timestamps,
    )


def submit_tasks_and_yield_stock_prices(
    executor: ThreadPoolExecutor,
    tasks: Iterator[StockPriceTask],
) -> Iterator[StockData]:
    pending: set[Future[list[StockData]]] = set()

    for _ in range(settings.MAX_WORKERS):
        future = _submit_next_task(executor, tasks)

        if future is None:
            break

        pending.add(future)

    while pending:
        completed, pending = wait(
            pending,
            return_when=FIRST_COMPLETED,
        )

        for future in completed:
            try:
                yield from future.result()
            except (ValueError, TypeError) as error:
                logger.error(f"Failed to fetch stock prices: {error}")

            next_future = _submit_next_task(executor, tasks)

            if next_future is not None:
                pending.add(next_future)


@timed
def fetch_stock_prices_concurrently(
    stock_timestamps: dict[str, dict[date, list[datetime]]],
) -> pd.DataFrame:
    total_tasks = sum(
        len(timestamps_by_day)
        for timestamps_by_day in stock_timestamps.values()
    )
    tasks = create_stock_price_tasks_per_day(stock_timestamps)

    with ThreadPoolExecutor(
        max_workers=settings.MAX_WORKERS,
    ) as executor:
        stock_prices = list(
            tqdm(
                submit_tasks_and_yield_stock_prices(executor, tasks),
                total=total_tasks,
                desc="Fetching stock prices",
            )
        )

    return pd.DataFrame(
        [asdict(stock_price) for stock_price in stock_prices]
    )