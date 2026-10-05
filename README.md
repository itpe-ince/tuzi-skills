# tuzi-skills

Claude Code 스킬 묶음. **세션 전사에서 반복된 지시를 세어** 만든다 — 같은 지시를
여러 세션에서 반복해 입력했다는 것은 그 지시가 기본 동작이 아니라는 뜻이고,
반복 횟수가 곧 "기본값이 틀어져 있는 지점"의 측정값이다.

## 묶음

| 묶음 | 스킬 수 | 무엇을 다루나 |
| --- | --- | --- |
| [tuzi-core](tuzi-core/) | 10 | 이어받기 · 실물 확인 · 변경 보고 · 커밋 · 오케스트레이션 · 근본 원인 · 검증 상한 · 자율 범위 · 문서 산출물 |

근거와 수집 방법은 [tuzi-core/README.md](tuzi-core/README.md) 에 있다.

## 설치

```bash
git clone https://github.com/itpe-ince/tuzi-skills.git
cd tuzi-skills

# 복사 — 이 저장소를 당겨도 반영되지 않는다
for d in tuzi-core/*/; do [ -f "$d/SKILL.md" ] && cp -r "$d" ~/.claude/skills/; done

# 또는 심볼릭 링크 — git pull 하면 바로 반영된다
for d in tuzi-core/*/; do [ -f "$d/SKILL.md" ] && ln -sfn "$PWD/${d%/}" ~/.claude/skills/; done
```

플러그인으로 배포할 때는 각 스킬 디렉터리를 플러그인의 `skills/` 아래로 옮긴다.

## 갱신

```bash
python3 tuzi-core/harvest.py ~/.claude/projects --min-count 3
```

세션 전사에서 반복 지시를 다시 세어 마크다운으로 출력한다. 다른 기계·다른 계정의
전사에도 그대로 돈다. 취합 절차는 [tuzi-core/README.md](tuzi-core/README.md) 3장.

## 이 저장소의 규칙

- **스킬은 도구를 지명하지 않는다.** 도구 이름이 박힌 규칙은 그 도구가 사라지면
  거짓말이 된다. 실제로 겪었다 — 2026-10-05 에 hi-loop·code-viz·bkit 을 지웠을 때
  규칙 문서만 남아 매 턴 노출됐다
- **프로젝트 고유 지식은 스킬이 아니다.** 게이트 스크립트 이름, 바꾸면 안 되는 키 같은
  것은 그 저장소의 `CLAUDE.md`·`HANDOFF.md` 자리다
- **모든 턴에 적용되는 것도 스킬이 아니다.** 응답 언어·어조는 `CLAUDE.md` 다.
  스킬은 호출돼야 읽힌다
- **1회성 지시는 스킬이 아니다.** 반복된 것만 올린다
- **숫자를 바꿨으면 표본을 열어 본다.** 집계만 보고 통과시켜 두 번 틀렸다
  (주입 턴 357건, 제품 도메인 어휘 81건 — 둘 다 숫자는 그럴듯했다)
