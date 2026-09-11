import sqlite3
from pathlib import Path

from models import Posting

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "local.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS postings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site TEXT NOT NULL,
    company TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    career_text TEXT,
    deadline TEXT,
    is_rolling INTEGER,
    is_closed INTEGER,
    tags TEXT,
    requirement_text TEXT,
    notion_synced INTEGER DEFAULT 0,
    first_seen_at TEXT DEFAULT (datetime('now'))
);
"""


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(SCHEMA)
    return conn


def is_known_url(conn: sqlite3.Connection, url: str) -> bool:
    """URL 하나가 이미 저장돼 있는지만 가볍게 확인한다.

    커리어리처럼 후보 URL이 수만 건인 사이트에서, 이미 아는 공고까지
    전부 상세 페이지를 열어보면 시간이 너무 오래 걸리고 사이트에도
    부담을 준다. 그래서 상세 조회 전에 이 함수로 먼저 걸러낸다.
    """
    cur = conn.execute("SELECT 1 FROM postings WHERE url = ?", (url,))
    return cur.fetchone() is not None


def save_posting(conn: sqlite3.Connection, posting: Posting) -> bool:
    """새 공고면 저장하고 True, 이미 본 공고면 False.

    URL만으로는 부족하다 — 사람인 등에서 같은 공고가 재노출되며 URL의
    트래킹 파라미터가 바뀌는 사례가 있어서, (사이트+회사명+직무명)이
    이미 있으면 "재게시"로 보고 URL만 갱신하고 신규로 세지 않는다.
    """
    cur = conn.cursor()

    cur.execute("SELECT id FROM postings WHERE url = ?", (posting.url,))
    if cur.fetchone():
        return False

    cur.execute(
        "SELECT id FROM postings WHERE site = ? AND company = ? AND title = ?",
        (posting.site, posting.company, posting.title),
    )
    existing = cur.fetchone()
    if existing:
        cur.execute(
            """UPDATE postings SET url = ?, deadline = ?, is_rolling = ?, is_closed = ?
               WHERE id = ?""",
            (posting.url, posting.deadline, int(posting.is_rolling), int(posting.is_closed), existing[0]),
        )
        conn.commit()
        return False

    cur.execute(
        """INSERT INTO postings
           (site, company, title, url, career_text, deadline, is_rolling, is_closed, tags, requirement_text)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            posting.site,
            posting.company,
            posting.title,
            posting.url,
            posting.career_text,
            posting.deadline,
            int(posting.is_rolling),
            int(posting.is_closed),
            ",".join(posting.tags),
            posting.requirement_text,
        ),
    )
    conn.commit()
    return True


if __name__ == "__main__":
    # 완료 기준 확인용: 같은 공고를 두 번 저장해도 안 깨지는지 확인
    import os

    if DB_PATH.exists():
        os.remove(DB_PATH)

    sample = Posting(
        site="사람인",
        company="테스트컴퍼니",
        title="테스트 그로스 마케터",
        url="https://example.com/job/1",
    )
    conn = get_conn()
    print("1차 저장 (신규여야 함):", save_posting(conn, sample))
    print("2차 저장, 같은 URL (신규 아니어야 함):", save_posting(conn, sample))

    republished = Posting(
        site="사람인",
        company="테스트컴퍼니",
        title="테스트 그로스 마케터",
        url="https://example.com/job/1-republished",
    )
    print("3차 저장, URL만 다름 (재게시, 신규 아니어야 함):", save_posting(conn, republished))

    cur = conn.execute("SELECT COUNT(*) FROM postings")
    print("총 row 수 (1이어야 함):", cur.fetchone()[0])
    conn.close()
