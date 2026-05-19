"""Production web scraper for real e-commerce sites

This module provides real scraping (no mock fallback). It handles:
- Multiple CSS selector fallbacks (span/div/h3 price tags)
- Cloudflare/anti-bot detection
- Custom headers per site
- Retry logic with delays
- Proper error reporting
"""

import logging
import re
import time
from typing import Optional, Dict, List

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ScraperError(Exception):
    """Base scraper error"""
    pass


class CloudflareBlockedError(ScraperError):
    """Site is protected by Cloudflare or similar anti-bot"""
    pass


class PriceNotFoundError(ScraperError):
    """Price could not be extracted from page"""
    pass


# Indicators that a site is blocked by anti-bot protection
ANTI_BOT_INDICATORS = [
    'cloudflare',
    'cf-browser-verification',
    'cf-challenge',
    'just a moment',
    'checking your browser',
    'enable javascript',
    'access denied',
    'ddos protection',
    'qrator',
    'incapsula',
    'distil_r_captcha',
]

# Default headers for requests
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
}


def detect_anti_bot(html: str) -> Optional[str]:
    """Detect if response is from anti-bot protection

    Args:
        html: HTML content to check

    Returns:
        Name of detected protection or None
    """
    if not html:
        return None

    html_lower = html.lower()

    for indicator in ANTI_BOT_INDICATORS:
        if indicator in html_lower:
            logger.warning(f"Anti-bot detected: '{indicator}'")
            return indicator

    # Check for very short responses (often indicates blocking)
    if len(html) < 500:
        logger.warning(f"Suspiciously short response: {len(html)} bytes")
        return "short_response"

    return None


def fetch_real_url(url: str, headers: Optional[Dict] = None,
                   timeout: int = 15, retries: int = 3,
                   retry_delay: int = 5) -> str:
    """Fetch URL from real website (NO mock fallback)

    Args:
        url: URL to fetch
        headers: Custom headers (merged with defaults)
        timeout: Request timeout in seconds
        retries: Number of retry attempts
        retry_delay: Delay between retries in seconds

    Returns:
        HTML content as string

    Raises:
        ScraperError: For general scraping errors
        CloudflareBlockedError: If site is protected by anti-bot
    """
    # Merge headers
    request_headers = DEFAULT_HEADERS.copy()
    if headers:
        request_headers.update(headers)

    last_error = None

    for attempt in range(1, retries + 1):
        try:
            logger.info(f"Fetching {url} (attempt {attempt}/{retries})")

            response = requests.get(
                url,
                headers=request_headers,
                timeout=timeout,
                allow_redirects=True
            )

            # Check HTTP status
            if response.status_code == 403:
                raise CloudflareBlockedError(
                    f"HTTP 403 Forbidden — likely blocked by anti-bot (url={url})"
                )

            if response.status_code == 429:
                logger.warning(f"Rate limited (429), waiting {retry_delay}s...")
                time.sleep(retry_delay)
                last_error = ScraperError(f"HTTP 429 Rate Limited")
                continue

            if response.status_code == 503:
                # Often used by Cloudflare for challenges
                anti_bot = detect_anti_bot(response.text)
                if anti_bot:
                    raise CloudflareBlockedError(
                        f"HTTP 503 with anti-bot indicator '{anti_bot}' (url={url})"
                    )

            response.raise_for_status()

            # Check for anti-bot content in response body
            anti_bot = detect_anti_bot(response.text)
            if anti_bot:
                raise CloudflareBlockedError(
                    f"Anti-bot protection detected: '{anti_bot}' (url={url})"
                )

            logger.info(f"Successfully fetched {url} ({len(response.text)} bytes)")
            return response.text

        except CloudflareBlockedError:
            # Don't retry on anti-bot blocks
            raise

        except requests.exceptions.Timeout as e:
            last_error = ScraperError(f"Timeout fetching {url}: {e}")
            logger.warning(f"Timeout on attempt {attempt}: {e}")

        except requests.exceptions.ConnectionError as e:
            last_error = ScraperError(f"Connection error for {url}: {e}")
            logger.warning(f"Connection error on attempt {attempt}: {e}")

        except requests.exceptions.HTTPError as e:
            last_error = ScraperError(f"HTTP error for {url}: {e}")
            logger.warning(f"HTTP error on attempt {attempt}: {e}")

        except requests.exceptions.RequestException as e:
            last_error = ScraperError(f"Request error for {url}: {e}")
            logger.warning(f"Request error on attempt {attempt}: {e}")

        # Wait before retry (but not on last attempt)
        if attempt < retries:
            logger.info(f"Waiting {retry_delay}s before retry...")
            time.sleep(retry_delay)

    # All retries exhausted
    raise last_error or ScraperError(f"Failed to fetch {url} after {retries} attempts")


