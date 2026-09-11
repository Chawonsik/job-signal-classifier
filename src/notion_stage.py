import os

import requests

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

STAGING_DATABASE_ID = "49b40c8da0d3411ebf62921d84b58182"
TRACKER_DATABASE_ID = "851745f8848a4f8592bde6ca8aeb337e"
NOTION_API = "https://api.notion.com/v1/pages"
NOTION_VERSION = "2022-06-28"

# 원문은 판별용 참고 자료라 전체를 다 담을 필요는 없다. Notion 텍스트
# 블록 하나의 안전한 한도 안에서 앞부분만 저장한다.
MAX_TEXT_LEN = 1900


def _headers() -> dict:
    token = os.environ["NOTION_TOKEN"]
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def _query_all_links(database_id: str) -> set[str]:
    urls: set[str] = set()
    cursor = None
    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        resp = requests.post(
            f"https://api.notion.com/v1/databases/{database_id}/query",
            headers=_headers(),
            json=body,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        for page in data.get("results", []):
            link = page.get("properties", {}).get("링크", {}).get("url")
            if link:
                urls.add(link)
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    return urls


def get_existing_urls() -> set[str]:
    """판별대기 + 트래커 두 DB에 이미 있는 링크를 전부 모은다.

    GitHub Actions는 매번 새 컨테이너에서 시작해 로컬 상태가 없으니,
    "이미 아는 공고인지"는 노션 자체를 조회해서 판단하는 수밖에 없다.
    """
    return _query_all_links(STAGING_DATABASE_ID) | _query_all_links(TRACKER_DATABASE_ID)


def add_to_staging(
    site: str,
    company: str,
    title: str,
    url: str,
    career_tags: list[str],
    is_intern: bool,
    requirement_text: str,
) -> None:
    payload = {
        "parent": {"database_id": STAGING_DATABASE_ID},
        "properties": {
            "공고": {"title": [{"text": {"content": f"{company} · {title}"[:200]}}]},
            "회사": {"rich_text": [{"text": {"content": company[:200]}}]},
            "직무": {"rich_text": [{"text": {"content": title[:200]}}]},
            "사이트": {"select": {"name": site}},
            "연차": {"multi_select": [{"name": t} for t in career_tags]},
            "인턴": {"checkbox": is_intern},
            "링크": {"url": url},
            "원문": {"rich_text": [{"text": {"content": (requirement_text or "")[:MAX_TEXT_LEN]}}]},
        },
    }
    resp = requests.post(NOTION_API, headers=_headers(), json=payload, timeout=15)
    resp.raise_for_status()


if __name__ == "__main__":
    add_to_staging(
        site="사람인",
        company="테스트컴퍼니",
        title="테스트 그로스 마케터",
        url="https://example.com/job/notion-stage-test",
        career_tags=["신입", "1~3년"],
        is_intern=False,
        requirement_text="이건 notion_stage.py 동작 확인용 테스트 항목입니다.",
    )
    print("판별대기 DB에 테스트 항목 추가함")
