import asyncio

from playwright.async_api import async_playwright

from config.logger import get_logger
from config.settings import settings
from src.browser_manager import initialize_browser
from src.output_manager import ScrapeOutputWriter
from src.url_input_reader import iter_urls
from src.worker_manager import process_multiple_urls

logger = get_logger(__name__)


async def main() -> None:
    logger.info("Starting scraper")

    try:
        output_manager = ScrapeOutputWriter(settings.OUTPUT_DIRECTORY)

        async with async_playwright() as playwright:
            browser = await initialize_browser(playwright)

            try:
                await process_multiple_urls(
                    browser,
                    iter_urls(),
                    output_manager,
                )
            finally:
                await browser.close()

        logger.info("Scraper finished successfully")

    except Exception as error:
        logger.error(f"Scraper failed: {error}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
