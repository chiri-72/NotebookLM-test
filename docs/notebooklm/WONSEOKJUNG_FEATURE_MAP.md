# wonseokjung/notebooklm-mcp Feature Map

Source: https://github.com/wonseokjung/notebooklm-mcp (README 기준)
Updated: 2026-02-19

## 목적
- 일반 언어 요청을 NotebookLM MCP 주요 기능으로 해석하기 위한 기준 맵
- 실행 전에 이 맵을 참조해 명령을 결정하도록 강제

## 주요 기능 그룹 (README "주요 기능" 기반)
- 노트북 관리:
  - `notebook_list`, `notebook_create`, `notebook_get`, `notebook_describe`, `notebook_rename`, `notebook_delete`
- 소스 관리:
  - `notebook_add_url`, `notebook_add_text`, `notebook_add_drive`
  - `source_describe`, `source_get_content`, `source_list_drive`, `source_sync_drive`, `source_delete`
- 채팅/질의:
  - `chat_configure`, `notebook_query`
- 리서치:
  - `research_start`, `research_status`, `research_import`
- 스튜디오 생성:
  - `audio_overview_create`, `video_overview_create`, `infographic_create`, `slide_deck_create`, `studio_status`, `studio_delete`
- 인증:
  - `refresh_auth`, `save_auth_tokens`

## 일반어 의도 → 기능 그룹 매핑 규칙
- "로그인/인증/세션" → 인증
- "노트북 목록/찾기/선택" → 노트북 관리
- "노트북 만들기/생성" → 노트북 관리
- "링크/유튜브/문서 추가" → 소스 관리
- "질문/요약/정리/분석" → 채팅/질의
- "딥리서치/웹 조사/소스 발굴" → 리서치
- "팟캐스트/슬라이드/인포그래픽" → 스튜디오 생성

## 실행 원칙
- 해석 결과가 리서치 관련이면:
  - 딥리서치 우선
  - 실패 시 fast research fallback
- 해석 결과가 모호하면:
  - NotebookLM 범주 안에서 가장 보수적으로 `notebook_query` 중심으로 처리
- NotebookLM 외 도구로 우회 금지

