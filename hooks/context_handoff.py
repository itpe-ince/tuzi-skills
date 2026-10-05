#!/usr/bin/env python3
"""컨텍스트가 임계치를 넘으면 응답을 끝내지 못하게 막고 /handoff 를 시킨다.

Stop 훅. 입력에는 사용률이 없어서 전사(transcript_path)의 마지막 응답 usage 로 계산한다.

설정 (앞이 우선):
  1. 환경 변수 TUZI_HANDOFF_THRESHOLD · TUZI_CONTEXT_WINDOW
     — 프로젝트별로 바꿀 때 .claude/settings.json 의 "env" 에 둔다
  2. 플러그인 설정 handoff_threshold · context_window (/config 또는 설치 시 입력)
     — Claude Code 가 CLAUDE_PLUGIN_OPTION_<KEY> 로 넘긴다
  3. 기본값 70 · 자동
임계치 0 은 끈다.

창 크기를 0(자동)으로 두면 이 순서로 정한다. 어느 훅 입력에도 창 크기 필드는 없다.
  a. SessionStart 훅이 남긴 모델 식별자에 [1m] 이 있으면 1,000,000
     (/clear 뒤처럼 이 세션 값이 없으면 마지막으로 남은 값)
  b. 실제로 읽은 토큰이 200,000 을 넘었으면 1,000,000 (그보다 작은 창일 수 없다)
  c. 그 외 200,000
"""
import json
import os
import sys
import tempfile

DEFAULT_THRESHOLD = 70.0
STANDARD_WINDOW = 200_000
LARGE_WINDOW = 1_000_000


def setting(env_key, option_key, default):
    for key in (env_key, option_key):
        raw = os.environ.get(key, "").strip()
        if raw:
            try:
                return float(raw.replace("_", "").replace(",", ""))
            except ValueError:
                pass
    return default


def last_context_tokens(transcript_path):
    """메인 대화의 마지막 응답이 읽은 입력 토큰 수. 못 찾으면 None."""
    last = None
    with open(transcript_path, encoding="utf-8") as f:
        for line in f:
            if '"assistant"' not in line:
                continue
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if row.get("type") != "assistant" or row.get("isSidechain"):
                continue
            usage = (row.get("message") or {}).get("usage")
            if usage:
                last = usage
    if not last:
        return None
    return (
        last.get("input_tokens", 0)
        + last.get("cache_read_input_tokens", 0)
        + last.get("cache_creation_input_tokens", 0)
    )


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


def auto_window(session_id, tokens):
    if "[1m]" in session_model(session_id).lower():
        return LARGE_WINDOW
    if tokens > STANDARD_WINDOW:
        return LARGE_WINDOW
    return STANDARD_WINDOW


def main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return
    if data.get("stop_hook_active"):
        return

    threshold = setting("TUZI_HANDOFF_THRESHOLD", "CLAUDE_PLUGIN_OPTION_HANDOFF_THRESHOLD", DEFAULT_THRESHOLD)
    window = setting("TUZI_CONTEXT_WINDOW", "CLAUDE_PLUGIN_OPTION_CONTEXT_WINDOW", 0)
    if threshold <= 0:
        return

    path = data.get("transcript_path")
    session_id = data.get("session_id") or "unknown"
    if not path or not os.path.exists(path):
        return

    tokens = last_context_tokens(path)
    if tokens is None:
        return
    if window <= 0:
        window = auto_window(session_id, tokens)
    pct = tokens / window * 100
    if pct < threshold:
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
    print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # 훅 오류로 세션을 멈추지 않는다
        print(f"tuzi context_handoff: {e}", file=sys.stderr)
    sys.exit(0)
