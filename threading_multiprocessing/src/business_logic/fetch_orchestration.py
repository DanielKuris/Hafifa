from collections.abc import Iterator
from concurrent.futures import (
    FIRST_COMPLETED,
    Future,
    ThreadPoolExecutor,
    wait,
)

import pandas as pd
from codetiming import Timer
from tqdm import tqdm

import re
from src.business_logic.stock_price_fetcher import fetch_stock_data_for_group
from src.config.logger import get_logger
from src.config.settings import settings
from src.models.stock_data import StockPriceTask

logger = get_logger(__name__)


def validate_split_time(split_time: tuple[int, str]) -> None:
    if not isinstance(split_time, tuple) or len(split_time) != 2:
        raise ValueError(
            "split_time must be a tuple of (int, str), e.g., (1, 'H') for 1 hour"
        )

    if not isinstance(split_time[0], int) or split_time[0] < 1:
        raise ValueError("The first element of split_time must be at least 1")

    if not isinstance(split_time[1], str) or not re.fullmatch(
        r"[dwmy]",
        split_time[1].lower(),
    ):
        raise ValueError(
            "The second element of split_time must be one of: d, w, m, y."
        )

def convert_split_time_to_frequency(
    split_time: tuple[int, str],
) -> str:
    frequency_units = {
        "d": "D",
        "w": "W",
        "m": "ME",
        "y": "YE",
    }

    amount, unit = split_time

    return f"{amount}{frequency_units[unit.lower()]}"

def create_stock_price_tasks(
    stock_data: pd.DataFrame,
    split_time: tuple[int, str],
) -> list[StockPriceTask]:

    validate_split_time(split_time)

    frequency = convert_split_time_to_frequency(split_time)
    grouped_data = stock_data.groupby(
        [
            "stock_id",
            pd.Grouper(
                key="timestamp",
                freq=frequency,
            ),
        ]
    )

    return [
        StockPriceTask(
            stock_id=stock_id,
            timestamps=tuple(group["timestamp"]),
        )
        for (stock_id, _), group in grouped_data
    ]

def _submit_next_task(
    executor: ThreadPoolExecutor,
    tasks: Iterator[StockPriceTask],
) -> Future[pd.DataFrame] | None:
    try:
        task = next(tasks)
    except StopIteration:
        return None

    return executor.submit(fetch_stock_data_for_group, task)


def submit_tasks_and_yield_stock_prices(
    executor: ThreadPoolExecutor,
    tasks: Iterator[StockPriceTask],
) -> Iterator[pd.DataFrame]:
    pending: set[Future[pd.DataFrame]] = set()

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
            yield future.result()

            next_future = _submit_next_task(executor, tasks)

            if next_future is not None:
                pending.add(next_future)


@Timer(
    name="fetch_stock_prices_concurrently",
    text="{name} took {seconds:.2f} seconds",
    logger=logger.info,
)
def fetch_stock_prices_concurrently(
    tasks: list[StockPriceTask],
) -> pd.DataFrame:
    with ThreadPoolExecutor(
        max_workers=settings.MAX_WORKERS,
    ) as executor:
        stock_price_groups = list(
            tqdm(
                submit_tasks_and_yield_stock_prices(
                    executor,
                    iter(tasks),
                ),
                total=len(tasks),
                desc="Fetching stock prices",
            )
        )

    if not stock_price_groups:
        return pd.DataFrame()

    return pd.concat(stock_price_groups, ignore_index=True)