from __future__ import annotations

import asyncio
from collections.abc import Iterator
from typing import TYPE_CHECKING

from playwright.async_api import Browser

from config.settings import settings
from src.page_scraper import process_url_and_save_results

if TYPE_CHECKING:
    from src.output_manager import OutputManager


async def process_queue_with_workers(
    queue: asyncio.Queue[tuple[int, str] | None],
    browser: Browser,
    output_manager: OutputManager,
) -> None:
    while True:
        item = await queue.get()

        try:
            if item is None:
                return

            index, url = item
            await process_url_and_save_results(
                browser,
                index,
                url,
                output_manager,
            )
        finally:
            queue.task_done()


async def enqueue_urls(
    queue: asyncio.Queue[tuple[int, str] | None],
    urls: Iterator[str],
    worker_count: int,
) -> None:
    for index, url in enumerate(urls, start=1):
        await queue.put((index, url))

    for _ in range(worker_count):
        await queue.put(None)


async def queue_and_process_urls_with_workers(
    browser: Browser,
    urls: Iterator[str],
    output_manager: OutputManager,
) -> None:
    queue: asyncio.Queue[tuple[int, str] | None] = asyncio.Queue(
        maxsize=settings.MAX_CONCURRENT_PAGES
    )

    async with asyncio.TaskGroup() as task_group:
        for _ in range(settings.MAX_CONCURRENT_PAGES):
            task_group.create_task(
                process_queue_with_workers(queue, browser, output_manager)
            )

        task_group.create_task(
            enqueue_urls(
                queue,
                urls,
                settings.MAX_CONCURRENT_PAGES,
            )
        )
