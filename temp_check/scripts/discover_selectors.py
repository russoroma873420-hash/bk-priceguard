"""Auto-discover product URL and price CSS selector for a category page.

Strategy:
  1. Open the category page via Playwright (real Chromium, antibot-safe).
  2. Grab the first link that looks like a product page.
  3. Open the product page.
  4. Run a DOM scan: find every element whose text matches a Russian
     price pattern (digits + space + ₽/руб) and short enough to be a price.
  5. Print top candidates with their CSS selectors.

Usage: python scripts/discover_selectors.py <category_url>
"""

import re
import sys

from playwright.sync_api import sync_playwright

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# JS injected into the page to enumerate price-like elements
DISCOVER_JS = r"""
() => {
    function buildSelector(el) {
        // Walk up to <body>, building a minimal stable selector
        const parts = [];
        while (el && el.nodeType === 1 && el !== document.body) {
            let part = el.tagName.toLowerCase();
            if (el.id) {
                part += '#' + el.id;
                parts.unshift(part);
                break;
            }
            const cls = (el.className && typeof el.className === 'string')
                ? el.className.trim().split(/\s+/).filter(Boolean)
                : [];
            if (cls.length) part += '.' + cls.slice(0, 3).join('.');
            parts.unshift(part);
            el = el.parentElement;
        }
        return parts.join(' > ');
    }
    const priceRe = /(?:^|\s)(\d[\d\s]{2,12}\d)\s*(?:₽|руб|р\.)/i;
    const seen = new Set();
    const out = [];
    document.querySelectorAll('span, div, p, h1, h2, h3, b, strong, ins').forEach(el => {
        // Only leaf-like elements
        if (el.children.length > 1) return;
        const text = (el.textContent || '').trim();
        if (text.length === 0 || text.length > 40) return;
        if (!priceRe.test(text)) return;
        const sel = buildSelector(el);
        if (seen.has(sel)) return;
        seen.add(sel);
        out.push({
            tag: el.tagName.toLowerCase(),
            cls: (el.className && typeof el.className === 'string') ? el.className : '',
            id: el.id || '',
            text: text,
            selector: sel,
        });
    });
    return out.slice(0, 15);
}
"""


def discover(category_url: str) -> None:
    print(f"\n{'=' * 70}\nDISCOVERING: {category_url}\n{'=' * 70}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, proxy=None)
        context = browser.new_context(
            user_agent=UA,
            viewport={"width": 1920, "height": 1080},
            locale="ru-RU",
            timezone_id="Europe/Moscow",
            ignore_https_errors=True,
            proxy=None,
        )
        page = context.new_page()

        # ---- Step 1: open category, find first product link ----
        try:
            page.goto(category_url, timeout=30000, wait_until="domcontentloaded")
        except Exception as e:
            print(f"[ERR] Cannot open category: {e}")
            browser.close()
            return

        page.wait_for_timeout(3000)
        category_html_size = len(page.content())
        print(f"[1] Category page loaded ({category_html_size} bytes)")

        # Common product-link heuristics
        product_url = page.evaluate(r"""
            () => {
                const patterns = [
                    'a[href*="/product/"]',
                    'a[href*="/products/"]',
                    'a[data-product-id]',
                    'a.product-card-top__link',
                    'a.catalog-product__name',
                    'a[href*="/product-detail/"]',
                ];
                for (const sel of patterns) {
                    const a = document.querySelector(sel);
                    if (a && a.href && !a.href.includes('#')) return a.href;
                }
                // Fallback: first <a> whose href contains 'product'
                for (const a of document.querySelectorAll('a[href]')) {
                    if (/\/products?\//.test(a.href)) return a.href;
                }
                return null;
            }
        """)

        if not product_url:
            print("[2] No product link found on category page — site might be blocked.")
            # Dump first 2000 chars to help debug
            snippet = page.content()[:2000]
            print("    First 2000 chars of page:")
            print("    " + snippet.replace("\n", "\n    ")[:2000])
            browser.close()
            return

        print(f"[2] Product URL discovered: {product_url}")

        # ---- Step 3: open product page ----
        try:
            page.goto(product_url, timeout=30000, wait_until="domcontentloaded")
        except Exception as e:
            print(f"[ERR] Cannot open product page: {e}")
            browser.close()
            return

        page.wait_for_timeout(3500)
        product_html_size = len(page.content())
        print(f"[3] Product page loaded ({product_html_size} bytes)")

        # ---- Step 4: discover price selectors ----
        candidates = page.evaluate(DISCOVER_JS)
        print(f"[4] Found {len(candidates)} price-like elements:\n")
        for i, c in enumerate(candidates, 1):
            print(f"  #{i}: <{c['tag']}>")
            print(f"      class    : {c['cls']!r}")
            print(f"      id       : {c['id']!r}")
            print(f"      text     : {c['text']!r}")
            print(f"      selector : {c['selector']}")
            print()

        browser.close()

        # ---- Step 5: dump product URL on its own line for easy copy-paste ----
        print(f"\nPRODUCT_URL={product_url}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/discover_selectors.py <category_url>")
        sys.exit(1)
    discover(sys.argv[1])
