# Tasks

Last Updated: 2026-09-10

## 0. 준비 (사용자)
- [ ] 원티드 OpenAPI 신청 (openapi.wanted.jobs) — 최우선, 승인 최대 3영업일
- [ ] Notion Integration 토큰 발급, "채용공고 트래커" DB에 연결 권한 부여
- [ ] ANTHROPIC_API_KEY 준비
- [ ] GitHub 저장소 생성

## 1. 손으로 한 번 — 완료
- [x] 노션 트래커에 13개 실제 공고 수동 수집·분류
- [x] 스키마 확정 (연차/인턴/계약직/마감일/마감됨/사이트/그룹)

## 2. 수집 스크립트
- [ ] 프로젝트 스캐폴딩 (requirements.txt, .gitignore, .env.example, 폴더 구조)
- [ ] `collectors/saramin.py` — 크롤링, 요청 간격 준수
- [x] `collectors/rocketpunch.py` — 시도 후 완전 제외 (형사처벌 경고 문구 + 로그인 게이트)
- [x] `collectors/careerly.py` — 사이트맵 기반 수집 완료
- [ ] `collectors/wanted.py` — 보류 (API vs 크롤링 미결정, 나중에 추가)
- [ ] 통합채용 감지 및 태그 필터링 로직

## 3. 적재 — 완료
- [x] `storage.py` SQLite 스키마 설계
- [x] 이중 기준 중복 제거 구현 (URL + 사이트·회사·직무명)
- [x] 같은 데이터 두 번 넣어도 안 깨지는지 확인 (테스트로 검증)

## 4. 자동 점검 — 완료
- [x] 필수 필드 체크 (`checks.py`)
- [x] 연차 파싱 (`career_parser.py`), 실패 시 "확인필요" 태그
- [x] 체크 결과 로그 출력 (정상/확인필요/실패 건수)
- 알려진 한계: 경계값(예: "신입~3년")에서 과포함 경향 있음. 최종 확인은 노션에서 사람이 함

## 5. 판별 로직
- [ ] `classify.py` 연차/인턴/계약직 정규식 파싱
- [ ] Claude API 연동 (직무 판별 프롬프트)
- [ ] 판별 결과 표본 검토 (오분류 확인)

## 6. 노션 업로드 + 스케줄
- [ ] `notion_sync.py` 신규 항목 업로드
- [ ] 기존 항목 마감일 재확인 로직
- [ ] `.github/workflows/collect.yml` 작성
- [ ] workflow_dispatch로 수동 1회 검증 후 cron 전환
