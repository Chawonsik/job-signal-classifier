import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from browser import fetch_html  # noqa: E402
from models import Posting  # noqa: E402

BASE = "https://www.saramin.co.kr"

# 검색용 키워드. 최종 포함/제외 판단은 classify.py가 JD를 읽고 하며,
# 여기서는 후보를 넓게 모으는 용도로만 쓴다.
SEARCH_KEYWORDS = [
    "그로스 마케터",
    "퍼포먼스 마케터",
    "CRM 마케터",
    "사업개발",
    "데이터 분석가",
    "PM",
    "PO",
]


def search_posting_urls(keyword: str) -> list[str]:
    """검색 결과에서 공고 rec_idx를 뽑아 항상 같은 형태(view_type=list)의
    URL로 정규화한다. 검색 결과가 그대로 주는 relay URL(view_type=etc,
    searchType=search...)은 요청할 때마다 다른 트래킹 파라미터가 붙어서
    같은 공고를 매번 다른 URL로 착각하게 만들고, 상세 내용 대신 껍데기
    페이지만 돌려주는 경우가 있었다.
    """
    url = f"{BASE}/zf_user/search/recruit?searchword={keyword}"
    html = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")
    rec_idxs = set()
    for a in soup.select("a[href*='/zf_user/jobs/relay/view']"):
        href = a.get("href") or ""
        m = re.search(r"rec_idx=(\d+)", href)
        if m:
            rec_idxs.add(m.group(1))
    return [
        f"{BASE}/zf_user/jobs/relay/view?rec_idx={rid}&view_type=list"
        for rid in sorted(rec_idxs)
    ]


def _parse_meta_description(html: str) -> dict:
    """<meta name="description">가 "회사, 직무, 경력:X, 학력:X, 급여,
    마감일:X, 홈페이지:X" 형태로 항상 안정적으로 들어있다.

    본문(body)은 사람인이 가끔 네비게이션 껍데기만 내려주는 경우가 있어서
    (JS 렌더링에 의존하는 것으로 보임), 거기서 정규식으로 경력을 뽑으면
    엉뚱하게 메뉴에 있는 "신입·인턴" 같은 글자를 진짜 요건으로 착각하는
    사고가 났다. 메타 태그는 body 렌더링 상태와 무관하게 항상 채워져
    있어서 회사명/직무명/경력/마감일은 이쪽을 신뢰한다.
    """
    m = re.search(r'<meta name="description" content="([^"]+)"', html)
    if not m:
        return {}
    parts = [p.strip() for p in m.group(1).split(",")]
    result = {}
    if len(parts) >= 2:
        result["company"] = parts[0]
        result["title"] = parts[1]
    for part in parts[2:]:
        if ":" in part:
            key, _, value = part.partition(":")
            result[key.strip()] = value.strip()
    return result


def _extract_deadline(career_field_deadline: str) -> tuple[str | None, bool]:
    """메타 설명의 마감일 값에서 (YYYY-MM-DD, 상시채용여부)를 뽑는다."""
    if not career_field_deadline or "상시" in career_field_deadline:
        return None, True
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", career_field_deadline)
    if m:
        return career_field_deadline[:10], False
    return None, False


def fetch_posting(url: str) -> Posting:
    html = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)

    meta = _parse_meta_description(html)

    # 메타 설명이 없으면(사실상 거의 없음) <title> "[회사명] 제목 - 사람인"으로 대체
    if meta.get("company") and meta.get("title"):
        company, title = meta["company"], meta["title"]
    else:
        title_full = soup.title.string if soup.title else ""
        m = re.match(r"\[(?P<company>[^\]]+)\]\s*(?P<title>.+?)\s*-\s*사람인\s*$", title_full or "")
        company = m.group("company").strip() if m else ""
        title = m.group("title").strip() if m else (title_full or "").strip()
        title = re.sub(r"\(D-?\d*\)\s*$", "", title).strip()
        title = re.sub(r"\(\)\s*$", "", title).strip()

    is_closed = "본 채용정보는 마감되었습니다" in text or "접수마감" in text
    deadline, is_rolling = _extract_deadline(meta.get("마감일", ""))

    # 메타의 "경력" 값은 "경력:경력 5년 이상"처럼 "경력:" 다음에 온다.
    career_text = meta.get("경력", "")

    tag_section = ""
    if "관련 태그" in text:
        tag_section = text.split("관련 태그", 1)[1][:2000]
    tags = re.findall(r"#([\w가-힣()·/]+)", tag_section)

    return Posting(
        site="사람인",
        company=company,
        title=title,
        url=url,
        career_text=career_text,
        deadline=deadline,
        is_rolling=is_rolling,
        is_closed=is_closed,
        tags=tags,
        requirement_text=text[:5000],
    )


if __name__ == "__main__":
    # 완료 기준 확인용: 검색 -> 후보 URL -> 상세 파싱까지 한 번에 실행
    urls = search_posting_urls("그로스 마케터")
    print(f"검색된 후보 URL: {len(urls)}건")
    for u in urls[:3]:
        print(" -", u)
    if urls:
        posting = fetch_posting(urls[0])
        print(posting)
