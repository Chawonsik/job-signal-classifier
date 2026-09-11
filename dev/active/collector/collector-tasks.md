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
- [x] `collectors/wanted.py` — 크롤링으로 완료. 내부 검색 API(`/api/chaos/search/v1/position`)로 후보 탐색, 연차는 API 응답의 annual_from/to로 정확히 파싱됨
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

## 5. 판별 로직 — 완료 (API 키 대신 구독 기반 클라우드 루틴으로 확정)
- [x] `classify.py`는 API 호출 코드 대신 판별 기준(INCLUDE/EXCLUDE)만 담은 참고용 상수 파일로 정리
- [x] 실제 판별은 클라우드 루틴 프롬프트에 기준을 그대로 임베드해서, 루틴이 직접 JD 읽고 판단
- [ ] 판별 결과 표본 검토 (오분류 확인) — 첫 실행 후 진행

## 6. 노션 업로드 + 스케줄 — 완료
- [x] main.py로 수집+적재+점검 파이프라인 완성, 사람인/원티드/커리어리 첫 실행 테스트 통과(총 566건 저장)
- [x] 깃허브 저장소 생성 (Chawonsik/job-signal-classifier, **Public** — claude.ai GitHub 연동이 public repo만 접근 가능해서 공개 전환함, 시크릿 없음 확인 완료)
- [x] claude.ai 스케줄 클라우드 루틴 생성 (trig_01HXfSsUsGdvZnMfzsjDVAEz, 이름: job-signal-daily)
  - 매일 KST 오전 9시(UTC 0시) 실행
  - Notion MCP 커넥터만 연결 (Google Drive/Vercel 등은 제외)
  - 프롬프트: main.py 실행 → pending_classification.json 읽고 직접 판별 → 채용공고 트래커 DB에 업로드(그룹/마감일/마감됨/계약직은 채우지 않음) → local.db·json 커밋/푸시로 상태 유지
- [ ] 다음 실행(2026-09-12 오전 9시경) 후 실제로 노션에 잘 들어갔는지, 커밋이 잘 됐는지 확인 필요

## 트러블슈팅 기록 (참고용)
- claude.ai 루틴이 private repo에 401→(연결 후)403 에러를 냄. 원인은 claude.ai의 "GitHub 연동" 기능이 OAuth 방식이라 저장소 선택 UI가 없고 **public 저장소만 접근 가능**했던 것. 저장소를 public으로 바꾸자 즉시 해결됨
- 클로드 데스크톱 앱의 "플러그인 > Github" 커넥터와 "커넥터 > GitHub 연동"은 서로 다른 별개 연동임 (전자는 이 세션 시작부터 깨져있던 것)

## 6. 노션 업로드 + 스케줄
- [ ] `notion_sync.py` 신규 항목 업로드
- [ ] 기존 항목 마감일 재확인 로직
- [ ] `.github/workflows/collect.yml` 작성
- [ ] workflow_dispatch로 수동 1회 검증 후 cron 전환
