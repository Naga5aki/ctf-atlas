"""Read-only Cursor workspace/context contract and curated-body consistency check."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = 'CTF-Atlas-知识库管理.code-workspace'
RULES = ['00-ctf-atlas-project.mdc', '10-practical-knowledge-style.mdc', '20-verification-and-handoff.mdc']
DOCS = ['START-HERE.md', 'WRITING-STANDARD.md', 'CURRENT-STATE.md', 'WORK-LOG.md',
        'CURSOR-START-PROMPT.md', 'examples/website-reconstruction-approved.md']


def check(root=ROOT):
    errors = []
    def require(condition, message):
        if not condition:
            errors.append(message)
    needed = [WORKSPACE, 'AGENTS.md', '.cursorindexingignore'] + [f'.cursor/rules/{p}' for p in RULES] + [f'docs/maintenance/{p}' for p in DOCS]
    for rel in needed:
        require((root / rel).is_file(), f'Missing: {rel}')
    if errors:
        return {'ok': False, 'errors': errors}
    tasks = []
    try:
        workspace = json.loads((root / WORKSPACE).read_text('utf-8'))
        folders = workspace.get('folders', [])
        require(len(folders) == 1 and folders[0].get('path') == '.', 'Workspace must point to the one existing project root')
        tasks = workspace.get('tasks', {}).get('tasks', [])
        require(len(tasks) >= 8, 'Expected manual validation and preview tasks')
        for task in tasks:
            require(task.get('runOptions', {}).get('runOn') != 'folderOpen', 'Tasks must not auto-run on workspace opening')
            require(task.get('options', {}).get('cwd') == '${workspaceFolder}', 'Task cwd must be the project root')
        require(workspace.get('settings', {}).get('files.autoSave') == 'off', 'Keep automatic writes disabled in this workspace')
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        errors.append(f'Invalid workspace: {exc}')
    for name in RULES:
        rule = (root / '.cursor/rules' / name).read_text('utf-8')
        require(rule.startswith('---\n'), f'{name}: missing MDC frontmatter')
        segments = rule.split('---', 2)
        frontmatter = segments[1] if len(segments) == 3 else ''
        require(bool(re.search(r'^alwaysApply: true$', frontmatter, re.M)), f'{name}: not always applied')
        require(len(rule.splitlines()) < 500, f'{name}: rule too long')
    style = (root / '.cursor/rules/10-practical-knowledge-style.mdc').read_text('utf-8')
    for token in ['语义查重', '考点', '参数', '交叉引用', '副本', 'salt', '失败', '版本']:
        require(token in style, f'Style contract missing {token}')
    pages = list((root / 'src/content/knowledge').glob('*.md'))
    require(bool(pages), 'No knowledge source pages found in this workspace')
    forensic, server, mismatched = 0, 0, []
    for page in pages:
        parts = page.read_text('utf-8').split('---', 2)
        if len(parts) != 3:
            errors.append(f'Missing frontmatter: {page.name}')
            continue
        header, body = parts[1:]
        if re.search(r'^module:\s*[\"\']?Forensics[\"\']?\s*$', header, re.M):
            forensic += 1
            curated = root / 'src/content-curation' / page.name
            if not curated.is_file() or curated.read_text('utf-8').strip() != body.strip():
                mismatched.append(page.name)
        if re.search(r'^track:\s*[\"\']?服务器取证[\"\']?\s*$', header, re.M):
            server += 1
    require(not mismatched, 'Curation/generated body mismatch: ' + ', '.join(mismatched))
    require(forensic > 0 and server > 0, 'Expected existing Forensics and server content')
    return {'ok': not errors, 'workspace': WORKSPACE, 'always_rules': len(RULES), 'manual_tasks': len(tasks),
            'knowledge_pages': len(pages), 'forensics_pages': forensic, 'server_pages': server,
            'curation_mismatches': mismatched, 'files_modified': 0, 'errors': errors}


if __name__ == '__main__':
    result = check()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result['ok'] else 1)
