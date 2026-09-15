"""원티드 전용 로컬 실행 스크립트.

GitHub Actions 러너 IP가 wanted.co.kr에 차단당해서, 원티드 수집만 이
컴퓨터(집 네트워크 IP)에서 launchd로 돌린다. 정해진 시각에 컴퓨터가
꺼져 있으면 그 시각엔 당연히 못 돈다 - 그래서 "하루에 한 번, 컴퓨터가
켜져 있을 때 아무 때나"로 바꿨다: launchd가 로그인/부팅 시점과 매시간
정각에 이 스크립트를 깨우고, 스크립트 자신이 "오늘 이미 돌았는지"를
마커 파일로 확인해서 중복 실행을 막는다.
"""

import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from main import collect_wanted, stage_postings  # noqa: E402
from notion_stage import get_existing_urls  # noqa: E402

STATE_FILE = Path(__file__).resolve().parent.parent / "data" / "wanted_local_last_run.txt"


def already_ran_today() -> bool:
    if not STATE_FILE.exists():
        return False
    return STATE_FILE.read_text().strip() == datetime.date.today().isoformat()


def mark_ran_today() -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(datetime.date.today().isoformat())


def main():
    today = datetime.date.today().isoformat()
    print(f"[{datetime.datetime.now().isoformat(timespec='seconds')}] 실행 체크")

    if already_ran_today():
        print(f"오늘({today}) 이미 실행함, 건너뜀")
        return

    known_urls = get_existing_urls()
    print(f"노션에 이미 있는 링크 {len(known_urls)}건 조회함")

    try:
        postings = collect_wanted(known_urls)
    except Exception as e:
        # 실패하면 마커를 남기지 않는다 - 다음 시간대 체크에서 다시 시도한다.
        print(f"[원티드 수집 실패] {type(e).__name__}: {e}")
        return

    print(f"원티드 신규 후보 {len(postings)}건 수집됨")
    staged = stage_postings(postings)
    print(f"판별대기 DB에 {staged}건 추가함")

    mark_ran_today()


if __name__ == "__main__":
    main()
