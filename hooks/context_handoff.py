#!/usr/bin/env python3
"""컨텍스트가 임계치를 넘으면 응답을 끝내지 못하게 막고 /handoff 를 시킨다.

Stop 훅. 입력에는 사용률이 없어서 전사(transcript_path)의 마지막 응답 usage 로 계산한다.

설정 (앞이 우선):
  1. 환경 변수 TUZI_HANDOFF_THRESHOLD · TUZI_CONTEXT_WINDOW
     — 프로젝트별로 바꿀 때 .claude/settings.json 의 "env" 에 둔다
  2. 플러그인 설정 handoff_threshold · context_window (/config 또는 설치 시 입력)
     — Claude Code 가 CLAUDE_PLUGIN_OPTION_<KEY> 로 넘긴다
  3. 기본값 70 · 1,000,000 (2026-10-06 — 자동 판정이 대화형 세션에서 1M 창을 200k 로 보고
     140k 에서 막아, 기본을 1M 으로 바꿨다. 200k 창 모델이면 200000 으로 지정한다)
임계치 0 은 끈다.

창 크기를 0(자동)으로 두면 이 순서로 정한다. 어느 훅 입력에도 창 크기 필드는 없다.
  a. 모델 지정에 [1m] 이 있으면 1,000,000 — SessionStart 훅이 남긴 모델 식별자
     (/clear 뒤처럼 이 세션 값이 없으면 마지막으로 남은 값), ANTHROPIC_MODEL,
     설정 파일(프로젝트 .claude/settings.local.json · .claude/settings.json, 사용자
     ~/.claude/settings.json)의 "model" 순으로 본다
  b. 실제로 읽은 토큰이 200,000 을 넘었으면 1,000,000 (그보다 작은 창일 수 없다)
  c. 그 외 200,000 — 근거 없는 추정이다. 1M 창인데 a 에 걸리지 않으면 b 에 닿기 전에
     200k 기준으로 먼저 막히므로, 막을 때 창 크기를 지정하라는 안내를 붙인다
     (2026-10-06 대화형 세션의 SessionStart model 은 "claude-opus-5-5" — [1m] 표기가 없었다)

오케스트레이션 중에는 미룬다. 백그라운드로 띄운 작업(tool_use 의 run_in_background)
가운데 완료 알림(<task-notification> 의 <tool-use-id>)이 아직 안 온 것이 있으면
코디네이터가 워커를 기다리는 중이다 — 그때 막으면 조정이 끊긴다(2026-10-06 세션
d4b7778e · 9e59f60f). 표시를 남기지 않으므로 작업이 끝난 뒤의 Stop 에서 다시 잰다.
다만 임계치 + DEFER_MARGIN 에 닿으면 미루지 않는다 — 알림이 영영 안 오는 작업이
인계를 무한히 막지 못하게 한다.
"""
import json
import os
import re
import sys
import tempfile

DEFAULT_THRESHOLD = 70.0
STANDARD_WINDOW = 200_000
LARGE_WINDOW = 1_000_000
DEFAULT_WINDOW = LARGE_WINDOW
DEFER_MARGIN = 15.0
TOOL_USE_ID = re.compile(r"<tool-use-id>([^<]+)</tool-use-id>")


def setting(env_key, option_key, default):
    for key in (env_key, option_key):
        raw = os.environ.get(key, "").strip()
        if raw:
            try:
                return float(raw.replace("_", "").replace(",", ""))
            except ValueError:
                pass
    return default


def scan_transcript(transcript_path):
    """메인 대화의 (마지막 응답이 읽은 입력 토큰 수 또는 None, 완료 알림이 안 온 백그라운드 작업 id 집합)."""
    last = None
    pending = set()
    with open(transcript_path, encoding="utf-8") as f:
        for line in f:
            if "task-notification" in line:
                pending.difference_update(TOOL_USE_ID.findall(line))
            if '"assistant"' not in line:
                continue
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if row.get("type") != "assistant" or row.get("isSidechain"):
                continue
            message = row.get("message") or {}
            for block in message.get("content") or []:
                if (
                    isinstance(block, dict)
                    and block.get("type") == "tool_use"
                    and (block.get("input") or {}).get("run_in_background")
                ):
                    pending.add(block.get("id"))
            if message.get("usage"):
                last = message["usage"]
    if not last:
        return None, pending
    tokens = (
        last.get("input_tokens", 0)
        + last.get("cache_read_input_tokens", 0)
        + last.get("cache_creation_input_tokens", 0)
    )
    return tokens, pending


