# NotebookLM Execution Archive

Last updated: 2026-02-19

## Purpose
- NotebookLM 실행 중 발생한 과부하/오류를 누적 관리
- 다음 실행 전에 같은 문제를 반복하지 않도록 기준을 제공

## Incident Log

### 2026-02-19 / Notebook naming policy (new)
- Requirement: 다수 노트북 생성 시 제목 앞 숫자 넘버링 부여
- Policy:
  - 기본 포맷: `NN_제목` (2자리 zero-padding)
  - 예시: `01_AI콘텐츠_기반모델`, `02_AI콘텐츠_개발생태계`
  - 통합 노트북: 마지막 번호 사용 (`06_AI콘텐츠_통합베스트소스`)
- Implementation:
  - `research/run_notebooklm_ai_content_pipeline.py`에 자동 넘버링 함수 적용
  - 실행 가드레일 문서(`docs/notebooklm/GUARDRAIL.md`)에 정책 반영

### 2026-02-19 / NotebookLM-only completion policy (new)
- Requirement:
  - NotebookLM 실행을 시작하면 중간에 NotebookLM 비사용 경로로 전환 금지
  - 과부하 시 멀티 에이전트 중지 또는 리서치 개수 축소를 강제
- Implementation:
  - `scripts/notebooklm_guardrail.sh`, `notebookLM`에서 강제 env 주입
  - `research/run_notebooklm_ai_content_pipeline.py`에서 강제 검증:
    - `NOTEBOOKLM_ONLY=1` 아니면 실행 중단
    - 과부하 이벤트 누적 시 임계값 도달 후 주제 확장 중단(감축 모드)

### 2026-02-19 / Deep-first + source-cap policy (new)
- Requirement:
  - "딥리서치" 요청 시 딥리서치를 최우선으로 시도
  - 충분히 긴 타임아웃 후 실패 시에만 fast 수집으로 전환
  - 소스 개수는 노트북당 최대 25개
  - YouTube + 아티클 혼합 및 해외 고퀄리티 소스 포함
- Implementation:
  - 강제 env:
    - `NOTEBOOKLM_DEEP_FIRST=1`
    - `NOTEBOOKLM_DEEP_TIMEOUT=1200`
    - `NOTEBOOKLM_MAX_SOURCES=25`
  - 파이프라인:
    - `research/run_notebooklm_ai_content_pipeline.py`
    - `research/run_agentic_workflow_deep_research.py`

### 2026-02-19 / Plain-language intent routing via wonseokjung feature map
- Requirement:
  - 일반 언어 요청도 `wonseokjung/notebooklm-mcp` 주요 기능 관점으로 먼저 해석 후 실행
- Implementation:
  - 기능 맵 문서 추가: `docs/notebooklm/WONSEOKJUNG_FEATURE_MAP.md`
  - 실행 라우터 추가: `scripts/notebooklm_intent_router.sh`
  - `notebookLM` 래퍼에서 unknown 입력은 라우터를 통해 `setup/status/list/ask`로 강제 매핑
  - 가드레일에서 기능 맵 문서 존재를 필수 체크

### 2026-02-19 / Learned improvements from this run
- Deep polling은 네트워크 상태에 따라 장시간 정체될 수 있음
  - 대응: deep-first + long-timeout + fallback 명시
- 장문 쿼리는 응답 지연 가능성이 큼
  - 대응: retry + 단계별 저장 + 과부하 감지 후 범위 감축
- 실행 중 정책 일관성이 흔들릴 수 있음
  - 대응: wrapper/guardrail/문서 3중 강제

### 2026-02-19 / Studio artifact missing despite local output
- Symptom:
  - 로컬 markdown 파일은 생성됐지만 NotebookLM UI(Studio)에는 산출물이 보이지 않음
- Root cause:
  - `query -> 로컬 저장` 경로만 실행하고 `create_report`(Studio artifact) 단계가 기본 경로에 없었음
- Prevention:
  - 기본 완료 기준을 Studio 아티팩트 완료로 변경
  - `NOTEBOOKLM_REQUIRE_STUDIO_ARTIFACT=1` 강제
  - 파이프라인에서 `create_report` + `poll_studio_status` 완료 체크 의무화

