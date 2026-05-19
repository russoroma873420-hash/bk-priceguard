"""Playwright-based scraper for JS-rendered sites with anti-bot protection

Use this when the simple requests-based scraper gets 401/403/Cloudflare blocks.
Playwright drives a real Chromium browser so JS executes and challenges
typically pass.

Requires one-time setup:
    python -m src.setup_browser
or:
    playwright install chromium
"""

import logging
from typing import Optional, Union

logger = logging.getLogger(__name__)

# Default User-Agent matching Windows 10 / Chrome 120
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# Default viewport (realistic desktop)
DEFAULT_VIEWPORT = {"width": 1920, "height": 1080}


def get_price_with_browser(
    url: str,
    selectors: Union[str, dict],
    wait_seconds: float = 2.0,
    timeout_ms: int = 30000,
    user_agent: str = DEFAULT_USER_AGENT,
) -> Optional[str]:
    """Fetch text content of an element using a headless Chromium browser.

    Args:
        url: Page URL to load.
        selectors: Either a single CSS selector string, or a dict with
            keys 'price', 'price_alt', 'price_alt2' (tried in order).
        wait_seconds: How long to wait after page load for JS to settle.
        timeout_ms: Page navigation timeout in milliseconds.
        user_agent: Browser User-Agent string.

    Returns:
        Element text content (stripped) if found, else None.
        Never raises — all errors are logged and return None.
    """
    # Import inside the function so the rest of the app doesn't crash if
    # Playwright isn't installed yet — only this function needs it.
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    except ImportError as e:
        logger.error(
            f"Playwright is not installed: {e}. "
            f"Run 'python -m src.setup_browser' to install."
        )
        return None

    # Normalize selectors to a list to try in priority order
    if isinstance(selectors, str):
        selector_list = [selectors]
    elif isinstance(selectors, dict):
        selector_list = [
            selectors[key]
            for key in ("price", "price_alt", "price_alt2")
            if selectors.get(key)
        ]
    else:
        logger.error(f"Invalid selectors type: {type(selectors)}")
        return None

    if not selector_list:
        logger.error("No selectors provided")
        return None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                context = browser.new_context(
                    user_agent=user_agent,
                    viewport=DEFAULT_VIEWPORT,
                    locale="ru-RU",
                    timezone_id="Europe/Moscow",
                    extra_http_headers={
                        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
                    },
                )

                page = context.new_page()

                logger.info(f"[playwright] Loading {url}")
                try:
                    page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
                except PlaywrightTimeout:
                    logger.warning(f"[playwright] Navigation timeout for {url}")
                    return None

                # Wait for JS / lazy content to settle
                page.wait_for_timeout(int(wait_seconds * 1000))

                # Try each selector in priority order
                for selector in selector_list:
                    try:
                        element = page.query_selector(selector)
                    except Exception as e:
                        logger.debug(f"[playwright] Selector '{selector}' query failed: {e}")
                        continue

                    if not element:
                        logger.debug(f"[playwright] Selector '{selector}' did not match")
                        continue

                    try:
                        text = element.text_content()
                    except Exception as e:
                        logger.debug(f"[playwright] text_content failed for '{selector}': {e}")
                        continue

                    if text and text.strip():
                        text = text.strip()
                        logger.info(
                            f"[playwright] Found via '{selector}': '{text[:60]}'"
                        )
                        return text

                logger.warning(
                    f"[playwright] None of the selectors matched on {url}: {selector_list}"
                )
                return None

            finally:
                browser.close()

    except Exception as e:
        logger.error(f"[playwright] Unexpected error scraping {url}: {e}")
        return None
