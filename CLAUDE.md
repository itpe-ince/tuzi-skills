# tuzi-skills

스킬 작성 원칙은 README 「이 저장소의 규칙」이 정본이다. 여기에는 손이 기억해야 할 것만 둔다.

## 게이트
`claude plugin validate . && claude plugin validate .claude-plugin/plugin.json` — 커밋 전 이것 하나.
경고 1건("CLAUDE.md at the plugin root is not loaded")은 의도된 것이다 — 이 파일은 저장소 작업용이지 배포 문맥이 아니다.
`hooks/` 를 고쳤으면 가짜 전사로 훅 단위 시험을 함께 돌린다:
`echo '{"session_id":"t","transcript_path":"<jsonl>"}' | TUZI_HANDOFF_THRESHOLD=1 python3 hooks/context_handoff.py`
질문 도구를 거치는 훅(`decision_log.py`)은 `claude -p` 로 시험되지 않는다 — 입력 JSON 을 파이프로 넣거나 대화형 세션으로 본다.

## 스킬을 고친 뒤
1. 계기가 된 상황을 임시 저장소에서 처음부터 재현한다(`claude -p --plugin-dir <이 체크아웃>`). 메일·외부 push·실 DB 쓰기는 빼거나 시험용으로 바꾼다
2. 고치기 전과 후를 PR 본문에 적는다. 재현하지 못했으면 못 했다고 적는다 — AI 결과는 매번 달라 한 번은 증명이 아니라 표본이다
3. `docs/skill-failures.md` 에 한 줄 남긴다. 같은 원인이 반복되면 다음 개선 대상이다

## 실행
`claude --plugin-dir /Users/sangincha/dev/tuzi/tuzi-skills` → 한 세션만 이 체크아웃으로 시험.
로컬 설치본(`tuzi@tuzi-skills`, 디렉터리 마켓플레이스)은 버전별 캐시 복사본으로 기록된다 —
고친 뒤 version 을 올리고 `claude plugin marketplace update tuzi-skills && claude plugin update tuzi@tuzi-skills`, 새 세션에서 적용.

## 하면 안 되는 것
- `plugin.json` 의 `version` 을 그대로 둔 채 릴리스하지 않는다 — `claude plugin update` 가 "already at the latest version" 으로 끝난다
- `docs/team.md` 경로를 바꾸지 않는다 — `team` 이 운영 결정의 흔적으로 읽는다
- 스킬 동작을 바꾸면 같은 커밋에서 `docs/guide.md`·`README.md` 의 해당 줄도 고친다 — 가이드가 정본이다
- 스킬 사이 링크는 절 제목 앵커로 걸려 있다(`report/SKILL.md#4-어디에-두나…`). 절 제목을 바꾸면 `grep -rn "SKILL.md#" skills` 로 호출부를 고친다

## 에이전트 운영
단일 — 2026-10-06 결정. 이유: 수정 대상이 서로 얽힌 마크다운 스킬이라 나누면 일관성 맞추는 비용이 더 크다. 팀으로 바꾸려면 `/team plan`

## 문서 자리
`docs/` 는 평면이다 — `guide.md`(사용 가이드 정본) · `evidence.md`(근거 집계) · `skill-failures.md`(스킬 실패 기록) · `decisions.md`(결정 이력, 훅이 쓴다). 새 분석·설계 문서는
`docs/analysis/` · `docs/design/` 에 `<YYYY-MM-DD>-<주제>.md` 로 둔다.
