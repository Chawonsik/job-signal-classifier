import time

import requests
from playwright.sync_api import sync_playwright

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


def fetch_html(url: str, timeout: int = 15) -> str:
    """단순 HTTP GET. 서버사이드 렌더링되는 사이트(예: 사람인)에 사용.

    사람인은 오히려 헤드리스 브라우저(Playwright)를 봇으로 감지해 응답이
    걸리는 반면, 일반 User-Agent를 붙인 단순 requests는 정상 응답한다.
    """
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def fetch_rendered_html(url: str, wait_seconds: float = 2.0) -> str:
    """Render a URL with a real browser and return the resulting HTML.

    Used instead of plain requests because some target sites (e.g. 로켓펀치)
    block non-browser HTTP clients at the Cloudflare layer even though their
    robots.txt permits crawling.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=USER_AGENT)
        page.goto(url, timeout=30000, wait_until="domcontentloaded")
        time.sleep(wait_seconds)
        html = page.content()
        browser.close()
        return html
