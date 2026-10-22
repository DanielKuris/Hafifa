from __future__ import annotations

import asyncio
from collections.abc import Iterator
from typing import TYPE_CHECKING

from playwright.async_api import Browser

from config.settings import settings
from src.page_scraper import process_url_and_save_results

if TYPE_CHECKING:
    from src.output_manager import OutputManager


async def process_url_with_semaphore(
    semaphore: asyncio.Semaphore,
    browser: Browser,
    index: int,
    url: str,
    output_manager: OutputManager,
) -> None:
    async with semaphore:
        await process_url_and_save_results(
            browser,
            index,
            url,
            output_manager,
        )


async def process_urls_with_semaphore(
    browser: Browser,
    urls: Iterator[str],
    output_manager: OutputManager,
) -> None:
    semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_PAGES)

    async with asyncio.TaskGroup() as task_group:
        for index, url in enumerate(urls, start=1):
            task_group.create_task(
                process_url_with_semaphore(
                    semaphore,
                    browser,
                    index,
                    url,
                    output_manager,
                )
            )