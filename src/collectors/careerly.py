import re
import sys
from pathlib import Path
from xml.etree import ElementTree

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from browser import fetch_html  # noqa: E402
from models import Posting  # noqa: E402

BASE = "https://careerly.co.kr"
SITEMAP_URL = f"{BASE}/sitemap/job/0.xml"
NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def list_all_job_urls() -> list[str]:
    """공고 사이트맵의 URL을 전부 반환한다.

    처음엔 lastmod로 "최근 N일"만 거르려 했는데, 실제로 확인해보니
    lastmod가 사이트 전체 재색인 시점(하루)에 일괄로 찍혀 있어서
    28,867건 중 25,925건이 같은 날짜였다 — 진짜 신규 여부를 알려주는
    신호가 아니었다. 그래서 여기서는 후보를 넓게 반환하고, "이미 본
    공고인지"는 다음 단계(storage.py, URL 기준 조회)에서 가볍게
    걸러낸다. 사이트맵 자체는 페이지를 하나씩 열어보는 것보다 훨씬
    가벼워서, 매번 전체를 받아도 문제 없다.
    """
    xml_text = fetch_html(SITEMAP_URL, timeout=30)
    root = ElementTree.fromstring(xml_text)
    return [
        url_el.findtext("sm:loc", default="", namespaces=NS)
        for url_el in root.findall("sm:url", NS)
    ]


def _extract_career_bracket(title: str) -> str:
    m = re.search(r"\[([^\]]+)\]", title)
    return m.group(1) if m else ""


def fetch_posting(url: str) -> Posting:
    html = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)

    # <title> 형태: "{직무명} - {회사명} 채용 | 커리어리"
    title_full = soup.title.string if soup.title else ""
    m = re.match(r"(?P<title>.+?)\s*-\s*(?P<company>.+?)\s*채용\s*\|\s*커리어리\s*$", title_full or "")
    title = m.group("title").strip() if m else (title_full or "").strip()
    company = m.group("company").strip() if m else ""

    career_text = _extract_career_bracket(title)

    req_m = re.search(r"자격\s*요건(.+?)(?:우대|기술\s*스택|AI\s*점수|$)", text)
    requirement_text = req_m.group(1).strip()[:2000] if req_m else text[:2000]

    tags_m = re.search(r"기술\s*스택(.+?)AI\s*점수", text)
    tags = tags_m.group(1).split() if tags_m else []

    return Posting(
        site="커리어리",
        company=company,
        title=title,
        url=url,
        career_text=career_text,
        tags=tags,
        requirement_text=requirement_text,
    )


if __name__ == "__main__":
    # 완료 기준 확인용: 사이트맵 전체 -> 상세 파싱까지 한 번에 실행
    urls = list_all_job_urls()
    print(f"사이트맵 전체 공고: {len(urls)}건")
    for u in urls[:3]:
        print(" -", u)
    if urls:
        print(fetch_posting(urls[0]))
