#!/usr/bin/env python3
"""HTML 문서의 Mermaid 블록이 실제로 그림(SVG)으로 그려졌는지 헤드리스 브라우저로 확인한다.

  python3 check_mermaid.py <html 파일>...

종료 코드: 0 전부 그려짐(블록이 없어도 0) · 1 안 그려진 블록 있음 · 2 확인 못 함
브라우저는 CHROME_PATH, 설치된 Chrome·Chromium, Playwright 캐시 순으로 찾는다.
외부 패키지를 쓰지 않는다. 없으면 설치하지 않고 2 로 끝낸다 — 그때 보고에 미확인이라고 적는다.
"""
import glob
import html.parser
import os
import shutil
import subprocess
import sys
import tempfile

WAIT_MS = 15000
TIMEOUT_SEC = 60
CANDIDATES = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
)
COMMANDS = ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome")
PLAYWRIGHT_GLOBS = (
    "~/Library/Caches/ms-playwright/chromium_headless_shell-*/*/chrome-headless-shell",
    "~/.cache/ms-playwright/chromium_headless_shell-*/*/chrome-headless-shell",
    "~/.cache/ms-playwright/chromium-*/chrome-linux*/chrome",
)


def find_browser():
    env = os.environ.get("CHROME_PATH", "").strip()
    if env:
        return env if os.access(env, os.X_OK) else None
    for path in CANDIDATES:
        if os.access(path, os.X_OK):
            return path
    for name in COMMANDS:
        path = shutil.which(name)
        if path:
            return path
    for pattern in PLAYWRIGHT_GLOBS:
        found = sorted(glob.glob(os.path.expanduser(pattern)), reverse=True)
        if found:
            return found[0]
    return None


def rendered_dom(browser, path):
    with tempfile.TemporaryDirectory() as profile:  # 사용자가 띄운 브라우저 프로필과 겹치지 않게
        result = subprocess.run(
            [
                browser,
                "--headless",
                "--disable-gpu",
                "--no-first-run",
                f"--user-data-dir={profile}",
                f"--virtual-time-budget={WAIT_MS}",
                "--dump-dom",
                "file://" + os.path.abspath(path),
            ],
            capture_output=True,
            text=True,
            errors="replace",
            timeout=TIMEOUT_SEC,
        )
    if result.returncode != 0 or "<html" not in result.stdout.lower():
        raise RuntimeError(f"브라우저 종료 코드 {result.returncode}: {result.stderr.strip()[:200]}")
    return result.stdout


class Blocks(html.parser.HTMLParser):
    """class 에 mermaid 가 든 요소마다 SVG 유무와 첫 줄을 모은다."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks = []
        self.current = None
        self.tag = None
        self.depth = 0
        self.error_svgs = 0
        self.svg_depth = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "svg" and attrs.get("aria-roledescription") == "error":
            self.error_svgs += 1
        if self.current is not None:
            if tag == self.tag:
                self.depth += 1
            if tag == "svg":
                self.svg_depth += 1
                if attrs.get("aria-roledescription") != "error":
                    self.current["svg"] = True
            return
        classes = (attrs.get("class") or "").split()
        if "mermaid" in classes or "language-mermaid" in classes:
            self.current = {"svg": False, "text": ""}
            self.tag = tag
            self.depth = 1

    def handle_startendtag(self, tag, attrs):
        if self.current is not None and tag == "svg":
            self.current["svg"] = True

    def handle_endtag(self, tag):
        if tag == "svg" and self.svg_depth:
            self.svg_depth -= 1
        if self.current is not None and tag == self.tag:
            self.depth -= 1
            if self.depth == 0:
                self.blocks.append(self.current)
                self.current = None

    def handle_data(self, data):
        if self.current is not None and not self.svg_depth:
            self.current["text"] += data


def check(browser, path):
    """(그려진 수, 안 그려진 첫 줄 목록, 오류 그림 수)"""
    parser = Blocks()
    parser.feed(rendered_dom(browser, path))
    good = sum(1 for b in parser.blocks if b["svg"])
    bad = []
    for block in parser.blocks:
        if not block["svg"]:
            lines = [line.strip() for line in block["text"].splitlines() if line.strip()]
            bad.append(lines[0][:60] if lines else "(빈 블록)")
    return good, bad, parser.error_svgs


def main(paths):
    if not paths:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    browser = find_browser()
    if not browser:
        print("확인 못 함: 헤드리스 브라우저를 찾지 못했다 (CHROME_PATH 로 지정할 수 있다)")
        return 2
    code = 0
    for path in paths:
        if not os.path.isfile(path):
            print(f"확인 못 함: {path} — 파일이 없다")
            code = max(code, 2)
            continue
        try:
            good, bad, errors = check(browser, path)
        except (RuntimeError, OSError, subprocess.SubprocessError) as e:
            print(f"확인 못 함: {path} — {e}")
            code = max(code, 2)
            continue
        total = good + len(bad)
        failed = bad or errors
        print(f"{'실패' if failed else '통과'}: {path} — 블록 {total}개 중 {good}개 그려짐")
        for line in bad:
            print(f"  안 그려짐: {line}")
        if errors:
            print(f"  문법 오류 그림: {errors}개")
        if failed:
            code = 1 if code != 2 else 2
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