def extract_price_from_text(text: str) -> Optional[float]:
    """Extract numeric price from text string

    Handles various Russian price formats:
    - "35 000 ₽"
    - "35000 руб."
    - "35,000.00"
    - "от 35 000 ₽"

    Args:
        text: Text containing price

    Returns:
        Price as float or None if not found
    """
    if not text:
        return None

    # Remove non-breaking spaces and normalize whitespace
    cleaned = text.replace('\xa0', ' ').replace(' ', ' ').strip()

    # Remove currency symbols and labels
    cleaned = re.sub(r'[₽$€£руб\.RUBUSDEUR]', '', cleaned, flags=re.IGNORECASE)

    # Find numbers with possible separators
    # Match: 12 345.67 or 12,345.67 or 12345
    matches = re.findall(r'\d[\d\s,\.]*\d|\d+', cleaned)

    if not matches:
        return None

    # Take the longest match (most likely the full price)
    price_str = max(matches, key=len)

    # Remove spaces (thousands separator in Russian format)
    price_str = price_str.replace(' ', '')

    # Handle comma as decimal separator (Russian format)
    # If there are both . and , — the last one is decimal
    if '.' in price_str and ',' in price_str:
        if price_str.rfind('.') > price_str.rfind(','):
            price_str = price_str.replace(',', '')
        else:
            price_str = price_str.replace('.', '').replace(',', '.')
    elif ',' in price_str:
        # Only comma — if it's at position -3, it's decimal; else thousands
        comma_pos = price_str.rfind(',')
        if len(price_str) - comma_pos - 1 == 2:
            # Decimal separator
            price_str = price_str.replace(',', '.')
        else:
            # Thousands separator
            price_str = price_str.replace(',', '')

    try:
        return float(price_str)
    except ValueError:
        logger.warning(f"Failed to convert '{price_str}' to float")
        return None


def parse_price_multi_selector(html: str, selectors: Dict[str, str]) -> float:
    """Parse price trying multiple CSS selectors in order

    Selectors are tried in this order:
    1. selectors['price'] (primary)
    2. selectors['price_alt'] (secondary)
    3. selectors['price_alt2'] (tertiary)

    Supports any HTML tag: <span>, <div>, <h3>, etc.

    Args:
        html: HTML content
        selectors: Dictionary with selector keys

    Returns:
        Parsed price as float

    Raises:
        PriceNotFoundError: If no selector matched or price couldn't be parsed
    """
    if not html:
        raise PriceNotFoundError("Empty HTML content")

    soup = BeautifulSoup(html, 'html.parser')

    # Try selectors in priority order
    selector_keys = ['price', 'price_alt', 'price_alt2']
    tried_selectors = []

    for key in selector_keys:
        selector = selectors.get(key)
        if not selector:
            continue

        tried_selectors.append(selector)
        logger.debug(f"Trying selector: {selector}")

        elements = soup.select(selector)

        for element in elements:
            # Try text content first
            text = element.get_text(strip=True)
            price = extract_price_from_text(text)

            if price and price > 0:
                logger.info(f"Found price {price} using selector '{selector}'")
                return price

            # Try data-price attribute
            data_price = element.get('data-price') or element.get('content')
            if data_price:
                price = extract_price_from_text(str(data_price))
                if price and price > 0:
                    logger.info(f"Found price {price} from attribute on '{selector}'")
                    return price

    raise PriceNotFoundError(
        f"Price not found. Tried selectors: {tried_selectors}"
    )


