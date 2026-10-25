from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, TypeVar

from playwright.async_api import Browser, BrowserContext, Page, Request
from playwright.async_api import Error as PlaywrightError

from config.logger import get_logger
from models.models import (
    OperationResult,
    PageData,
    PageDataResult,
    ScreenshotData,
    ScreenshotResult,
)
from src.browser_manager import initialize_page

R = TypeVar("R", bound=OperationResult)

if TYPE_CHECKING:
    from src.output_manager import OutputManager

logger = get_logger(__name__)


def track_requested_urls(page: Page) -> set[str]:
    requested_urls: set[str] = set()

    def record_request(request: Request) -> None:
        requested_urls.add(request.url)

    page.on("request", record_request)

    return requested_urls


async def navigate_to_url(page: Page, url: str) -> None:
    await page.goto(url, wait_until="domcontentloaded")


async def initialize_page_and_track_requested_urls(
    browser: Browser,
) -> tuple[BrowserContext, Page, set[str]]:
    context, page = await initialize_page(browser)
    resources = track_requested_urls(page)

    return context, page, resources


def create_failed_result(
    result_type: type[R],
    url: str,
    error: Exception,
) -> R:
    return result_type(
        url=url,
        success=False,
        error=str(error),
    )


async def get_page_data(
    page: Page,
    resources: set[str],
) -> PageData:
    return PageData(
        title=await page.title(),
        html=await page.content(),
        resources=resources,
    )


async def get_page_data_operation_result(
    page: Page,
    url: str,
    resources: set[str],
) -> PageDataResult:
    try:
        data = await get_page_data(page, resources)

        return PageDataResult(
            url=url,
            success=True,
            data=data,
        )

    except PlaywrightError as exc:
        logger.error(f"Playwright failed to collect page data for {url}")

        return create_failed_result(
            PageDataResult,
            url,
            exc,
        )


async def get_screenshot(
    page: Page,
    screenshot_path: Path,
) -> None:
    await page.screenshot(
        path=str(screenshot_path),
        full_page=True,
    )


async def get_screenshot_operation_result(
    page: Page,
    url: str,
    screenshot_path: Path,
) -> ScreenshotResult:

    try:
        await get_screenshot(page, screenshot_path)

        return ScreenshotResult(
            url=url,
            success=True,
            data=ScreenshotData(path=str(screenshot_path)),
        )

    except (PlaywrightError, OSError) as exc:
        screenshot_path.unlink(missing_ok=True)

        logger.error(f"Failed to capture screenshot for {url}")

        return create_failed_result(
            ScreenshotResult,
            url,
            exc,
        )


async def create_scrape_results(
    page: Page,
    url: str,
    screenshot_path: Path,
    resources: set[str],
) -> tuple[PageDataResult, ScreenshotResult]:
    page_result = await get_page_data_operation_result(
        page,
        url,
        resources,
    )

    screenshot_result = await get_screenshot_operation_result(
        page,
        url,
        screenshot_path,
    )

    return page_result, screenshot_result


async def process_url_and_save_results(
    browser: Browser,
    index: int,
    url: str,
    output_manager: OutputManager,
) -> None:
    output_directory = output_manager.create_url_directory(index)
    screenshot_path = output_manager.get_screenshot_path(output_directory)
    context = None

    try:
        context, page, resources = await initialize_page_and_track_requested_urls(
            browser
        )

        await navigate_to_url(page, url)

        page_result, screenshot_result = await create_scrape_results(
            page,
            url,
            screenshot_path,
            resources,
        )

    except PlaywrightError as exc:
        logger.error(f"Failed to process {url}")

        page_result = create_failed_result(
            PageDataResult,
            url,
            exc,
        )

        screenshot_result = create_failed_result(
            ScreenshotResult,
            url,
            exc,
        )

    finally:
        if context is not None:
            try:
                await context.close()
            except PlaywrightError:
                logger.error(f"Failed to close browser context for {url}")

    output_manager.save_results(output_directory, page_result, screenshot_result)
