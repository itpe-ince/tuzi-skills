# HANDOFF — 2026-10-19 master

## 한 줄 현황
tuzi 플러그인(명령 12개 + 자동 인계 훅 2개)이 돈다. master 는 PR #6 머지(`20a4cc8`, 2.3.3)까지, 열린 PR 없음.
원격·로컬 브랜치는 `master` 하나(머지 끝난 6개 정리함). 설치본 2.3.3 — `installed_plugins.json` sha `20a4cc8`,
사용자 설정 `context_window: 1000000`.
스킬을 고치면 version 을 올리고 `claude plugin marketplace update tuzi-skills && claude plugin update tuzi@tuzi-skills`, 열린 세션은 `/reload-plugins`.

2026-10-12 ~ 19 에 들어간 것:
- PR #4 (2.3.1) `report` — HTML 에 Mermaid 를 넣으면 렌더러까지 넣고 블록마다 SVG 로 바뀌었는지 확인
- PR #5 (2.3.2) `go` — 같은 세션의 `진행해` 는 직전 응답의 제안·질문에 대한 답. 안의 일과 바깥 작업을 함께 물었으면 안의 일부터
- PR #6 (2.3.3) `ship` — 인자는 사슬. `/ship merge` 하나로 커밋·push·PR·병합

## 지금 당장 할 일
없음. 다음 작업은 master 에서 새 feature 브랜치를 따서 한다.
(미룬 것: `hooks/session_handoff.py` 가 세션마다 `model-<id>` 파일을 남기고 지우지 않는다,
`model-latest` 는 동시 세션끼리 덮어쓴다 — 우선순위 낮음)

## 기다리는 것 (사용자 결정)
없음.

## 확인한 것 / 확인 안 한 것
| 무엇 | 상태 | 증거 |
| --- | --- | --- |
| `/scan` 실세션 | 확인 | `claude -p "/scan"` — 파일 변경 0, 인계 문서와 실제가 어긋난 곳 5개를 찾음 |
| `/bench` 실세션 | 확인 안 함 | 웹 조사가 길어 돌리지 않았다 |
| `report` HTML Mermaid 렌더 | 확인 (실물 1건) | devx-collabo `docs/reports/2026-10-12-container-flow.html` 에 렌더러를 넣고 헤드리스 Chromium → 4개 모두 SVG, 콘솔 오류 0. 스킬이 새로 만든 HTML 로는 확인 안 함 |
| `go` 직전 응답 우선 | 확인 안 함 | 계기: deep-sos 세션 `e6cee1ba` — 직전 응답이 "두 건 고칠까요? 1번 머지할까요?" 로 끝난 뒤 `/go` 가 머지를 집었다. 고친 뒤 재현 안 함 |
| `/ship merge` 단독으로 push·PR·병합 | 확인 안 함 | 문서만 고침 |
| 오케스트레이션 중 인계 유예 | 확인 (재생) | 실전사 `d4b7778e`·`9e59f60f` 를 막힌 지점까지 잘라 재생 → 둘 다 미룸. 가짜 전사 6사례. 실제 오케스트레이션 세션에서는 확인 안 함 |
| 매니페스트 | 확인 | `claude plugin validate .` · `.claude-plugin/plugin.json` 둘 다 통과 (2.3.3) |
| Stop 훅 — 임계치에서 /handoff 강제 | 확인 | 가짜 전사 단위 시험 + 설치본 실세션(임계치 1%) → HANDOFF.md 생성 |
| 창 크기 자동 판정 | 확인 | 가짜 전사 7사례 |
| SessionStart 의 `model` 필드 (대화형) | 확인 — 들어온다, 단 `[1m]` 표기 없음 | 플러그인 데이터의 `model-bdbd42ff…` = `claude-opus-5-5`. 그래서 훅이 `ANTHROPIC_MODEL`·설정 `model` 도 보고, 200k 추정으로 막을 땐 창 크기 지정 안내를 붙인다(가짜 전사 8사례) |
| 1M 세션에서 실제 조기 인계 여부 | 확인 안 함 | 이 머신 세션이 1M 창인지 모른다 |
| `/go` 운영 결정 질문 | 확인 | `-p` 실세션 — 흔적 없음: 두 선택지·파일 변경 0건, 단일 기록 있음: 바로 착수 |
| 팀 선택 → plan → setup → run | 확인 안 함 | — |
| `/report` ERD·화면 절, 문서 자리 | 확인 | `-p` 실세션 — `docs/reports/…/index.md`, 설계→`docs/design/`, 설명서→`docs/guides/` |
| 실제 캡처가 든 화면 전후 비교 | 확인 안 함 | 시험 저장소에 앱 실행 설정이 없었다 |
| `/start` 가 `## 문서 자리` 를 남기는지 | 확인 안 함 | — |
| `/config` 에 tuzi 설정 두 항목 표시 | 확인 안 함 | CLI(`claude plugin configure`)로는 저장 확인 |
| 로컬 설치 | 확인 | 2.3.3 (2026-10-19), 캐시 `~/.claude/plugins/cache/tuzi-skills/tuzi/2.3.3`. `plugin update` 는 체크아웃을 다시 읽으므로 체크아웃을 머지 전 브랜치에 둔 채 갱신하지 않는다 |

## 하면 안 되는 것
- `plugin.json` 의 `version` 을 그대로 둔 채 릴리스하지 않는다 — `claude plugin update` 가
  "already at the latest version" 으로 끝나 사용자에게 안 간다. 릴리스마다 올린다
- `docs/team.md` 경로를 바꾸지 않는다 — `team` 이 운영 결정의 흔적으로 읽는다
- `~/.claude/CLAUDE.md` 의 「변경 보고 규약」을 빼라고 안내하지 않는다 — 매 턴 규칙이라 CLAUDE.md 자리다
  (`docs/evidence.md` 4장)
- 스킬 안에 도구 이름을 박지 않는다 (README 「이 저장소의 규칙」)
- 사용자 설정(`~/.claude/settings.json`)을 고칠 때는 먼저 백업한다 — 2026-10-06 설치 전 백업:
  `~/.claude/settings.json.bak-1791274614`

## 자주 쓰는 명령
- 게이트: `claude plugin validate . && claude plugin validate .claude-plugin/plugin.json` (경고 1 — 루트 CLAUDE.md, 의도됨)
- 한 세션만 시험: `claude --plugin-dir /Users/sangincha/dev/tuzi/tuzi-skills`
- 설치 상태: `claude plugin list` · `claude plugin configure tuzi@tuzi-skills`
- 훅 단위 시험: `echo '{"session_id":"t","transcript_path":"<jsonl>"}' | TUZI_HANDOFF_THRESHOLD=1 python3 hooks/context_handoff.py`
- 반복 지시 재집계: `python3 tools/harvest.py ~/.claude/projects --min-count 3`
