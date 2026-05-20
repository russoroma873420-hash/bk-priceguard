"""One-shot: load a DNS-Shop product URL and find every element
that contains a given exact price. Prints stable CSS selectors.

Usage:
    python scripts/find_dns_selector.py <url> <price_text>
"""

import sys

from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# JS: find every leaf element whose textContent contains the price (any spacing)
# and return its tag + class + id + a minimal CSS selector path.
FIND_JS = r"""
(priceVariants) => {
    function sel(el) {
        const parts = [];
        while (el && el.nodeType === 1 && el !== document.body) {
            let p = el.tagName.toLowerCase();
            if (el.id) { p += '#' + el.id; parts.unshift(p); break; }
            const cls = (el.className && typeof el.className === 'string')
                ? el.className.trim().split(/\s+/).filter(Boolean) : [];
            if (cls.length) p += '.' + cls.slice(0, 3).join('.');
            parts.unshift(p);
            el = el.parentElement;
        }
        return parts.join(' > ');
    }
    const seen = new Set();
    const out = [];
    document.querySelectorAll('*').forEach(el => {
        if (el.children.length > 0) return;          // leaf only
        const text = (el.textContent || '').trim();
        if (!text || text.length > 100) return;
        for (const v of priceVariants) {
            if (text.includes(v)) {
                const s = sel(el);
                if (seen.has(s)) return;
                seen.add(s);
                out.push({
                    tag: el.tagName.toLowerCase(),
                    cls: (el.className && typeof el.className === 'string') ? el.className : '',
                    id: el.id || '',
                    text: text,
                    selector: s,
                });
                return;
            }
        }
    });
    return out;
}
"""


def main(url: str, price: str) -> None:
    variants = [price, price.replace(" ", ""), price.replace(" ", " ")]
    print(f"URL    : {url}")
    print(f"PRICE  : {price!r}  variants={variants}\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, proxy=None)
        ctx = browser.new_context(
            user_agent=UA,
            viewport={"width": 1920, "height": 1080},
            locale="ru-RU",
            timezone_id="Europe/Moscow",
            ignore_https_errors=True,
            proxy=None,
        )
        page = ctx.new_page()
        try:
            page.goto(url, timeout=40000, wait_until="domcontentloaded")
        except Exception as e:
            print(f"[ERR] goto failed: {e}")
            browser.close()
            return

        page.wait_for_timeout(5000)  # let JS finish

        html_size = len(page.content())
        title = page.title()
        print(f"[1] Page loaded: {html_size} bytes, title='{title}'")

        # Detect known block pages
        body_text = page.evaluate("() => document.body ? document.body.innerText.slice(0, 400) : ''")
        print(f"[2] body preview: {body_text!r}\n")

        hits = page.evaluate(FIND_JS, variants)
        print(f"[3] Elements containing price: {len(hits)}\n")
        for i, h in enumerate(hits, 1):
            print(f"  #{i}: <{h['tag']}>")
            print(f"      text     : {h['text']!r}")
            print(f"      class    : {h['cls']!r}")
            print(f"      id       : {h['id']!r}")
            print(f"      selector : {h['selector']}")
            print()

        browser.close()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scripts/find_dns_selector.py <url> <price_text>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