def parse_stock_status(html: str, selector: str) -> str:
    """Parse stock/availability status

    Args:
        html: HTML content
        selector: CSS selector for stock element

    Returns:
        Stock status text or "Unknown"
    """
    if not html or not selector:
        return "Unknown"

    try:
        soup = BeautifulSoup(html, 'html.parser')
        element = soup.select_one(selector)

        if not element:
            return "Unknown"

        return element.get_text(strip=True) or "Unknown"

    except Exception as e:
        logger.warning(f"Failed to parse stock with '{selector}': {e}")
        return "Unknown"


def parse_product_name(html: str, selector: str) -> str:
    """Parse product name

    Args:
        html: HTML content
        selector: CSS selector for product name

    Returns:
        Product name or empty string
    """
    if not html or not selector:
        return ""

    try:
        soup = BeautifulSoup(html, 'html.parser')
        element = soup.select_one(selector)

        if not element:
            return ""

        return element.get_text(strip=True)

    except Exception as e:
        logger.warning(f"Failed to parse product name with '{selector}': {e}")
        return ""


def scrape_real_product(monitor_config: Dict, scraper_config: Optional[Dict] = None) -> Dict:
    """Scrape product from real website

    Args:
        monitor_config: Monitor configuration dict with:
            - url: Product URL
            - selectors: CSS selectors dict (price, price_alt, price_alt2, stock, product_name)
            - headers: Custom HTTP headers (optional)
            - sku: Product SKU (optional)
        scraper_config: Scraper settings:
            - REQUEST_TIMEOUT: timeout in seconds
            - RETRY_COUNT: number of retries
            - RETRY_DELAY: delay between retries

    Returns:
        Dictionary with scraped data:
            {
                'url': str,
                'sku': str,
                'price': float,
                'stock': str,
                'name': str,
                'success': bool,
                'error': str | None,
                'error_type': str | None
            }
    """
    scraper_config = scraper_config or {}
    url = monitor_config.get('url', '')
    selectors = monitor_config.get('selectors', {})
    headers = monitor_config.get('headers')
    sku = monitor_config.get('sku', 'UNKNOWN')

    result = {
        'url': url,
        'sku': sku,
        'price': 0.0,
        'stock': '',
        'name': '',
        'success': False,
        'error': None,
        'error_type': None
    }

    if not url:
        result['error'] = "URL is empty"
        result['error_type'] = 'CONFIG_ERROR'
        return result

    try:
        # Fetch HTML
        html = fetch_real_url(
            url,
            headers=headers,
            timeout=scraper_config.get('REQUEST_TIMEOUT', 15),
            retries=scraper_config.get('RETRY_COUNT', 3),
            retry_delay=scraper_config.get('RETRY_DELAY', 5)
        )

        # Parse price (required, tries multiple selectors)
        result['price'] = parse_price_multi_selector(html, selectors)

        # Parse stock (optional)
        if 'stock' in selectors:
            result['stock'] = parse_stock_status(html, selectors['stock'])

        # Parse name (optional)
        if 'product_name' in selectors:
            result['name'] = parse_product_name(html, selectors['product_name'])

        result['success'] = True
        logger.info(f"Successfully scraped {url}: price={result['price']}")

    except CloudflareBlockedError as e:
        result['error'] = str(e)
        result['error_type'] = 'CLOUDFLARE_BLOCKED'
        logger.error(f"Cloudflare/anti-bot blocked {url}: {e}")

    except PriceNotFoundError as e:
        result['error'] = str(e)
        result['error_type'] = 'PRICE_NOT_FOUND'
        logger.error(f"Price not found on {url}: {e}")

    except ScraperError as e:
        result['error'] = str(e)
        result['error_type'] = 'SCRAPER_ERROR'
        logger.error(f"Scraper error for {url}: {e}")

    except Exception as e:
        result['error'] = f"Unexpected error: {e}"
        result['error_type'] = 'UNEXPECTED_ERROR'
        logger.exception(f"Unexpected error scraping {url}")

    return result


def scrape_all(monitors: List[Dict], scraper_config: Optional[Dict] = None) -> List[Dict]:
    """Scrape all monitors

    Args:
        monitors: List of monitor configurations
        scraper_config: Scraper settings

    Returns:
        List of scrape results
    """
    results = []

    for monitor in monitors:
        result = scrape_real_product(monitor, scraper_config)
        results.append(result)

    successful = sum(1 for r in results if r['success'])
    logger.info(f"Scraped {successful}/{len(results)} monitors successfully")

    return results
