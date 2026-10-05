#!/usr/bin/env python3
"""세션의 모델 식별자를 남기고, 새 세션(startup · clear)이 HANDOFF.md 가 있는
저장소에서 열리면 그 사실을 알린다.

SessionStart 훅. 작업을 시작시키지는 않는다 — 사용자가 "진행해" 라고 하면
/go 규칙으로 HANDOFF.md 를 읽고 이어받게 문맥만 넣는다.
"""
import json
import os
import sys
import tempfile


def record_model(data):
    """context_handoff 가 창 크기를 자동으로 정할 때 쓴다. 모델 필드는 빠질 수 있다."""
    model, session_id = data.get("model"), data.get("session_id")
    if not model or not session_id:
        return
    base = os.environ.get("CLAUDE_PLUGIN_DATA") or os.path.join(tempfile.gettempdir(), "tuzi")
    os.makedirs(base, exist_ok=True)
    # /clear 뒤 세션은 model 이 빠질 수 있어 마지막 값도 남긴다
    for name in (f"model-{session_id}", "model-latest"):
        with open(os.path.join(base, name), "w", encoding="utf-8") as f:
            f.write(str(model))


def main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return
    record_model(data)
    if data.get("source") not in ("startup", "clear"):
        return

    root = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
    handoff = os.path.join(root, "HANDOFF.md")
    if not os.path.isfile(handoff):
        return

    context = (
        f"[tuzi] 이 저장소에 인계 문서가 있다: {handoff}. "
        "사용자가 '진행해'·'계속해'·/go 처럼 이어가라고 하면 go 스킬 규칙대로 "
        "이 문서와 git status 를 대조해 '지금 당장 할 일' 부터 착수한다."
    )
    print(json.dumps(
        {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": context}},
        ensure_ascii=False,
    ))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"tuzi session_handoff: {e}", file=sys.stderr)
    sys.exit(0)
