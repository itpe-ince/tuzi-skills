#!/usr/bin/env python3
"""사용자에게 물어 받은 답을 프로젝트 문서에 남긴다.

PostToolUse 훅(질문 도구). 대화가 끝나면 무엇을 물었고 무엇을 골랐는지 찾을 수 없어,
답을 받는 순간 저장소 안 문서에 항목을 덧붙인다. 이유·결과·상태는 스킬이 채운다
(skills/go/references/decisions.md).

자리: 저장소 루트의 DECISIONS.md 가 있으면 그것, 없으면 docs/decisions.md.
끄기: 플러그인 설정 decision_log = 0, 또는 환경 변수 TUZI_DECISION_LOG=0.
git 저장소 밖이면 쓰지 않는다. 오류가 나도 세션을 멈추지 않는다.
"""
import datetime
import json
import os
import re
import subprocess
import sys

RECOMMENDED = re.compile(r"\(?\s*(recommended|권장|권고)\s*\)?", re.IGNORECASE)
SECRET = re.compile(
    r"(sk-[A-Za-z0-9_-]{8,}|gh[pousr]_[A-Za-z0-9]{8,}|AKIA[0-9A-Z]{12,}"
    r"|(?i:password|passwd|비밀번호|api[_-]?key|token|secret)\s*[=:]\s*\S+)"
)
HEADER = """# 결정 이력

사용자에게 물어 정한 것과 그 결과. 형식은 tuzi `go` 의 references/decisions.md.
항목을 지우거나 덮어쓰지 않는다 — 바꾸면 새 항목을 쓰고 옛 항목에 번복을 적는다.
"""


def enabled():
    for key in ("TUZI_DECISION_LOG", "CLAUDE_PLUGIN_OPTION_DECISION_LOG"):
        raw = os.environ.get(key, "").strip().lower()
        if raw:
            return raw not in ("0", "false", "off", "no")
    return True


def repo_root(cwd):
    try:
        out = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def target_file(root):
    existing = os.path.join(root, "DECISIONS.md")
    return existing if os.path.isfile(existing) else os.path.join(root, "docs", "decisions.md")


def clean(text):
    """한 줄로 줄이고 자유 입력에 섞인 비밀 값을 가린다."""
    return SECRET.sub("[가림]", " ".join(str(text).split()))


def unused_id(base, content):
    candidate, n = base, 1
    while f"## {candidate} " in content:
        n += 1
        candidate = f"{base}-{n}"
    return candidate


def entries(tool_input, answers, now, content):
    annotations = tool_input.get("annotations") or {}
    base = "D-" + now.strftime("%y%m%d-%H%M")
    for question in tool_input.get("questions") or []:
        text = question.get("question", "")
        answer = answers.get(text)
        if answer in (None, ""):  # 답하지 않고 닫은 질문은 결정이 아니다
            continue
        labels = [o.get("label", "") for o in question.get("options") or []]
        recommended = [RECOMMENDED.sub("", l).strip() for l in labels if RECOMMENDED.search(l)]
        note = (annotations.get(text) or {}).get("notes", "")
        adopted = RECOMMENDED.sub("", str(answer)).strip()
        decision_id = unused_id(base, content)
        title = clean(question.get("header") or text)[:40]
        block = (
            f"\n## {decision_id} {title}\n\n"
            f"- 결정일: {now:%Y-%m-%d}\n"
            f"- 질문: {clean(text)}\n"
            f"- 선택 항목: {clean(' / '.join(RECOMMENDED.sub('', l).strip() for l in labels)) or '없음'}\n"
            f"- 권고: {clean(', '.join(recommended)) or '없음'}\n"
            f"- 채택: {clean(adopted)}\n"
            "- 결정자: 사용자\n"
            f"- 이유: {clean(note) or '미기재'}\n"
            "- 결과: 미기재\n"
            "- 상태: 대기\n"
        )
        content += block
        yield block


def main():
    data = json.load(sys.stdin)
    if not enabled():
        return
    tool_input = data.get("tool_input") or {}
    response = data.get("tool_response")
    answers = (response.get("answers") if isinstance(response, dict) else None) or tool_input.get("answers") or {}
    if not answers:
        return
    root = repo_root(data.get("cwd") or os.getcwd())
    if not root:
        return
    path = target_file(root)
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
    except OSError:
        content = ""
    blocks = list(entries(tool_input, answers, datetime.datetime.now(), content))
    if not blocks:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        if not content:
            f.write(HEADER)
        f.write("".join(blocks))
    rel = os.path.relpath(path, root)
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": f"[tuzi] 결정 {len(blocks)}건을 {rel} 에 기록했다. 커밋할 때 이 파일을 함께 넣는다.",
        }
    }, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # 훅 오류로 세션을 멈추지 않는다
        print(f"tuzi decision_log: {e}", file=sys.stderr)
    sys.exit(0)
