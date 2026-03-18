import re
import sys
from urllib.parse import urljoin, urlparse
import requests
import trafilatura
from bs4 import BeautifulSoup


def fetch_html_requests(url: str, timeout: int = 30) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )
    }
    r = requests.get(url, headers=headers, timeout=timeout)
    r.raise_for_status()
    return r.text


async def fetch_html_playwright(url: str, timeout_ms: int = 45000) -> str:
    # Lazy import so you don’t need Playwright unless you actually use it
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto(url, wait_until="networkidle", timeout=timeout_ms)

        # Optional: expand code blocks / open collapsibles if your docs use them
        # (left minimal on purpose)

        html = await page.content()
        await context.close()
        await browser.close()
        return html


def extract_main_text(html: str, url: str) -> dict:
    """
    Returns best-effort extraction without site-specific selectors.
    """
    downloaded = trafilatura.extract(
        html,
        url=url,
        include_comments=False,
        include_tables=False,
        include_images=False,
        favor_precision=True,
        output_format="json",
    )
    if not downloaded:
        return {"url": url, "ok": False, "reason": "trafilatura_extract_returned_none"}

    return {"url": url, "ok": True, "data": downloaded}


def looks_js_dependent(html: str) -> bool:
    """
    Heuristic: if there’s very little text, or it looks like an SPA shell.
    """
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)
    if len(text) < 400:
        return True

    # Common SPA indicators
    if soup.find(id="__next") or soup.find(id="app") or soup.find(id="root"):
        return True

    if re.search(r"enable javascript|javascript required|please turn on javascript", text, re.I):
        return True

    return False


def scrape_url(url: str) -> dict:
    html = fetch_html_requests(url)
    if looks_js_dependent(html):
        # fallback to Playwright render
        import asyncio

        html = asyncio.run(fetch_html_playwright(url))

    return extract_main_text(html, url)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scrape_docs.py <url>")
        sys.exit(2)

    url = sys.argv[1].strip()
    result = scrape_url(url)
    # Print JSON string (trafilatura already returns JSON for 'data')
    print("type: ",type(result))
    import json

    print(json.dumps(result, ensure_ascii=False, indent=2))