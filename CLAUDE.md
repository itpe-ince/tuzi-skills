# tuzi-skills

스킬 작성 원칙은 README 「이 저장소의 규칙」이 정본이다. 여기에는 손이 기억해야 할 것만 둔다.

## 게이트
`claude plugin validate . && claude plugin validate .claude-plugin/plugin.json` — 커밋 전 이것 하나.
경고 1건("CLAUDE.md at the plugin root is not loaded")은 의도된 것이다 — 이 파일은 저장소 작업용이지 배포 문맥이 아니다.
`hooks/` 를 고쳤으면 가짜 전사로 훅 단위 시험을 함께 돌린다:
`echo '{"session_id":"t","transcript_path":"<jsonl>"}' | TUZI_HANDOFF_THRESHOLD=1 python3 hooks/context_handoff.py`

## 실행
`claude --plugin-dir /Users/sangincha/dev/tuzi/tuzi-skills` → 한 세션만 이 체크아웃으로 시험.
로컬 설치본(`tuzi@tuzi-skills`)은 이 디렉터리를 그 자리에서 읽는다 — 브랜치를 바꾸면 설치본도 바뀐다.

## 하면 안 되는 것
- `plugin.json` 의 `version` 을 그대로 둔 채 릴리스하지 않는다 — `claude plugin update` 가 "already at the latest version" 으로 끝난다
- `docs/team.md` 경로를 바꾸지 않는다 — `team` 이 운영 결정의 흔적으로 읽는다
- 스킬 동작을 바꾸면 같은 커밋에서 `docs/guide.md`·`README.md` 의 해당 줄도 고친다 — 가이드가 정본이다
- 스킬 사이 링크는 절 제목 앵커로 걸려 있다(`report/SKILL.md#4-어디에-두나…`). 절 제목을 바꾸면 `grep -rn "SKILL.md#" skills` 로 호출부를 고친다

## 에이전트 운영
단일 — 2026-10-06 결정. 이유: 수정 대상이 서로 얽힌 마크다운 스킬이라 나누면 일관성 맞추는 비용이 더 크다. 팀으로 바꾸려면 `/team plan`

## 문서 자리
`docs/` 는 평면이다 — `guide.md`(사용 가이드 정본) · `evidence.md`(근거 집계). 새 분석·설계 문서는
`docs/analysis/` · `docs/design/` 에 `<YYYY-MM-DD>-<주제>.md` 로 둔다.
