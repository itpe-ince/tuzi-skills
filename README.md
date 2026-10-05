# tuzi-skills

Claude Code 스킬 묶음. **소프트웨어 라이프사이클 순서**로 명령을 나눴다 —
지금 어느 단계인지만 알면 무엇을 부를지 정해진다.

규칙은 **세션 전사에서 반복된 지시를 세어** 만들었다. 같은 지시를 여러 세션에서
반복해 입력했다는 것은 그 지시가 기본 동작이 아니라는 뜻이다. 근거는
[docs/evidence.md](docs/evidence.md).

## 한눈에

```
  시작         진행             검증         보고          배포         인계
 ┌──────┐   ┌──────┬──────┐   ┌───────┐   ┌────────┐   ┌──────┐   ┌─────────┐
 │start │──▶│  go  │ fix  │──▶│ check │──▶│ report │──▶│ ship │──▶│ handoff │
 └──────┘   └──────┴──────┘   └───────┘   └────────┘   └──────┘   └─────────┘
                 ▲                                                     │
                 └──────────────── 다음 세션은 go 로 받는다 ◀───────────┘

  auto = go → check → report → ship(로컬 커밋) 을 끝까지 한 번에
  team = 여러 에이전트로 나눠 돌릴 때 (분석 → 편성 → 구성 → 위임)
```

| 단계 | 명령 | 이렇게 말해도 된다 | 하는 일 |
| --- | --- | --- | --- |
| 1 시작 | `/tuzi:start [목표]` | 새 프로젝트 만들어줘 · 이 저장소 파악해줘 | 기준선 측정 · 게이트 하나 · 얇은 끝-끝 경로 · `CLAUDE.md`/`HANDOFF.md` |
| 2 진행 | `/tuzi:go [할 일]` | 진행해 · 계속해 · 알아서 해 | 중단 지점 복원 → 한 수 착수. 워크트리 안은 묻지 않는다 |
| 2 고치기 | `/tuzi:fix [증상]` | 근본 원인 해결해줘 | 원인 한 문장 → 재현 → 같은 구멍 → 강제자 |
| 3 검증 | `/tuzi:check [대상]` | 확인해봐 · 띄워줘 | 실물 기동 · 증거 파일 · 확인/미확인 분리 · 1라운드 상한 |
| 4 보고 | `/tuzi:report [형식]` | 보고해줘 · 워드로 만들어줘 | 3열 대조 + 이유 + 영향 파일 · 문서 산출물(Pretendard) |
| 5 배포 | `/tuzi:ship [push\|pr\|deploy]` | 커밋해줘 · pr 올려줘 | 게이트 → 브랜치 → 경로 add → 로컬 커밋. 바깥은 말한 턴에만 |
| 6 인계 | `/tuzi:handoff` | 세션 넘겨 · 인수인계 | `HANDOFF.md` — 다음 세션이 `go` 한 번으로 받는다 |
| 끝까지 | `/tuzi:auto <목표>` | 끝나면 알려줘 | 2→5 를 멈추지 않고. 워크트리 밖에서만 멈춘다 |
| 팀 | `/tuzi:team [plan\|setup\|run\|status\|clean]` | 프로젝트 분석해서 에이전트 구성해줘 · 워커에 맡겨 | 구조·커밋 이력 분석 → 워커 명단(`docs/team.md`) → 구성 → 위임 |
| 지도 | `/tuzi:help` | 뭐 써야 해? | 이 표 + 지금 저장소 상태에 맞는 다음 명령 하나 |

**하나만 기억한다면** — 시작할 때 `/tuzi:go`, 끝까지 맡길 때 `/tuzi:auto`.

명령을 외울 필요는 없다. 각 스킬의 설명에 위 "이렇게 말해도 된다" 표현이 들어 있어
`진행해` · `확인해봐` 처럼 평소대로 말해도 해당 단계가 불린다.

## 설치

### 플러그인 (권장 — `/tuzi:` 접두가 붙는다)

Claude Code 안에서:

```
/plugin marketplace add itpe-ince/tuzi-skills
/plugin install tuzi@tuzi-skills
```

로컬 체크아웃으로 시험할 때:

```bash
claude --plugin-dir /경로/tuzi-skills
```

### 개별 스킬로 복사 (접두 없이 `/go`, `/check` …)

다른 스킬과 이름이 겹칠 수 있다(`help` 는 내장 명령과 겹치므로 빼고 건다).

```bash
for d in skills/*/; do
  n=$(basename "$d"); [ "$n" = help ] && continue
  ln -sfn "$PWD/${d%/}" ~/.claude/skills/"$n"    # 링크 — git pull 하면 바로 반영
done
```

### v1(`tuzi-core`)에서 옮겨 올 때

`~/.claude/skills/` 에 걸어 둔 v1 스킬 10개를 지운다. 같은 규칙이 두 이름으로
불리면 한쪽만 고치게 된다. 어떤 규칙이 어디로 갔는지는
[docs/evidence.md 2장](docs/evidence.md#2-묶음-구성--v1-스킬-10개--v2-라이프사이클-명령).

```bash
cd ~/.claude/skills && rm -f resume-work verify-for-real change-report commit-gate \
  orchestration-setup worker-delegation root-cause-first effort-budget \
  autonomy-scope deliverable-docs
```

설치 후 `~/.claude/CLAUDE.md` 에서 「변경 보고 규약」·「산출물 폰트 규약」 절을 뺀다
(`report` 가 맡는다).

## 구조

```
.claude-plugin/        plugin.json · marketplace.json
skills/<단계>/SKILL.md  라이프사이클 명령 10개
skills/team/references/ 편성 설계(design) · 구성(setup) · 위임(delegation) 상세
docs/evidence.md       근거 — 사람이 쓴 메시지 1,362건 집계
tools/harvest.py       근거를 다시 세는 스크립트
```

## 갱신

```bash
python3 tools/harvest.py ~/.claude/projects --min-count 3
```

세션 전사에서 반복 지시를 다시 세어 마크다운으로 출력한다. 새 지시가 나오면
**어느 라이프사이클 단계에서 나왔는지** 보고 그 스킬에 붙인다. 취합 절차는
[docs/evidence.md](docs/evidence.md) 3장.

## 이 저장소의 규칙

- **스킬은 도구를 지명하지 않는다.** 도구 이름이 박힌 규칙은 그 도구가 사라지면
  거짓말이 된다. 실제로 겪었다 — 2026-10-05 에 hi-loop·code-viz·bkit 을 지웠을 때
  규칙 문서만 남아 매 턴 노출됐다
- **프로젝트 고유 지식은 스킬이 아니다.** 게이트 스크립트 이름, 바꾸면 안 되는 키 같은
  것은 그 저장소의 `CLAUDE.md`·`HANDOFF.md` 자리다 (`start` 가 뼈대를 만든다)
- **모든 턴에 적용되는 것도 스킬이 아니다.** 응답 언어·어조는 `CLAUDE.md` 다.
  스킬은 호출돼야 읽힌다
- **1회성 지시는 스킬이 아니다.** 반복된 것만 올린다
- **명령 이름은 라이프사이클 동사다.** 규칙 내용으로 이름을 짓지 않는다 — v1 이
  그래서 무엇을 불러야 할지 떠올리기 어려웠다
- **숫자를 바꿨으면 표본을 열어 본다.** 집계만 보고 통과시켜 두 번 틀렸다
  (주입 턴 357건, 제품 도메인 어휘 81건 — 둘 다 숫자는 그럴듯했다)
