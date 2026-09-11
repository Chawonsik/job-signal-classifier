import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from browser import USER_AGENT, fetch_html  # noqa: E402
from models import Posting  # noqa: E402

BASE = "https://www.wanted.co.kr"
SEARCH_API = f"{BASE}/api/chaos/search/v1/position"

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


def search_position_ids(keyword: str, limit: int = 20) -> list[dict]:
    """원티드 검색 페이지가 내부적으로 쓰는 공개 검색 API를 그대로 호출한다.

    이 API는 원티드 자체 웹사이트가 브라우저에서 호출하는 것과 동일한
    엔드포인트로, 공식 OpenAPI(사업자등록번호 필요)와는 별개다. 응답에
    annual_from/annual_to(연차 범위)가 이미 구조화돼 있어서, 정규식으로
    연차를 추측해야 하는 다른 사이트보다 오히려 더 정확하게 뽑을 수 있다.
    """
    params = {
        "query": keyword,
        "country": "kr",
        "years": "-1",
        "locations": "all",
        "sort": "job.recommend_order",
        "limit": limit,
        "offset": 0,
    }
    resp = requests.get(SEARCH_API, params=params, headers={"User-Agent": USER_AGENT}, timeout=15)
    resp.raise_for_status()
    return resp.json().get("data", [])


def fetch_posting(job: dict) -> Posting:
    """검색 API가 준 job dict(하나의 포지션)를 상세 페이지와 합쳐 Posting으로 만든다."""
    job_id = job["id"]
    url = f"{BASE}/wd/{job_id}"
    html = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)

    annual_from = job.get("annual_from")
    annual_to = job.get("annual_to")
    if annual_from == 0:
        career_text = "신입"
    elif annual_from is not None and annual_to is not None:
        career_text = f"경력 {annual_from}~{annual_to}년"
    else:
        career_text = ""

    is_intern = bool(re.search(r"\[인턴\]|인턴", job.get("position", "")))
    is_rolling = "상시채용" in text

    return Posting(
        site="원티드",
        company=job.get("company", {}).get("name", ""),
        title=job.get("position", ""),
        url=url,
        career_text=career_text,
        is_rolling=is_rolling,
        tags=["인턴"] if is_intern else [],
        requirement_text=text[:5000],
    )


if __name__ == "__main__":
    # 완료 기준 확인용: 검색 -> 후보 -> 상세 파싱까지 한 번에 실행
    jobs = search_position_ids("그로스 마케터", limit=5)
    print(f"검색된 후보: {len(jobs)}건")
    for j in jobs[:3]:
        print(" -", j["id"], j.get("company", {}).get("name"), j.get("position"))
    if jobs:
        print(fetch_posting(jobs[0]))
