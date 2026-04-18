# NotebookLM Guardrail

Last updated: 2026-02-19

## Run Before Every Execution
- `docs/notebooklm/EXECUTION_ARCHIVE.md` 최근 이슈 확인
- `docs/notebooklm/WONSEOKJUNG_FEATURE_MAP.md` 기준으로 일반어 의도 해석
- 다수 노트북 생성 시 제목 넘버링 정책 적용 확인:
  - 형식: `01_제목`, `02_제목`, ...
  - 통합 노트북은 마지막 번호 사용 (예: 6개면 `06_...`)
- 인증 파일 존재 확인:
  - `~/.notebooklm-mcp/auth.json`
  - `skills/skills/notebooklm/data/browser_state/state.json`
- 실행 전략:
  - 기본은 fast research
  - deep research는 timeout 시 즉시 fallback
- 장문 질의는 retry 적용, 단계별 즉시 저장

## Mandatory Policy (Forced)
- NotebookLM 실행을 시작하면 끝까지 NotebookLM으로만 완료한다.
- 중간에 NotebookLM 비사용 경로(수동 웹검색/로컬 임의 대체)로 전환하지 않는다.
- 사용자가 "딥리서치"를 요청한 경우:
  - 딥리서치를 최우선으로 시도하고
  - 긴 타임아웃으로 충분히 대기한 뒤
  - 실패/타임아웃일 때만 fast 수집으로 전환한다.
- 과부하/대량 작업 시:
  - 멀티 에이전트 단계는 중지하거나,
  - 리서치 대상 개수를 줄여서 진행한다.
- 소스 수집 강제 조건:
  - 딥리서치 시 노트북당 최소 25개 소스 확보
  - 25개 초과로 리서치되면 모두 사용(상한 제한 없음)
  - YouTube + Article 혼합
  - 해외 고퀄리티(영문/글로벌) 소스 적극 포함
  - 시의성 높은 주제(AI/트렌드/정책 변화)는 최근 2년 자료 우선
  - 시의성 낮은 주제는 구자료 허용
- 강제 환경값:
  - `NOTEBOOKLM_ONLY=1`
  - `NOTEBOOKLM_ADAPTIVE_LOAD=1`
  - `NOTEBOOKLM_OVERLOAD_LIMIT=2` (기본)
  - `NOTEBOOKLM_DEEP_FIRST=1`
  - `NOTEBOOKLM_DEEP_TIMEOUT=1200` (기본)
  - `NOTEBOOKLM_MAX_SOURCES=0` (0 = no cap)
  - `NOTEBOOKLM_TARGET_SOURCES=25`
  - `NOTEBOOKLM_RECENCY_WINDOW_YEARS=2`
  - `NOTEBOOKLM_REQUIRE_STUDIO_ARTIFACT=1`

## Intent Interpretation (Forced)
- 사용자가 일반 언어로 말해도, 먼저 `wonseokjung/notebooklm-mcp` 주요 기능 맵으로 의도를 해석한다.
- 해석 결과를 NotebookLM 기능 그룹(노트북/소스/채팅/리서치/스튜디오/인증) 중 하나로 매핑한 후 실행한다.
- 매핑 불확실 시 NotebookLM 범주 내 `notebook_query`/`ask`로 보수적으로 처리한다.

## Deliverable Target (Forced)
- 특별한 명시가 없는 한, 결과물은 NotebookLM 내부(Studio)에서 생성 완료되어야 한다.
- 로컬 파일 저장은 보조 산출물이며, Studio 아티팩트 완료를 대체하지 않는다.
- 완료 기준: `studio_status == completed`

## Notebook Reuse (Forced)
- 동일 주제/유사 제목의 기존 노트북이 있으면 새 노트북 생성보다 **기존 노트북 재사용**을 우선한다.
- 기존 노트북에 Deep Research 완료 카드가 있고 소스가 비어있으면, 먼저 `가져오기(import)` 경로를 수행한다.
- 기존 소스가 충분하면(기본 10개 이상) 신규 리서치를 시작하지 않는다.

## Agentic Workflow Policy (Forced)
- 정책 파일: `docs/notebooklm/AGENTIC_WORKFLOW_POLICY.json`
- 실행 시 4개 에이전트 역할을 순서대로 적용:
  1. Source Curator
  2. Fact Synthesizer
  3. Blog Writer
  4. Quality Gate
- `notebookLM` 실행 명령:
  - `notebookLM workflow-agentic`
  - `notebookLM workflow-content6`

## Stop Conditions
- 인증 만료(`RPC Error 16`) 발생
- DNS/네트워크 에러가 2회 이상 반복
- 동일 단계에서 10분 이상 무응답

## Fallback Order
1. 재인증 (`.venv/bin/notebooklm-mcp-auth --port 9223`)
2. fast research 모드로 전환
3. 질의 횟수 축소 + 개별 재시도