def data_dir():
    base = os.environ.get("CLAUDE_PLUGIN_DATA") or os.path.join(tempfile.gettempdir(), "tuzi")
    os.makedirs(base, exist_ok=True)
    return base


def marker_path(session_id):
    return os.path.join(data_dir(), f"handoff-fired-{session_id}")


def session_model(session_id):
    for name in (f"model-{session_id}", "model-latest"):
        try:
            with open(os.path.join(data_dir(), name), encoding="utf-8") as f:
                return f.read().strip()
        except OSError:
            continue
    return ""


def configured_models():
    """사용자가 지정한 모델 문자열들. 세션 식별자에 [1m] 이 빠져도 여기엔 남을 수 있다."""
    models = [os.environ.get("ANTHROPIC_MODEL", "")]
    project = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    for path in (
        os.path.join(project, ".claude", "settings.local.json"),
        os.path.join(project, ".claude", "settings.json"),
        os.path.join(os.path.expanduser("~"), ".claude", "settings.json"),
    ):
        try:
            with open(path, encoding="utf-8") as f:
                models.append(str(json.load(f).get("model") or ""))
        except (OSError, ValueError, AttributeError):
            continue
    return models


def auto_window(session_id, tokens):
    """(창 크기, 근거가 있었나)"""
    for model in [session_model(session_id)] + configured_models():
        if "[1m]" in model.lower():
            return LARGE_WINDOW, True
    if tokens > STANDARD_WINDOW:
        return LARGE_WINDOW, True
    return STANDARD_WINDOW, False


def main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return
    if data.get("stop_hook_active"):
        return

    threshold = setting("TUZI_HANDOFF_THRESHOLD", "CLAUDE_PLUGIN_OPTION_HANDOFF_THRESHOLD", DEFAULT_THRESHOLD)
    window = setting("TUZI_CONTEXT_WINDOW", "CLAUDE_PLUGIN_OPTION_CONTEXT_WINDOW", DEFAULT_WINDOW)
    if threshold <= 0:
        return

    path = data.get("transcript_path")
    session_id = data.get("session_id") or "unknown"
    if not path or not os.path.exists(path):
        return

    tokens, pending = scan_transcript(path)
    if tokens is None:
        return
    guessed = False
    if window <= 0:
        window, known = auto_window(session_id, tokens)
        guessed = not known
    pct = tokens / window * 100
    if pct < threshold:
        return
    if pending and pct < threshold + DEFER_MARGIN:
        return

    # 세션마다 한 번만 막는다. 인계 뒤에도 같은 세션에서 계속 쓰면 다시 막지 않는다
    marker = marker_path(session_id)
    if os.path.exists(marker):
        return
    with open(marker, "w") as f:
        f.write(f"{tokens} {pct:.1f}\n")

    reason = (
        f"[tuzi] 컨텍스트 {pct:.0f}% 사용 ({tokens:,} / {int(window):,} 토큰, 인계 임계치 {threshold:g}%). "
        "새 작업을 시작하지 말고 지금 handoff 스킬(/handoff) 절차를 수행하라 — "
        "미커밋 정리 후 HANDOFF.md 갱신. 끝나면 사용자에게 '/clear 입력 후 /go 로 이어받으면 됩니다' 라고 알린다."
    )
    if pending:
        reason += (
            f" 백그라운드 작업 {len(pending)}건이 아직 완료 알림을 보내지 않았지만 미룰 수 있는 상한"
            f"({threshold + DEFER_MARGIN:g}%)을 넘었다. 워커·작업의 현재 상태를 조회해 HANDOFF.md 에 적는다."
        )
    if guessed:
        reason += (
            " 창 크기는 200k 로 추정했다(모델 지정에 [1m] 없음). 1M 창이면 사용자에게 "
            "'/config 의 tuzi context_window 를 기본값 1000000 으로 되돌리면 이 이른 인계가 사라집니다' 라고 함께 알린다."
        )
    print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # 훅 오류로 세션을 멈추지 않는다
        print(f"tuzi context_handoff: {e}", file=sys.stderr)
    sys.exit(0)
