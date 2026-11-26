"""Read-only Chinese writing linter for CTF Atlas content pages.

Checks content Markdown (knowledge, curation, tools, writeups) against the
project's writing standard and terminology table. It never edits files.

Default rules are high-confidence only, so a run over the existing corpus is
actionable rather than noisy:

    placeholder          正文占位词（此处省略、过程略……）
    code-placeholder     代码块里的省略号或占位符
    meta                 元叙述（这页把……）
    term                 术语错误拼写（BurpSuite、SQLMap……）
    h1                   正文出现一级标题（标题由 frontmatter 生成）

--wide adds heuristics that need human review:

    vague                空转表达（进行检查、相关命令……）
    missing-explanation  代码块后没有说明文字
    punct                中文句子里用半角标点
    heading-jump         标题层级跳级

Exit status is 0 in report mode. Use --strict to fail when anything is found.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIRS = [
    'src/content-curation',
    'src/content/knowledge',
    'src/content/tools',
    'src/content/writeups',
]

HIGH_RULES = ('placeholder', 'code-placeholder', 'meta', 'term', 'h1')
WIDE_RULES = HIGH_RULES + ('vague', 'missing-explanation', 'punct', 'heading-jump')

PLACEHOLDER_WORDS = (
    '此处省略', '此处略', '不再赘述', '过程略', '步骤略', '命令略',
    '细节略', '略过', '略去',
)
DOTS_PATTERNS = (
    re.compile(r'^\.{3,}$'),
    re.compile(r'^…+$'),
    re.compile(r'^#\s*(\.{3,}|…+)$'),
)
EXPLICIT_PLACEHOLDERS = (
    re.compile(r'<payload>', re.I),
    re.compile(r'<[^>]*替换[^>]*>'),
    re.compile(r'<填入[^>]*>'),
)
# Meta prose is "this page does X", not every mention of 本页. Keep the verb.
META_PATTERN = re.compile(r'(这页|本页)(把|将|分为|分成|介绍|说明|讲)|本文将|本节将|下面介绍|接下来介绍')
VAGUE_WORDS = (
    '进行检查', '进行验证', '进行配置', '进行测试', '进行排查',
    '相关操作', '执行相关命令', '使用相关工具', '配置好后继续',
)
# Wrong spelling -> expected spelling. Keep in sync with TERMINOLOGY.md.
TERM_FIXES = (
    ('BurpSuite', 'Burp Suite'),
    ('SQLMap', 'sqlmap'),
    ('SQLmap', 'sqlmap'),
    ('Powershell', 'PowerShell'),
    ('Nodejs', 'Node.js'),
    ('Mysql', 'MySQL'),
    ('thinkphp', 'ThinkPHP'),
    ('Volatility2', 'Volatility 2'),
    ('K8S', 'k8s 或 Kubernetes'),
)
HALF_PUNCT = re.compile(r'[\u4e00-\u9fff][,;:?!]')
HALF_PERIOD = re.compile(r'[\u4e00-\u9fff]\.(?=[\u4e00-\u9fff]|$)')
HEADING = re.compile(r'^(#{1,6})\s+(.*)$')


def strip_inline(text: str) -> str:
    """Remove inline code, link targets and URLs before prose checks."""
    text = re.sub(r'`[^`]*`', '', text)
    text = re.sub(r'\]\([^)]*\)', ']', text)
    text = re.sub(r'https?://\S+', '', text)
    return text


def iter_pages(paths, root: Path):
    for raw in paths:
        path = (root / raw) if not Path(raw).is_absolute() else Path(raw)
        if path.is_dir():
            for page in sorted(path.rglob('*.md')):
                yield page
        elif path.is_file():
            yield path


def check_code_block(code_lines, add):
    """Flag a block that is only dots, or that carries an explicit placeholder.

    A dots line inside a block with several real commands is a range shorthand,
    not a missing step, so only a near-empty block counts as placeholder prose.
    """
    real = [(index, text) for index, text in code_lines if text]
    if not real:
        return
    dots = [(index, text) for index, text in real if any(p.match(text) for p in DOTS_PATTERNS)]
    others = [pair for pair in real if pair not in dots]
    if dots and len(others) <= 1:
        add(dots[0][0], 'code-placeholder', '代码块几乎只有省略号，没有可执行内容', dots[0][1])
    for index, text in real:
        for pattern in EXPLICIT_PLACEHOLDERS:
            if pattern.search(text):
                add(index, 'code-placeholder', '代码块里出现占位符', text)
                break


def lint_page(page: Path, rules, root: Path) -> list[dict]:
    issues: list[dict] = []
    text = page.read_text('utf-8')
    lines = text.splitlines()
    try:
        display = str(page.relative_to(root))
    except ValueError:
        display = str(page)

    in_frontmatter = False
    frontmatter_done = False
    in_code = False
    code_lines: list[tuple[int, str]] = []
    last_heading = 0

    def add(lineno, rule, message, snippet):
        issues.append({
            'path': display,
            'line': lineno,
            'rule': rule,
            'message': message,
            'text': snippet.strip()[:160],
        })

    for index, line in enumerate(lines, start=1):
        stripped = line.strip()

        # Frontmatter: only at the very beginning of the file.
        if index <= 2 and stripped == '---' and not frontmatter_done:
            in_frontmatter = True
            continue
        if in_frontmatter:
            if stripped == '---':
                in_frontmatter = False
                frontmatter_done = True
            continue

        # Fenced code blocks.
        if stripped.startswith('```') or stripped.startswith('~~~'):
            if in_code:
                in_code = False
                if 'code-placeholder' in rules:
                    check_code_block(code_lines, add)
                if 'missing-explanation' in rules:
                    nxt = ''
                    for probe in lines[index:index + 3]:
                        candidate = probe.strip()
                        if candidate:
                            nxt = candidate
                            break
                    if nxt == '' or nxt.startswith('```') or nxt.startswith('~~~') or HEADING.match(nxt):
                        add(index, 'missing-explanation', '代码块后没有说明文字', stripped)
                code_lines = []
            else:
                in_code = True
                code_lines = []
            continue

        if in_code:
            code_lines.append((index, stripped))
            continue

        heading = HEADING.match(stripped)
        if heading:
            level = len(heading.group(1))
            if level == 1 and 'h1' in rules:
                add(index, 'h1', '正文一级标题由 frontmatter 生成，正文不再写 #', stripped)
            if 'heading-jump' in rules and last_heading and level > last_heading + 1:
                add(index, 'heading-jump', f'标题从 h{last_heading} 跳到 h{level}', stripped)
            last_heading = level
            continue

        prose = strip_inline(line)
        if not prose.strip():
            continue

        if 'placeholder' in rules:
            for word in PLACEHOLDER_WORDS:
                if word in prose:
                    add(index, 'placeholder', f'正文占位词：{word}', prose)
                    break
        if 'meta' in rules:
            match = META_PATTERN.search(prose)
            if match:
                add(index, 'meta', f'元叙述：{match.group(0)}', prose)
        if 'term' in rules:
            for wrong, right in TERM_FIXES:
                if wrong in prose:
                    add(index, 'term', f'{wrong} 应写作 {right}', prose)
        if 'vague' in rules:
            for word in VAGUE_WORDS:
                if word in prose:
                    add(index, 'vague', f'空转表达：{word}', prose)
                    break
        if 'punct' in rules:
            if HALF_PUNCT.search(prose) or HALF_PERIOD.search(prose):
                add(index, 'punct', '中文句子里用了半角标点', prose)

    return issues


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='CTF Atlas 中文写作 lint（只读）')
    parser.add_argument('--root', default=str(ROOT), help='工程根目录')
    parser.add_argument('--paths', nargs='*', help='要检查的文件或目录，默认四个内容目录')
    parser.add_argument('--wide', action='store_true', help='启用需要人工复核的启发式规则')
    parser.add_argument('--rules', nargs='*', help='只启用指定规则名')
    parser.add_argument('--strict', action='store_true', help='有命中时以 1 退出')
    parser.add_argument('--json', action='store_true', help='输出 JSON')
    parser.add_argument('--max', type=int, default=200, help='最多打印的条目数，0 表示全部')
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    rules = set(args.rules) if args.rules else set(WIDE_RULES if args.wide else HIGH_RULES)
    unknown = rules - set(WIDE_RULES)
    if unknown:
        parser.error(f'未知规则：{", ".join(sorted(unknown))}')

    paths = args.paths or [str(root / part) for part in DEFAULT_DIRS]
    pages = list(iter_pages(paths, root))
    issues = []
    for page in pages:
        issues.extend(lint_page(page, rules, root))

    counter = Counter(item['rule'] for item in issues)
    by_file = Counter(item['path'] for item in issues)

    if args.json:
        print(json.dumps({
            'root': str(root),
            'files': len(pages),
            'total': len(issues),
            'by_rule': dict(sorted(counter.items())),
            'by_file': dict(sorted(by_file.items())),
            'issues': issues,
        }, ensure_ascii=False, indent=2))
    else:
        limit = args.max if args.max > 0 else len(issues)
        for item in issues[:limit]:
            print(f"{item['path']}:{item['line']}: [{item['rule']}] {item['message']}")
            if item['text']:
                print(f"    {item['text']}")
        if len(issues) > limit:
            print(f"... 另有 {len(issues) - limit} 条未显示，用 --max 0 查看全部")
        print()
        print(f'files={len(pages)}  issues={len(issues)}')
        for rule in sorted(counter):
            print(f'  {rule:<20} {counter[rule]}')
        if by_file:
            print('top files:')
            for path, count in by_file.most_common(10):
                print(f'  {count:>4}  {path}')

    if args.strict and issues:
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
