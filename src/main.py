import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checks import check_posting  # noqa: E402
from collectors import groupby, wanted  # noqa: E402
from notion_stage import add_to_staging, add_to_tracker, get_existing_urls  # noqa: E402


def collect_wanted(known_urls: set[str]):
    postings = []
    for keyword in wanted.SEARCH_KEYWORDS:
        for job in wanted.search_position_ids(keyword):
            url = f"{wanted.BASE}/wd/{job['id']}"
            if url in known_urls:
                continue
            postings.append(wanted.fetch_posting(job))
            known_urls.add(url)
    return postings


def stage_postings(postings: list) -> int:
    """점검을 통과한 공고를 판별대기 DB에 적재하고, 적재된 건수를 반환한다.

    판별대기를 거치는 사이트는 AI 판별 루틴이 원문을 직접 읽고 포함/제외를
    정한다.
    """
    staged = 0
    for posting in postings:
        result = check_posting(posting)
        if not result.ok:
            print(f"  [점검 실패] {posting.url} - {', '.join(result.reasons)}")
            continue
        # "인턴" 태그 여부만 보면 거의 안 잡힌다 (사람인은 해시태그에 인턴이
        # 잘 안 붙고, 커리어리는 tags 필드가 기술스택 용도로 쓰인다). 직무명에
        # "인턴"이 들어있는지를 기준으로 삼는 게 사이트 상관없이 더 정확하다.
        is_intern = bool(re.search(r"인턴", posting.title)) or "인턴" in posting.tags
        add_to_staging(
            site=posting.site,
            company=posting.company,
            title=posting.title,
            url=posting.url,
            career_tags=result.career_tags,
            is_intern=is_intern,
            requirement_text=posting.requirement_text,
        )
        staged += 1
    return staged


def collect_groupby(known_urls: set[str]):
    postings = []
    for slug in groupby.CATEGORY_SLUGS:
        for position in groupby.list_category_positions(slug):
            if not groupby.is_target_tags(position):
                continue
            url = f"{groupby.BASE}/positions/{position['id']}"
            if url in known_urls:
                continue
            postings.append(groupby.to_posting(position))
            known_urls.add(url)
    return postings


def track_groupby(postings: list) -> int:
    """그룹바이는 로그인 없이 원문을 못 읽어서 AI 판별을 거칠 수 없다.

    직무 태그로 이미 포함/제외가 끝난 상태로 들어오니, 판별대기를 건너뛰고
    트래커에 바로 적재한다. 그룹바이는 스타트업 전문 채용 플랫폼이라
    기업규모를 추측할 필요 없이 '스타트업'으로 확정할 수 있다.
    """
    tracked = 0
    for posting in postings:
        result = check_posting(posting)
        if not result.ok:
            print(f"  [점검 실패] {posting.url} - {', '.join(result.reasons)}")
            continue
        is_intern = bool(re.search(r"인턴", posting.title))
        add_to_tracker(
            site=posting.site,
            company=posting.company,
            title=posting.title,
            url=posting.url,
            career_tags=result.career_tags,
            is_intern=is_intern,
            company_size="스타트업",
        )
        tracked += 1
    return tracked


def main():
    known_urls = get_existing_urls()
    print(f"노션에 이미 있는 링크 {len(known_urls)}건 조회함")

    wanted_postings = []
    try:
        wanted_postings = collect_wanted(known_urls)
    except Exception as e:
        print(f"  [원티드 수집 실패] {type(e).__name__}: {e}")
    print(f"원티드 신규 후보 {len(wanted_postings)}건 수집됨")
    staged = stage_postings(wanted_postings)
    print(f"판별대기 DB에 {staged}건 추가함")

    groupby_postings = []
    try:
        groupby_postings = collect_groupby(known_urls)
    except Exception as e:
        print(f"  [그룹바이 수집 실패] {type(e).__name__}: {e}")
    print(f"그룹바이 태그 통과 {len(groupby_postings)}건 수집됨")
    tracked = track_groupby(groupby_postings)
    print(f"트래커 DB에 {tracked}건 바로 추가함")


if __name__ == "__main__":
    main()
