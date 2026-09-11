import requests

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


def fetch_html(url: str, timeout: int = 15) -> str:
    """단순 HTTP GET. 사람인·커리어리·원티드 모두 이걸로 충분하다.

    로켓펀치처럼 Cloudflare가 비브라우저 클라이언트를 막는 사이트도 있었지만
    (헤드리스 브라우저로 우회 시도했던 fetch_rendered_html은 이제 안 씀),
    그 사이트 자체를 스코프에서 제외해서 더 이상 필요 없어졌다.
    """
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
    resp.raise_for_status()
    return resp.text
