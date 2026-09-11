import re

# (태그, 하한, 상한) — 상한 None은 "그 이상 전부"를 뜻함
BUCKETS = [
    ("1~3년", 1, 3),
    ("3~5년", 3, 5),
    ("5년+", 5, None),
]


def parse_career(text: str) -> list[str]:
    """자격요건 텍스트에서 연차 태그를 뽑는다.

    "2~10년"처럼 범위가 넓으면 겹치는 구간을 전부 태깅한다(A-3에서 정한
    멀티 선택 원칙). 숫자를 전혀 못 뽑으면 "확인필요"만 붙이고, 숫자
    없이 "경력"이라는 단어만 있으면 "경력"+"확인필요"를 함께 붙인다.
    경계값(예: 정확히 3년 이상 요구인데 1~3년 구간과 겹치는지)은 사람마다
    판단이 갈릴 수 있는 영역이라, 겹치면 일단 포함시키고 최종 확인은
    사람 몫으로 남긴다.
    """
    text = text or ""
    tags: set[str] = set()

    if "신입" in text:
        tags.add("신입")

    range_m = re.search(r"(\d+)\s*[~\-]\s*(\d+)\s*년", text)
    over_m = re.search(r"(\d+)\s*년\s*(?:이상|↑)", text)
    entry_range_m = re.search(r"신입\s*[~\-]\s*(\d+)\s*년", text)

    if entry_range_m:
        hi = int(entry_range_m.group(1))
        for name, blo, bhi in BUCKETS:
            bhi_eff = bhi if bhi is not None else 999
            if hi >= blo:
                tags.add(name)

    if range_m:
        lo, hi = int(range_m.group(1)), int(range_m.group(2))
        for name, blo, bhi in BUCKETS:
            bhi_eff = bhi if bhi is not None else 999
            if lo <= bhi_eff and hi >= blo:
                tags.add(name)
    elif over_m:
        lo = int(over_m.group(1))
        for name, blo, bhi in BUCKETS:
            bhi_eff = bhi if bhi is not None else 999
            if bhi_eff >= lo:
                tags.add(name)

    if not tags:
        tags.add("확인필요")
    elif tags == {"신입"} and "경력" in text:
        # "신입·경력(년수무관)"처럼 숫자 없이 경력도 함께 언급된 경우
        tags.add("경력")
        tags.add("확인필요")

    if not range_m and not over_m and "경력" in text and "신입" not in text:
        tags.add("경력")
        tags.add("확인필요")

    return sorted(tags)
