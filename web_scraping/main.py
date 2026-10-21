import asyncio

from playwright.async_api import async_playwright

from browser_manager import initialize_browser
from logger import get_logger
from output_manager import OutputManager
from url_input_reader import iter_urls
from worker_manager import queue_and_process_urls_with_workers

logger = get_logger(__name__)


async def main() -> None:
    logger.info("Starting scraper")

    try:
        output_manager = OutputManager()

        async with async_playwright() as playwright:
            browser = await initialize_browser(playwright)

            try:
                await queue_and_process_urls_with_workers(
                    browser,
                    iter_urls(),
                    output_manager,
                )
            finally:
                await browser.close()

        logger.info("Scraper finished successfully")

    except Exception:
        logger.exception("Scraper failed")
        raise


if __name__ == "__main__":
    asyncio.run(main())