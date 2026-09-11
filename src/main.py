import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checks import check_posting  # noqa: E402
from collectors import careerly, saramin, wanted  # noqa: E402
from storage import get_conn, is_known_url, save_posting  # noqa: E402

PENDING_PATH = Path(__file__).resolve().parent.parent / "data" / "pending_classification.json"


def collect_saramin(conn):
    new_postings = []
    for keyword in saramin.SEARCH_KEYWORDS:
        for url in saramin.search_posting_urls(keyword):
            if is_known_url(conn, url):
                continue
            posting = saramin.fetch_posting(url)
            if save_posting(conn, posting):
                new_postings.append(posting)
    return new_postings


CAREERLY_MAX_FETCH_PER_RUN = 150


def collect_careerly(conn):
    """사이트맵 URL을 job ID 내림차순(최신 추정)으로 정렬해서, 모르는
    URL 중 앞에서부터 최대 CAREERLY_MAX_FETCH_PER_RUN개만 상세 조회한다.

    사이트맵에 3만 건 가까이 있는데 첫 실행에서 그걸 다 열어보면 몇
    시간이 걸리고 사이트에도 부담을 준다. 매일 조금씩 처리하면 며칠
    안에 다 따라잡고, 그 이후로는 정말 새로 생긴 것만 몇 건 처리하면
    되니까 이 정도 캡으로 충분하다.
    """
    all_urls = careerly.list_all_job_urls()
    unknown = [u for u in all_urls if not is_known_url(conn, u)]
    unknown.sort(key=lambda u: int(u.rstrip("/").rsplit("/", 1)[-1]), reverse=True)

    new_postings = []
    for url in unknown[:CAREERLY_MAX_FETCH_PER_RUN]:
        posting = careerly.fetch_posting(url)
        if save_posting(conn, posting):
            new_postings.append(posting)
    return new_postings


def collect_wanted(conn):
    new_postings = []
    for keyword in wanted.SEARCH_KEYWORDS:
        for job in wanted.search_position_ids(keyword):
            url = f"{wanted.BASE}/wd/{job['id']}"
            if is_known_url(conn, url):
                continue
            posting = wanted.fetch_posting(job)
            if save_posting(conn, posting):
                new_postings.append(posting)
    return new_postings


def main():
    conn = get_conn()
    new_postings = []
    new_postings += collect_saramin(conn)
    new_postings += collect_wanted(conn)
    new_postings += collect_careerly(conn)
    conn.close()

    print(f"신규 공고 {len(new_postings)}건 수집됨")

    pending = []
    for posting in new_postings:
        result = check_posting(posting)
        if not result.ok:
            print(f"  [점검 실패] {posting.url} - {', '.join(result.reasons)}")
            continue
        pending.append(
            {
                "site": posting.site,
                "company": posting.company,
                "title": posting.title,
                "url": posting.url,
                "career_tags": result.career_tags,
                "is_rolling": posting.is_rolling,
                "is_closed": posting.is_closed,
                "tags": posting.tags,
                "requirement_text": posting.requirement_text,
            }
        )

    PENDING_PATH.parent.mkdir(parents=True, exist_ok=True)
    PENDING_PATH.write_text(json.dumps(pending, ensure_ascii=False, indent=2))
    print(f"판별 대기 {len(pending)}건을 {PENDING_PATH}에 저장함")


if __name__ == "__main__":
    main()
