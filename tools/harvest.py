#!/usr/bin/env python3
"""세션 전사에서 사람이 반복한 지시를 뽑는다.

docs/evidence.md 1장의 표를 만든 스크립트다. 다른 기계·다른 계정의 전사에도 그대로 돈다.

    python3 tools/harvest.py ~/.claude/projects
    python3 tools/harvest.py /경로/projects --min-count 3 --max-len 60
    python3 tools/harvest.py ~/.claude/projects /프로필2/projects --since 2026-10-05   # 여러 경로·날짜 이후만

핵심은 집계가 아니라 **주입 턴 걸러내기**다. 전사의 type:"user" 에는 오케스트레이터
프리앰블·검증 에이전트 디스패치·슬래시 커맨드 출력이 섞여 있다. 걸러내지 않으면
기계 문장이 상위를 다 차지한다 — 첫 집계에서 '보고-전후대조 357건' 이 나왔는데
전부 주입이었다. 필터를 늘릴 일이 있으면 INJECTED 에 접두사를 추가한다.
"""

import argparse
import collections
import json
import os
import re
import sys

# 사람이 쓴 것이 아닌 user 턴의 표식. 접두 또는 앞 80자 안에 있으면 버린다.
INJECTED = (
    '# 규칙', '저장소 루트:', 'export PATH', '너는 ', '## TASK', '<task>', 'PREAMBLE',
    '# MARK ', 'orca orchestration', 'Caveat:', '<command-name>', '<local-command',
    '## CONV-', 'pasted_content', '# 검증', '# 지시', 'You are ', '# 보고서',
    '아래는 사건 목록', '<system-reminder>', '[Request interrupted',
)

# 사람이 썼지만 집계를 흐리는 것. 이미지 붙여넣기 경로와 제품 도메인의 '에이전트'다.
# 이것을 걸러내지 않으면 오케스트레이션 축이 81건으로 부풀고 표본이 전부 이미지 경로가 된다.
NOISE = ('orca-paste', '[Image', 'moai-agent', 'mark agent', 'mark-agent',
         'device-mock', 'mock-device')
PRODUCT_AGENT = re.compile(r'(moai|mark|a2a|device)[- ]?agent', re.I)

# 주제 → 그 주제를 드러내는 표현. 취합할 때 여기를 늘린다.
# 순서가 의미를 갖는다 — 첫 일치 주제로만 계상하므로 좁은 주제를 위에 둔다.
THEMES = {
    '오케스트레이션 구성':  ['오케스트레이션 모드', '오케스트레이션 구성', '오케스트레이션 환경',
                             '팀 구성', '모드를 구성', '워크트리', 'worktree', '서브 에이전트 모드'],
    '워커 위임·상태':       ['워커에 맡', '워커에게', '워커가', '워커들', '워커 보고', 'dispatch',
                             '디스패치', '위임', '코디네이터', '코디에이터', '완료 통지',
                             'task로 돌리', '멀티쓰레드'],
    '이어받아 진행':        ['진행해', '진행시켜', '계속해', '계속 진행', '이어서', '이어 진행', '다음 진행'],
    '실물 확인':            ['확인해', '확인할', '띄워', '스크린샷', '캡처', 'e2e', '돌려 봐', '실행해 봐'],
    '보고 규율':            ['보고', '대조', '정리해', '뭐가 달라', '무엇이 달라'],
    '커밋·배포':            ['커밋', 'push', 'pr 올', 'merge', '배포'],
    '근본 원인':            ['근본 원인', '왜 그런', '또 같은', '다시 해'],
    '과잉 금지·토큰':       ['토큰', '무한 반복', '그만', '너무 오래', '빨리', '간단히', '범위를 좁'],
    '자율 수행':            ['알아서', '묻지 말고', '확인 받지', '되묻지'],
    '문서·산출물':          ['문서로', '워드', 'pdf', 'ppt', '엑셀', '반영해', '로드맵', '인수인계'],
    '폰트·서식':            ['Pretendard', '폰트', '레이아웃'],
    '임의 설치 금지':       ['임의로 설치', '설치하지', '마음대로'],
}


