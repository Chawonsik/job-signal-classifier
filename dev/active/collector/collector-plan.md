# 채용공고 데이터직무 판별 자동화 — 승인된 계획

Last Updated: 2026-09-10

전문은 `/Users/wonsik/.claude/plans/typed-wiggling-unicorn.md` 에 저장된 계획과 동일.

## Context
워크북(PART1~4) 완료. 노션 트래커에 13개 실제 공고로 손 작업(1단계) 완료. 이번 프로젝트는 PART4의 2~6단계를 코드로 구현.

**확정 스코프**: 원티드(공식 API) + 사람인·로켓펀치·커리어리(크롤링). 잡코리아·인크루트는 robots.txt 전체 차단으로 이번 범위 제외, 나중에 재검토.

## 구조
```
채용공고 데이터직무 판별 자동화/
├── .github/workflows/collect.yml
├── src/
│   ├── collectors/{wanted,saramin,rocketpunch,careerly}.py
│   ├── storage.py       # SQLite 적재 + 이중 기준(URL / 회사+직무+게시일) 중복 제거
│   ├── classify.py      # 연차·인턴·계약직 파싱 + Claude API 직무 판별
│   ├── notion_sync.py   # 노션 업로드 + 마감일 재확인
│   └── main.py
├── data/local.db (gitignore)
├── .env.example
├── requirements.txt
└── README.md
```

## 판별 로직 핵심
- 규칙: 연차(신입/1~3년/3~5년/5년+/경력/확인필요, 다중), 인턴·계약직 체크박스
- AI 판단(Claude API, Haiku급): 그로스/CRM/사업개발/전략기획/PM/PO/데이터분석 vs 제외(인플루언서·SNS마케팅, CS위주, 데이터엔지니어/개발자, 영업·행동위주)
- 그룹(지원후보/참고용)은 자동 결정 안 함 — 사람이 최종 배정
- 통합채용 공고: 태그에 포함 카테고리 있으면 "확인필요", 없으면 skip

## 노션 대상
데이터베이스: `collection://3b542d87-d02c-4cac-a6fb-07eb7e368217` ("채용공고 트래커")

## 사전 준비 (사용자)
- 원티드 OpenAPI 신청 (openapi.wanted.jobs, 승인 최대 3영업일 — 최우선 시작)
- Notion Integration 토큰 + DB 연결 권한
- ANTHROPIC_API_KEY
- GitHub 저장소 + Secrets 등록
