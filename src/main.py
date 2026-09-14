import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checks import check_posting  # noqa: E402
from collectors import careerly, saramin, wanted  # noqa: E402
from notion_stage import add_to_staging, get_existing_urls  # noqa: E402


def collect_saramin(known_urls: set[str]):
    postings = []
    for keyword in saramin.SEARCH_KEYWORDS:
        for url in saramin.search_posting_urls(keyword):
            if url in known_urls:
                continue
            postings.append(saramin.fetch_posting(url))
            known_urls.add(url)
    return postings


CAREERLY_MAX_FETCH_PER_RUN = 150


def collect_careerly(known_urls: set[str]):
    """사이트맵 URL을 job ID 내림차순(최신 추정)으로 정렬해서, 모르는
    URL 중 앞에서부터 최대 CAREERLY_MAX_FETCH_PER_RUN개만 상세 조회한다.

    사이트맵에 3만 건 가까이 있는데 첫 실행에서 그걸 다 열어보면 몇
    시간이 걸리고 사이트에도 부담을 준다. 매일 조금씩 처리하면 며칠
    안에 다 따라잡고, 그 이후로는 정말 새로 생긴 것만 몇 건 처리하면
    되니까 이 정도 캡으로 충분하다.
    """
    all_urls = careerly.list_all_job_urls()
    unknown = [u for u in all_urls if u not in known_urls]
    unknown.sort(key=lambda u: int(u.rstrip("/").rsplit("/", 1)[-1]), reverse=True)

    postings = []
    for url in unknown[:CAREERLY_MAX_FETCH_PER_RUN]:
        postings.append(careerly.fetch_posting(url))
        known_urls.add(url)
    return postings


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


def main():
    known_urls = get_existing_urls()
    print(f"노션에 이미 있는 링크 {len(known_urls)}건 조회함")

    new_postings = []
    for site_name, collect_fn in (
        ("사람인", collect_saramin),
        ("원티드", collect_wanted),
        ("커리어리", collect_careerly),
    ):
        try:
            new_postings += collect_fn(known_urls)
        except Exception as e:
            # 사이트 하나가 막히거나(예: IP 차단) 일시적으로 실패해도
            # 나머지 사이트에서 이미 모은 공고는 그대로 판별대기 DB에
            # 올려야 한다. 한 사이트 오류로 전체 배치를 날리지 않는다.
            print(f"  [{site_name} 수집 실패] {type(e).__name__}: {e}")
    print(f"신규 후보 {len(new_postings)}건 수집됨")

    staged = 0
    for posting in new_postings:
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

    print(f"판별대기 DB에 {staged}건 추가함")


if __name__ == "__main__":
    main()
