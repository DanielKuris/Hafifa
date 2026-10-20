
import asyncio
import json
import re
import shutil
from collections.abc import Iterator
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    Request,
    async_playwright,
)

""" Chrome browser scraper using Playwright. """
""" Scraping operations include HTML, title, screenshot, and resource URLs. """

# ---------- Configuration ----------

BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "urls.input"
OUTPUT_DIR = BASE_DIR / "output"

MAX_CONCURRENT_PAGES = 5
NAVIGATION_TIMEOUT_MS = 30_000


# ---------- URL input ----------

def parse_url(line: str) -> str:
    """Extract an HTTP(S) URL from Markdown or plain text."""

    markdown_match = re.search(
        r"\[[^\]]*\]\((https?://[^)\s]+)\)",
        line,
    )

    if markdown_match:
        url = markdown_match.group(1)
    else:
        plain_match = re.search(r"https?://\S+", line)

        if not plain_match:
            raise ValueError(f"No URL found in line: {line!r}")

        url = plain_match.group(0).rstrip(".,;)")

    parsed = urlparse(url)

    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"Invalid URL: {url!r}")

    return url



def iter_urls(path: Path) -> Iterator[str]:
    """Yield URLs from the input file one line at a time. (Generator)"""

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            try:
                yield parse_url(line)
            except ValueError as exc:
                raise ValueError(
                    f"Invalid input on line {line_number} "
                    f"of {path.name}: {line!r}"
                ) from exc


# ---------- Output setup ----------

def prepare_output_directory() -> None:
    """Create output/ and remove its existing subdirectories."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for path in OUTPUT_DIR.iterdir():
        if path.is_dir():
            shutil.rmtree(path)


def create_url_directory(index: int) -> Path:
    """Create and return the output directory for one URL."""

    output_path = OUTPUT_DIR / f"url_{index}"
    output_path.mkdir(parents=True, exist_ok=True)

    return output_path


# ---------- Browser setup ----------

async def initialize_browser(playwright: Playwright) -> Browser:
    """Launch Chrome."""

    return await playwright.chromium.launch(
        channel="chrome",
        headless=True,
    )


async def initialize_page(
    browser: Browser,
) -> tuple[BrowserContext, Page]:
    """Create an isolated browser context and page."""

    context = await browser.new_context()
    page = await context.new_page()
    page.set_default_navigation_timeout(NAVIGATION_TIMEOUT_MS)

    return context, page


def initialize_resource_tracking(page: Page) -> list[str]:
    """Record URLs requested while the page loads."""

    requested_urls: list[str] = []

    def record_request(request: Request) -> None:
        requested_urls.append(request.url)

    page.on("request", record_request)

    return requested_urls


# ---------- Navigation ----------

async def navigate_to_url(page: Page, url: str) -> None:
    """Navigate to a website and wait for its DOM to load."""

    await page.goto(url, wait_until="domcontentloaded")


# ---------- Scraping operations ----------

async def scrape_html(page: Page) -> str:
    """Retrieve the current page HTML."""

    return await page.content()

def deduplicate_resource_urls(requested_urls: list[str]) -> list[str]:
    """Remove duplicate URLs while preserving their order."""
    return list(dict.fromkeys(requested_urls))

async def scrape_screenshot(page: Page, path: Path) -> None:
    """Capture the entire page and save it as a PNG."""

    await page.screenshot(
        path=str(path),
        full_page=True,
    )


async def scrape_title(page: Page) -> str:
    """Retrieve the page title."""

    return await page.title()


# ---------- Saving results ----------

def save_json(data: dict[str, Any], path: Path) -> None:
    """Write data to a JSON file."""

    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


# ---------- Processing one URL ----------

async def process_page(
    browser: Browser,
    url: str,
    index: int,
) -> dict[str, Any]:
    """Scrape one URL and save its results."""

    output_path = create_url_directory(index)
    json_path = output_path / "browser.json"
    screenshot_path = output_path / "screenshot.png"

    context: BrowserContext | None = None

    try:
        # initialize the browser context and page for scraping
        context, page = await initialize_page(browser)

        requested_urls = initialize_resource_tracking(page)

        await navigate_to_url(page, url)

        # scrape the page content and resources
        html = await scrape_html(page)
        resources = deduplicate_resource_urls(requested_urls)

        await scrape_screenshot(page, screenshot_path)

        data = {
            "url": url,
            "title": await scrape_title(page),
            "html": html,
            "resources": resources,
        }

        save_json(data, json_path)

        return {
            "url": url,
            "output_directory": str(output_path),
            "success": True,
        }

    except Exception as exc:  # noqa: BLE001
        error_data = {
            "url": url,
            "error": str(exc),
        }

        # save the error information to a JSON file
        save_json(error_data, json_path)

        return {
            "url": url,
            "output_directory": str(output_path),
            "success": False,
            "error": str(exc),
        }

    finally:
        if context is not None:
            await context.close()


# ---------- Concurrent processing ----------

async def process_with_limit(
    browser: Browser,
    url: str,
    index: int,
    semaphore: asyncio.Semaphore,
) -> dict[str, Any]:
    """Process a URL while respecting the concurrency limit."""

    async with semaphore:
        return await process_page(browser, url, index)


async def process_urls(
    browser: Browser,
    urls: Iterator[str],
) -> None:
    """Consume the URL generator and process URLs concurrently."""

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_PAGES)
    tasks: set[asyncio.Task[dict[str, Any]]] = set()

    try:
        for index, url in enumerate(urls, start=1):
            task = asyncio.create_task(
                process_with_limit(browser, url, index, semaphore)
            )
            tasks.add(task)

            # Keep the number of scheduled tasks bounded.
            if len(tasks) >= MAX_CONCURRENT_PAGES:
                done, pending = await asyncio.wait(
                    tasks,
                    return_when=asyncio.FIRST_COMPLETED,
                )

                tasks = set(pending)

                for completed_task in done:
                    await completed_task

        # Process any tasks still running after the generator is exhausted.
        for completed_task in asyncio.as_completed(tasks):
            await completed_task

    finally:
        # Finish remaining tasks before the browser is closed.
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


# ---------- Application entry point ----------

async def main() -> None:
    """Initialize the scraper and run it."""

    prepare_output_directory()

    async with async_playwright() as playwright:
        browser = await initialize_browser(playwright)

        try:
            urls = iter_urls(INPUT_FILE)
            await process_urls(browser, urls)

        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
    print("Scraping completed. Check the output/ directory for results.")