### 2026-02-19 / CLI ask headless browser crash (TargetClosedError)
- Symptom:
  - `./notebookLM ask ...` 실행 시 patchright headless Chrome이 즉시 종료
  - 오류: `BrowserType.launch_persistent_context: Target page, context or browser has been closed`
- Root cause:
  - 실행 환경 권한/프로세스 제약으로 headless 브라우저 실행 실패
- Prevention:
  - 콘텐츠 생성 완료 기준은 `ask` 결과가 아니라 Studio 아티팩트 완료(`create_report`)로 강제
  - 필요 시 `--show-browser`로 진단하되, 기본 생성 경로는 API 기반 Studio 생성 유지

### 2026-02-19 / Existing notebook ignored, new notebook created unnecessarily
- Symptom:
  - 기존 노트북에 Deep Research 결과가 있는데도 새 노트북이 생성됨
- Root cause:
  - 단일 주제 실행 스크립트가 기존 노트북 탐색/재사용 로직 없이 항상 `create_notebook` 수행
- Prevention:
  - 동일 주제 기존 노트북 재사용 우선
  - 기존 Deep Research 완료 + 소스 0개 상태에서는 기존 태스크를 우선 import
  - 기존 소스가 충분하면 신규 research 시작 금지

### 2026-02-19 / Recency prioritization policy for fast-changing domains
- Requirement:
  - AI처럼 시의성이 높은 주제는 최근 2년 자료를 최우선
  - 시의성 낮은 주제는 구자료를 허용
- Implementation:
  - `NOTEBOOKLM_RECENCY_WINDOW_YEARS=2` 기본값 강제
  - 소스 점수 계산에 recency bonus 적용(주제 시의성 판별 기반)
  - 리서치 쿼리에 최근 2년 우선 조건을 동적으로 삽입

### 2026-02-19 / Dependency install failed (network/DNS)
- Symptom: `pip install -r requirements.txt`에서 `nodename nor servname provided`
- Root cause: 샌드박스 네트워크 제한
- Resolution: 권한 상승 실행으로 설치 완료
- Guardrail:
  - 네트워크 필요한 단계는 `require_escalated` 권한으로 실행
  - 설치 단계 실패 시 재시도 전에 DNS/네트워크 확인

### 2026-02-19 / API auth expired
- Symptom: `RPC Error 16: Authentication expired`
- Root cause: `~/.notebooklm-mcp/auth.json` 세션 만료
- Resolution: `.venv/bin/notebooklm-mcp-auth --port 9223`로 토큰 재생성
- Guardrail:
  - 본 실행 전 `notebooklm-mcp-auth --show-tokens` 또는 상태 점검
  - 인증 실패 시 우선 재인증 후 재시도

### 2026-02-19 / Chrome driver mismatch
- Symptom: `SessionNotCreatedException` (ChromeDriver 145 vs browser 144)
- Root cause: `undetected_chromedriver` 경로의 버전 불일치
- Resolution: `verify_and_export_auth.py` 우회, 공식 `notebooklm-mcp-auth` 사용
- Guardrail:
  - 인증 추출은 `notebooklm-mcp-auth` 우선
  - `undetected_chromedriver` 기반 스크립트는 fallback으로만 사용

### 2026-02-19 / Deep research poll hang
- Symptom: `poll_research` 단계에서 장시간 정체
- Root cause: 네트워크/응답 지연 + deep polling 구간 불안정
- Resolution: `fast research + import + notebook query`로 전환
- Guardrail:
  - 기본 전략을 fast research로 시작
  - deep research는 제한 시간 내 실패 시 즉시 fallback

### 2026-02-19 / Long query timeout/overload
- Symptom: 장문 질의 중 `httpx` read 대기 장기화
- Root cause: 장문 응답 + 네트워크 변동
- Resolution: 질의 수 축소, retry(최대 3회), 단계별 즉시 저장
- Guardrail:
  - 한 노트북당 질의 횟수 최소화
  - 결과는 단계별로 즉시 파일 저장

## Stable Run Pattern (Recommended)
1. 인증/토큰 유효성 점검
2. 노트북 생성
3. fast research로 소스 수집
4. 소스 필터링 후 import (유튜브+아티클 비율 검증)
5. 최소 질의로 아티클 생성
6. 즉시 저장 후 다음 노트북 진행