def human_messages(root, max_len, since=''):
    """전사를 훑어 사람이 쓴 것으로 판정된 메시지를 흘려보낸다.

    since 는 'YYYY-MM-DD'. 주면 timestamp 가 그 날짜 이전인 턴(과 timestamp 가 없는 턴)을 버린다.
    """
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if not fn.endswith('.jsonl'):
                continue
            path = os.path.join(dirpath, fn)
            try:
                with open(path, errors='ignore') as f:
                    for line in f:
                        if '"user"' not in line:
                            continue
                        try:
                            rec = json.loads(line)
                        except Exception:
                            continue
                        if rec.get('type') != 'user':
                            continue
                        if since and (rec.get('timestamp') or '') < since:
                            continue
                        content = (rec.get('message') or {}).get('content')
                        if isinstance(content, list):
                            text = ' '.join(
                                b.get('text', '') for b in content
                                if isinstance(b, dict) and b.get('type') == 'text'
                            )
                        elif isinstance(content, str):
                            text = content
                        else:
                            continue
                        t = text.strip().replace('\n', ' ')
                        if not t or len(t) > max_len or t.startswith('<'):
                            continue
                        if t.startswith(INJECTED) or any(k in t[:80] for k in INJECTED):
                            continue
                        if t.startswith('/'):          # 슬래시 커맨드는 지시가 아니다
                            continue
                        if len(t) <= 2 or t.isdigit():  # 메뉴 선택('1', 'A')은 지시가 아니다
                            continue
                        if any(n in t for n in NOISE) or PRODUCT_AGENT.search(t):
                            continue
                        yield t
            except Exception:
                continue


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('roots', nargs='*', default=[os.path.expanduser('~/.claude/projects')],
                    help='전사 폴더. 여럿이면 합쳐 센다 (프로필이 둘 이상인 기계)')
    ap.add_argument('--since', default='', help='이 날짜(YYYY-MM-DD) 이후 턴만 센다')
    ap.add_argument('--min-count', type=int, default=2, help='반복 지시로 볼 최소 횟수')
    ap.add_argument('--max-len', type=int, default=500, help='이보다 길면 주입으로 본다')
    ap.add_argument('--short-len', type=int, default=40, help='"짧은 지시" 기준 길이')
    args = ap.parse_args()

    for root in args.roots:
        if not os.path.isdir(root):
            sys.exit('경로가 없다: %s' % root)
    if args.since and not re.fullmatch(r'\d{4}-\d{2}-\d{2}', args.since):
        sys.exit('--since 는 YYYY-MM-DD 형식이다: %s' % args.since)

    # 프로필 폴더가 다른 폴더를 가리키는 링크인 경우가 있다(orca 프로필 → ~/.claude/projects). 실제 경로로 한 번만 센다
    roots = list(dict.fromkeys(os.path.realpath(r) for r in args.roots))
    msgs = [m for root in roots for m in human_messages(root, args.max_len, args.since)]
    if not msgs:
        sys.exit('사람이 쓴 메시지를 찾지 못했다. INJECTED 필터가 과한지 본다.')

    print('# 수집 결과 — %s%s' % (', '.join(roots), ' (%s 이후)' % args.since if args.since else ''))
    print()
    print('사람이 쓴 것으로 판정된 메시지: **%d건**' % len(msgs))
    print()

    print('## 1. 그대로 반복된 짧은 지시 (%d자 이하, %d회 이상)' % (args.short_len, args.min_count))
    print()
    print('| 지시 | 횟수 |')
    print('| --- | --- |')
    short = [m for m in msgs if len(m) <= args.short_len]
    for text, n in collections.Counter(short).most_common():
        if n < args.min_count:
            break
        print('| `%s` | %d |' % (text.replace('|', '\\|'), n))
    print()

    print('## 2. 주제별 빈도')
    print()
    print('| 주제 | 건수 | 비율 |')
    print('| --- | --- | --- |')
    counts = collections.Counter()
    samples = collections.defaultdict(list)
    for m in msgs:
        for theme, kws in THEMES.items():
            if any(k in m for k in kws):
                counts[theme] += 1
                if len(samples[theme]) < 5 and len(m) < 160:
                    samples[theme].append(m)
                break  # 첫 일치 주제로만 센다 — 중복 계상 방지
    for theme, n in counts.most_common():
        print('| %s | %d | %.1f%% |' % (theme, n, 100 * n / len(msgs)))
    print()

    print('## 3. 주제별 표본')
    print()
    for theme, _ in counts.most_common():
        print('### %s' % theme)
        for s in samples[theme]:
            print('- %s' % s)
        print()


if __name__ == '__main__':
    main()
