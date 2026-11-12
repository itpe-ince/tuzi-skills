# tuzi-skills

스킬 작성 원칙은 README 「이 저장소의 규칙」이 정본이다. 여기에는 손이 기억해야 할 것만 둔다.

## 게이트
`claude plugin validate . && claude plugin validate .claude-plugin/plugin.json` — 커밋 전 이것 하나.
경고 1건("CLAUDE.md at the plugin root is not loaded")은 의도된 것이다 — 이 파일은 저장소 작업용이지 배포 문맥이 아니다.
`hooks/` 를 고쳤으면 가짜 전사로 훅 단위 시험을 함께 돌린다:
`echo '{"session_id":"t","transcript_path":"<jsonl>"}' | TUZI_HANDOFF_THRESHOLD=1 python3 hooks/context_handoff.py`
질문 도구를 거치는 훅(`decision_log.py`)은 `claude -p` 로 시험되지 않는다 — 입력 JSON 을 파이프로 넣거나 대화형 세션으로 본다.

## 스킬을 고친 뒤
1. 계기가 된 상황을 임시 저장소에서 처음부터 재현한다(`claude -p --plugin-dir <워크트리>`). 메일·외부 push·실 DB 쓰기는 빼거나 시험용으로 바꾼다
2. 고치기 전과 후를 PR 본문에 적는다. 재현하지 못했으면 못 했다고 적는다 — AI 결과는 매번 달라 한 번은 증명이 아니라 표본이다
3. `docs/skill-failures.md` 에 한 줄 남긴다. 같은 원인이 반복되면 다음 개선 대상이다

## 실행
**`/Users/sangincha/dev/tuzi/tuzi-skills` 는 master 에 둔다. 작업은 워크트리 `../tuzi-skills-work` 에서 한다.**
로컬 설치본(`tuzi@tuzi-skills`, 디렉터리 마켓플레이스)의 훅·스킬이 이 폴더에서 바로 실행된다(2026-11-04 디버그 기록 확인) —
브랜치를 바꾸거나 파일을 고치면 새로 여는 모든 세션에 번진다. 설치 기록에는 버전별 캐시 경로가 적혀 있지만 실행 경로는 이 폴더다.
`claude --plugin-dir <워크트리 경로>` → 한 세션만 그 워크트리로 시험.
머지 뒤 이 폴더에서 `git pull` 하고, version 을 올렸으면 `claude plugin marketplace update tuzi-skills && claude plugin update tuzi@tuzi-skills`. 열린 세션은 `/reload-plugins`.

## 배포
- 시점: 작업 단위마다 — master 머지가 곧 릴리스다(운영 서버 없음)
- 민감도: 낮음 — 머지 요청에 경고·재확인을 붙이지 않는다(머지 자체는 사용자가 말할 때). 머지 전 `version` 올림만 확인
- 방법: PR 머지 → 위 「실행」의 pull·플러그인 업데이트

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
