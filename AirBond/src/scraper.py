"""Web scraper module for fetching and parsing product prices and stock"""

import logging
from typing import Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Mock data for testing (when real sites are blocked)
MOCK_DATA = {
    'https://example.com/ac-model-001': {
        'html': '''
            <html>
                <body>
                    <h1 class="product-title">AC Model 001</h1>
                    <span class="price">5500</span>
                    <div class="stock">In Stock</div>
                </body>
            </html>
        ''',
        'price': 5500.0
    },
    'https://example.com/ac-model-002': {
        'html': '''
            <html>
                <body>
                    <h1 class="product-title">AC Model 002</h1>
                    <span class="price">7800</span>
                    <div class="stock">Available</div>
                </body>
            </html>
        ''',
        'price': 7800.0
    },
    'https://shop.example.com/ac-003': {
        'html': '''
            <html>
                <body>
                    <h1 class="item-name">AC Model 003</h1>
                    <p class="item-price">9200</p>
                    <span class="item-code">MODEL_003</span>
                </body>
            </html>
        ''',
        'price': 9200.0
    },
}


def fetch_url(url: str, timeout: int = 10, use_mock: bool = True) -> Optional[str]:
    """Fetch HTML content from URL

    Args:
        url: URL to fetch
        timeout: Request timeout in seconds
        use_mock: Use mock data if real request fails

    Returns:
        HTML content as string or None if failed
    """
    try:
        logger.info(f"Fetching {url}...")
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        logger.debug(f"Successfully fetched {url} (status: {response.status_code})")
        return response.text

    except requests.exceptions.Timeout:
        logger.warning(f"Timeout fetching {url}")
    except requests.exceptions.ConnectionError:
        logger.warning(f"Connection error for {url}")
    except requests.exceptions.HTTPError as e:
        logger.warning(f"HTTP error {e.response.status_code} for {url}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error for {url}: {e}")

    # Try to use mock data if real request failed
    if use_mock and url in MOCK_DATA:
        logger.info(f"Using mock data for {url}")
        return MOCK_DATA[url]['html']

    return None


def parse_price(html: str, css_selector_price: str) -> float:
    """Parse price from HTML using CSS selector

    Args:
        html: HTML content
        css_selector_price: CSS selector for price element

    Returns:
        Price as float or 0.0 if parsing failed
    """
    try:
        if not html:
            logger.warning("HTML content is empty")
            return 0.0

        soup = BeautifulSoup(html, 'html.parser')
        price_element = soup.select_one(css_selector_price)

        if not price_element:
            logger.warning(f"Price element not found with selector: {css_selector_price}")
            return 0.0

        price_text = price_element.get_text(strip=True)

        # Remove common currency symbols and spaces
        cleaned_price = price_text.replace('$', '').replace('₽', '').replace(',', '.').strip()

        # Extract numeric value
        price_value = float(''.join(c for c in cleaned_price if c.isdigit() or c == '.'))
        logger.debug(f"Parsed price: {price_value} from '{price_text}'")
        return price_value

    except (ValueError, AttributeError) as e:
        logger.error(f"Failed to parse price: {e}")
        return 0.0
    except Exception as e:
        logger.error(f"Unexpected error parsing price: {e}")
        return 0.0


def parse_stock(html: str, css_selector_stock: str) -> str:
    """Parse stock/availability status from HTML

    Args:
        html: HTML content
        css_selector_stock: CSS selector for stock element

    Returns:
        Stock status text or empty string if not found
    """
    try:
        if not html:
            logger.warning("HTML content is empty")
            return ""

        soup = BeautifulSoup(html, 'html.parser')
        stock_element = soup.select_one(css_selector_stock)

        if not stock_element:
            logger.debug(f"Stock element not found with selector: {css_selector_stock}")
            return ""

        stock_text = stock_element.get_text(strip=True)
        logger.debug(f"Parsed stock status: {stock_text}")
        return stock_text

    except Exception as e:
        logger.error(f"Failed to parse stock status: {e}")
        return ""


def parse_product_name(html: str, css_selector_name: str) -> str:
    """Parse product name from HTML

    Args:
        html: HTML content
        css_selector_name: CSS selector for product name element

    Returns:
        Product name or empty string if not found
    """
    try:
        if not html:
            return ""

        soup = BeautifulSoup(html, 'html.parser')
        name_element = soup.select_one(css_selector_name)

        if not name_element:
            logger.debug(f"Product name element not found with selector: {css_selector_name}")
            return ""

        name_text = name_element.get_text(strip=True)
        logger.debug(f"Parsed product name: {name_text}")
        return name_text

    except Exception as e:
        logger.error(f"Failed to parse product name: {e}")
        return ""


def scrape_product(url: str, selectors: dict, use_mock: bool = True) -> dict:
    """Scrape complete product information from URL

    Args:
        url: URL to scrape
        selectors: Dictionary with CSS selectors:
            - price: CSS selector for price
            - stock: CSS selector for stock status
            - name: CSS selector for product name (optional)
        use_mock: Use mock data if real request fails

    Returns:
        Dictionary with scraped data:
            {
                'url': url,
                'price': float,
                'stock': str,
                'name': str,
                'success': bool
            }
    """
    html = fetch_url(url, use_mock=use_mock)

    if not html:
        logger.error(f"Failed to fetch {url}")
        return {
            'url': url,
            'price': 0.0,
            'stock': '',
            'name': '',
            'success': False
        }

    # Parse price (required)
    price = parse_price(html, selectors.get('price', 'span.price'))

    # Parse stock (optional)
    stock = parse_stock(html, selectors.get('stock', 'div.stock')) if 'stock' in selectors else ''

    # Parse product name (optional)
    name = parse_product_name(html, selectors.get('name', 'h1.product-name')) if 'name' in selectors else ''

    success = price > 0

    result = {
        'url': url,
        'price': price,
        'stock': stock,
        'name': name,
        'success': success
    }

    logger.info(f"Scraped {url}: price={price}, stock={stock}, success={success}")
    return result
