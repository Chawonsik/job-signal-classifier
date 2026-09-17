import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from browser import fetch_html  # noqa: E402
from models import Posting  # noqa: E402

BASE = "https://groupby.kr"

# robots.txt가 /api/를 명시적으로 막아뒀다. 카테고리 페이지(/jobs/<slug>)는
# 서버 렌더링이라 최초 10건은 requests만으로 그대로 읽히지만, 그 이상은
# 내부 API를 호출해야 해서 건드리지 않는다. 하루 10건×카테고리 수 한도로
# 운영한다. PM/사업개발 전용 카테고리 URL은 없어서, 실제로 관련 태그가
# 섞여 나오는 두 카테고리만 본다.
CATEGORY_SLUGS = ["marketing", "data-analyst"]

# 그룹바이 공고 하나에 포함 태그와 제외 태그가 동시에 붙는 경우가 흔하다
# (노출을 늘리려고 관련 태그를 넓게 붙이는 구조). 원문을 못 읽는 대신
# 태그로 판단해야 하니, 충돌하면 애매한 쪽이 아니라 제외 쪽으로 둔다.
INCLUDE_TAGS = {"그로스 마케터", "퍼포먼스 마케터", "CRM 마케터", "사업 개발", "서비스 기획자", "데이터 분석가", "PM/PO"}
EXCLUDE_TAGS = {"인플루언서 마케터", "바이럴 마케터", "CX/CS", "데이터 엔지니어", "B2B 영업", "B2C 영업", "영업 지원"}


def _extract_next_data(html: str) -> dict:
    import json

    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        return {}
    return json.loads(m.group(1))


def list_category_positions(slug: str) -> list[dict]:
    """카테고리 페이지 최초 로드에 서버가 같이 내려주는 공고 목록(최대 10건)을 그대로 읽는다."""
    html = fetch_html(f"{BASE}/jobs/{slug}")
    data = _extract_next_data(html)
    return data.get("props", {}).get("pageProps", {}).get("positions", []) or []


def is_target_tags(position: dict) -> bool:
    names = {t.get("name") for t in position.get("positionTypes", [])}
    return bool(names & INCLUDE_TAGS) and not bool(names & EXCLUDE_TAGS)


def _career_text(position: dict) -> str:
    career_type = position.get("careerType")
    exp = position.get("experienceRange") or {}
    if career_type == "무관":
        return "경력무관"
    lo, hi = exp.get("min"), exp.get("max")
    if lo is not None and hi is not None:
        return f"경력 {lo}~{hi}년"
    return "경력"


def to_posting(position: dict) -> Posting:
    startup = position.get("startup") or {}
    tags = [t.get("name") for t in position.get("positionTypes", []) if t.get("name")]
    return Posting(
        site="그룹바이",
        company=startup.get("name", ""),
        title=position.get("name", ""),
        url=f"{BASE}/positions/{position['id']}",
        career_text=_career_text(position),
        is_rolling=False,
        tags=tags,
        # 로그인 없이는 원문을 못 읽어서 비워둔다. 판별은 이미 태그로
        # 끝났으니 판별대기 DB로 보내는 게 아니라 트래커로 바로 간다.
        requirement_text="",
    )


if __name__ == "__main__":
    # 완료 기준 확인용: 카테고리별 후보 -> 태그 필터 -> Posting 변환까지 한 번에
    for slug in CATEGORY_SLUGS:
        positions = list_category_positions(slug)
        targets = [p for p in positions if is_target_tags(p)]
        print(f"[{slug}] 전체 {len(positions)}건 중 태그 통과 {len(targets)}건")
        for p in targets:
            posting = to_posting(p)
            print(" -", posting.company, "|", posting.title, "|", posting.career_text, "|", posting.url)
