"""Utility implementations for web search and browsing."""

import os

import httpx


def _require_key(env_var: str) -> str:
    val = os.environ.get(env_var, "")
    if not val:
        raise RuntimeError(
            f"API key is not configured ({env_var}). Set this variable in config/.env; "
            "see setup/api_guide.md."
        )
    return val


async def search(query: str, count: int = 5) -> dict:
    """Search the web with Brave Search and return summaries of the top N results."""
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": _require_key("SEARCH_API_KEY"),
    }
    params = {"q": query, "count": count, "search_lang": "zh-hans"}

    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers=headers,
            params=params,
        )
        r.raise_for_status()
        data = r.json()

    results = []
    for item in data.get("web", {}).get("results", [])[:count]:
        results.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "description": item.get("description", ""),
        })

    return {"query": query, "results": results}


_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

_EXTRACT_JS = """() => {
    const selectors = [
        'article', 'main', '[class*=detail]', '[class*=Detail]',
        '[class*=content]', '[class*=Content]', '.content', '#content', 'body'
    ];
    let best = '';
    for (const sel of selectors) {
        for (const el of document.querySelectorAll(sel)) {
            const text = el.innerText || '';
            if (text.length > best.length) best = text;
        }
    }
    return best || document.body.innerText;
}"""

# Content below this threshold is treated as an empty shell (navigation/loading UI) and retried.
_MIN_CONTENT_LEN = 200


async def browse(url: str, max_chars: int = 6000) -> dict:
    """Load a page in headless Playwright and extract its body as Markdown.

    Many job and e-commerce detail pages are SPAs whose data has not arrived when
    DOM parsing completes. Wait for network idle rather than extracting immediately
    at domcontentloaded. If content remains too short, indicating only navigation or
    a loading shell, scroll and retry with backoff instead of returning the shell.
    """
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(user_agent=_UA)
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            try:
                # SPA data often arrives afterward. Long-polling or heartbeat requests
                # may prevent networkidle forever, so ignore the timeout and continue.
                await page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass

            content = (await page.evaluate(_EXTRACT_JS)).strip()

            attempt = 0
            while len(content) < _MIN_CONTENT_LEN and attempt < 4:
                attempt += 1
                await page.mouse.wheel(0, 2000)
                await page.wait_for_timeout(1500 * attempt)
                content = (await page.evaluate(_EXTRACT_JS)).strip()
        finally:
            await browser.close()

    truncated = len(content) > max_chars
    content = content[:max_chars]
    return {
        "url": url,
        "content": content,
        "truncated": truncated,
        "warning": (
            "Page content remained too short. A login wall, anti-bot protection, or "
            "longer loading time may be responsible, and the extraction may be incomplete."
            if len(content) < _MIN_CONTENT_LEN else None
        ),
    }
