"""List entries in docs/server-forensics-review-20261006.json whose recorded SHA-256
no longer matches the file on disk. Read-only: prints the stale paths and exits 0.

Usage (from the project root):
    py -V:3.12 -X utf8 .dsh/skills/ctf-atlas-verify/scripts/hash_mismatches.py
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

# ASCII only in this file: Windows PowerShell 5.1 reads BOM-less scripts as ANSI.
REPORT_REL = 'docs/server-forensics-review-20261006.json'


def find_root(start: pathlib.Path) -> pathlib.Path:
    """Walk up to the directory that holds both package.json and .git."""
    for candidate in [start, *start.parents]:
        if (candidate / 'package.json').is_file() and (candidate / '.git').exists():
            return candidate
    raise SystemExit('project root not found from ' + str(start))


def main() -> int:
    root = find_root(pathlib.Path(__file__).resolve().parent)
    report_path = root / REPORT_REL
    if not report_path.is_file():
        print('report not found:', report_path)
        return 2
    entries = json.loads(report_path.read_text(encoding='utf-8'))['unaffected_hashes']
    stale = []
    for path, expected in entries.items():
        target = root / path
        actual = hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else 'MISSING'
        if actual != expected:
            stale.append((path, actual, expected))
    print('entries', len(entries), 'stale', len(stale))
    for path, actual, expected in stale:
        print('  MISMATCH', path)
        print('      on disk  ', actual)
        print('      recorded ', expected)
    return 0


if __name__ == '__main__':
    sys.exit(main())
