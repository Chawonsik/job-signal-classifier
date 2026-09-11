from dataclasses import dataclass

from career_parser import parse_career
from models import Posting


@dataclass
class CheckResult:
    posting: Posting
    ok: bool
    career_tags: list[str]
    reasons: list[str]


def check_posting(posting: Posting) -> CheckResult:
    reasons = []

    if not posting.company:
        reasons.append("회사명 없음")
    if not posting.title:
        reasons.append("직무명 없음")
    if not posting.url:
        reasons.append("링크 없음")

    career_tags = parse_career(posting.career_text or posting.requirement_text)
    if career_tags == ["확인필요"]:
        reasons.append("연차 파싱 불확실")

    # 필수 필드가 빠지면 실패, 연차만 불확실하면 "확인필요"로 통과시키되 기록해둔다.
    ok = not any(r in ("회사명 없음", "직무명 없음", "링크 없음") for r in reasons)
    return CheckResult(posting=posting, ok=ok, career_tags=career_tags, reasons=reasons)


def run_checks(postings: list[Posting]) -> list[CheckResult]:
    results = [check_posting(p) for p in postings]

    failed = sum(1 for r in results if not r.ok)
    needs_review = sum(1 for r in results if r.ok and r.reasons)
    passed_clean = len(results) - failed - needs_review

    print(
        f"점검 결과: 총 {len(results)}건 / 정상 {passed_clean}건 / "
        f"확인필요 {needs_review}건 / 실패(필수필드 누락) {failed}건"
    )
    for r in results:
        if not r.ok:
            print(f"  [실패] {r.posting.url} - {', '.join(r.reasons)}")

    return results


if __name__ == "__main__":
    samples = [
        Posting(site="사람인", company="해피테일즈", title="퍼포먼스 마케터", url="https://x/1",
                 career_text="경력무관(신입포함)"),
        Posting(site="사람인", company="프랭크스토어", title="그로스 마케터", url="https://x/2",
                 career_text="경력 2~10년"),
        Posting(site="", company="", title="", url=""),
    ]
    run_checks(samples)
