from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
)

from config import (
    BROWSER_CHANNEL,
    HEADLESS,
    NAVIGATION_TIMEOUT_MS,
)


async def initialize_browser(playwright: Playwright) -> Browser:
    return await playwright.chromium.launch(
        channel=BROWSER_CHANNEL,
        headless=HEADLESS,
    )


async def initialize_page(
    browser: Browser,
) -> tuple[BrowserContext, Page]:
    context = await browser.new_context()
    page = await context.new_page()
    page.set_default_navigation_timeout(NAVIGATION_TIMEOUT_MS)

    return context, page


async def close_browser(browser: Browser) -> None:
    await browser.close()
