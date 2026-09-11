import json
import os
from dataclasses import dataclass

from models import Posting

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

MODEL = "claude-haiku-4-5-20251001"

INCLUDE = (
    "그로스/CRM/퍼포먼스 마케터, 사업개발/기획, 데이터분석가(데이터 엔지니어 제외), "
    "PM/PO처럼 데이터로 의사결정하는 직무"
)
EXCLUDE = "인플루언서/SNS 마케터, CS 위주 마케팅, 데이터 엔지니어/개발자, 영업·행동 위주 분석직"

PROMPT_TEMPLATE = """다음은 채용공고 원문 일부입니다. 이 공고의 직무가 데이터 기반 직무인지 판단해주세요.

포함 대상: {include}
제외 대상: {exclude}

키워드 매칭이 아니라 실제 업무 내용을 읽고 판단하세요. 애매하면 is_data_driven을 false로 하고
reason에 이유를 적으세요.

공고 원문:
---
{text}
---

아래 JSON 형식으로만 답하세요. 다른 말은 하지 마세요.
{{"is_data_driven": true 또는 false, "reason": "한 줄 이유"}}
"""


@dataclass
class Classification:
    is_data_driven: bool
    reason: str


def classify_job(posting: Posting, client=None) -> Classification:
    from anthropic import Anthropic

    client = client or Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    prompt = PROMPT_TEMPLATE.format(
        include=INCLUDE, exclude=EXCLUDE, text=(posting.requirement_text or "")[:4000]
    )

    resp = client.messages.create(
        model=MODEL,
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = resp.content[0].text.strip()
    try:
        data = json.loads(raw)
        return Classification(is_data_driven=bool(data["is_data_driven"]), reason=data.get("reason", ""))
    except (json.JSONDecodeError, KeyError):
        return Classification(is_data_driven=False, reason=f"응답 파싱 실패: {raw[:100]}")


if __name__ == "__main__":
    samples = [
        Posting(
            site="원티드",
            company="화이트큐브",
            title="Account Manager - 광고 운영",
            url="https://example.com/1",
            requirement_text=(
                "광고/마케팅/고객사 관리 경험이 있는 분. 모객률, 구매율, 매출 등의 광고 데이터 "
                "기반으로 광고 성과를 해석하여 개선 방향을 제안하고 실행해요."
            ),
        ),
        Posting(
            site="사람인",
            company="테스트기업",
            title="고객센터 상담원",
            url="https://example.com/2",
            requirement_text="전화 응대 및 CS 처리, 고객 문의 상담, 친절한 응대 태도 필수",
        ),
    ]
    for s in samples:
        print(s.title, "->", classify_job(s))
