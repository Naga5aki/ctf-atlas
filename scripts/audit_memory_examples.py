"""Check documented CLI names and shell syntax against the pinned catalogs.

This does not load an evidence image or validate a forensic conclusion.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import shlex
import shutil
import subprocess

SITE = Path(__file__).resolve().parents[1]


def flag_names(option, version):
    if version == 3:
        return set(option.get('options', [])) | ({option['cliOption']} if option.get('cliOption') else set())
    return {option[k] for k in ('long_option', 'short_option') if option.get(k)}


def audit():
    catalogs = json.loads((SITE / 'src/data/volatility-catalog.json').read_text(encoding='utf-8'))
    versions = {n: catalogs[f'volatility{n}'] for n in (2, 3)}
    plugins = {n: {p['name']: p for p in c['plugins']} for n, c in versions.items()}
    globals_ = {n: set().union(*(flag_names(o, n) for o in c.get('globalOptions', c.get('global_options', [])))) for n, c in versions.items()}
    bash = shutil.which('bash') or ('C:/Program Files/Git/bin/bash.exe' if Path('C:/Program Files/Git/bin/bash.exe').exists() else None)
    failures, commands, blocks = [], [], 0
    for path in sorted((SITE / 'src/content-curation').glob('forensic-memory*.md')):
        body = path.read_text(encoding='utf-8')
        for block in re.findall(r'^```bash\s*\n(.*?)^```\s*$', body, re.M | re.S):
            blocks += 1
            if bash:
                checked = subprocess.run([bash, '-n'], input=block, text=True, encoding='utf-8', capture_output=True)
                if checked.returncode:
                    failures.append({'page': path.stem, 'shell': checked.stderr.strip()})
            else:
                failures.append({'page': path.stem, 'shell': 'bash unavailable; syntax check not performed'})
            for line in block.replace('\\\n', ' ').splitlines():
                if line.lstrip().startswith('#'):
                    continue
                try:
                    tokens = shlex.split(line, comments=True)
                except ValueError as error:
                    failures.append({'page': path.stem, 'parse': str(error)})
                    continue
                if not tokens:
                    continue
                if tokens[0] == 'volatility':
                    version = 2
                elif tokens[0] in ('python2', 'python3') and len(tokens) > 1 and tokens[1].endswith('/vol.py') or tokens[:2] in (['python2', 'vol.py'], ['python3', 'vol.py']):
                    version = 2 if tokens[0] == 'python2' else 3
                else:
                    continue
                matches = [p for p in plugins[version] if p in tokens]
                if version == 3 and not matches:
                    abbreviated = [t for t in tokens if any(t in p for p in plugins[version]) and not t.startswith('-') and not t.endswith('vol.py') and t != 'python3']
                    for token in abbreviated:
                        resolved = [p for p in plugins[version] if token in p]
                        if len(resolved) == 1:
                            matches.append(resolved[0])
                if len(matches) > 1:
                    failures.append({'page': path.stem, 'command': line, 'problem': 'multiple plugin names'})
                    continue
                if not matches:
                    if not any(x in tokens for x in ('--help', '-h', '--info')):
                        failures.append({'page': path.stem, 'command': line, 'problem': 'no unique pinned plugin'})
                    continue
                name = matches[0]
                item = plugins[version][name]
                options = item.get('parameters', item.get('options', []))
                allowed = globals_[version] | set().union(*(flag_names(o, version) for o in options), set())
                used = {t.split('=', 1)[0] for t in tokens if t.startswith('-') and t not in ('-',)}
                unknown = used - allowed
                if unknown:
                    failures.append({'page': path.stem, 'plugin': name, 'unknownFlags': sorted(unknown)})
                commands.append({'page': path.stem, 'version': version, 'plugin': name, 'flags': sorted(used)})
    return {'shellBlocks': blocks, 'documentedVolatilityCommands': len(commands), 'commands': commands,
            'failures': failures, 'scope': 'pinned CLI names/options and shell syntax only; no evidence replay'}


if __name__ == '__main__':
    result = audit()
    output = SITE / '.work/memory-curation/example-verification.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'commands'}, ensure_ascii=False, indent=2))
    raise SystemExit(bool(result['failures']))
