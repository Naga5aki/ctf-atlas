"""Check maintenance coverage and its collection destinations (not website content)."""
import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def audit(cached=False):
    manifest = json.loads((ROOT / 'docs/forensics-web-coverage.json').read_text('utf-8'))
    records = manifest['records']
    errors = []
    keys = [(p['site'], p['id']) for p in records]
    if len(keys) != len(set(keys)):
        errors.append('重复页面记录')
    expected = {'Forensics-Wiki': 57, 'DigiForensics': 58, 'GoodLunatic': 1, 'Hello CTF': 1}
    if Counter(p['site'] for p in records) != expected:
        errors.append('指定目录或独立入口覆盖数量不符')
    allowed = {'curated', 'public-preview', 'non-knowledge', 'image-index',
               'link-index', 'tool-index', 'attachment-curated'}
    for p in records:
        if p['coverage'] not in allowed:
            errors.append(f'{p["id"]}: 未定义处理状态')
        if not p.get('themes') or not p.get('title'):
            errors.append(f'{p["id"]}: 缺少标题/范围说明')
        if p['site'] == 'DigiForensics' and (
                p['coverage'] != 'public-preview' or
                p['status'] != 'login-required' or not p.get('pending')):
            errors.append(f'{p["id"]}: 登录限制被误记为全文已完成')
        if p['coverage'] != 'non-knowledge' and not p.get('targets'):
            errors.append(f'{p["id"]}: 未映射正文/工具入口')
        for target in p['targets']:
            collection, id_ = target.split('/', 1)
            folder = {'knowledge': 'knowledge', 'tool': 'tools'}.get(collection)
            if folder is None:
                errors.append(f'{p["id"]}: 无效落点 {target}')
                continue
            path = ROOT / 'src/content' / folder / f'{id_}.md'
            if not path.is_file():
                errors.append(f'{p["id"]}: 落点不存在 {target}')
                continue
            fm = path.read_text('utf-8').split('---', 2)[1]
            if not re.search(r'''^module:[ \t]*(?:Forensics|"Forensics"|'Forensics')[ \t]*$''', fm, re.M):
                errors.append(f'{p["id"]}: 落点不属Forensics {target}')
            if not re.search(r'^topic: .+', fm, re.M):
                errors.append(f'{p["id"]}: 落点无主题 {target}')
        if cached:
            path = ROOT / '.work/forensics-web' / p['cache']
            if not path.is_file():
                errors.append(f'{p["id"]}: 读取缓存缺失')
                continue
            content = path.read_text('utf-8')
            digest = hashlib.sha256(content.encode('utf-8')).hexdigest()
            if p.get('sha256') and digest != p['sha256']:
                errors.append(f'{p["id"]}: 读取缓存哈希发生变化')
    if cached:
        catalog = json.loads((ROOT / '.work/forensics-web/pages.json').read_text('utf-8'))
        if set((p['site'], p['id']) for p in catalog) != set(
                key for key in keys if key[0] in ('Forensics-Wiki', 'DigiForensics')):
            errors.append('页面清单与覆盖记录不一致')
    standards = [p for p in records if p['site'] == 'DigiForensics' and
                 p['id'].startswith(('sf-', 'gb-'))]
    standard_text = (ROOT / 'src/content/knowledge/forensic-quality.md').read_text('utf-8')
    for p in standards:
        code = p['id'].upper().replace('SF-T-', 'SF/T ').replace('SF-Z-JD-', 'SF/Z JD').replace('GB-T-', 'GB/T ')
        # Chinese titles may include spacing; compare the stable standard number.
        if code.replace(' ', '') not in standard_text.replace(' ', ''):
            errors.append(f'{p["id"]}: 公开规范编号未入索引')
    if len(standards) != 50:
        errors.append('规范页清单数量不符')
    print(json.dumps({'pages': len(records), 'states': dict(Counter(p['coverage'] for p in records)),
                      'standards': len(standards), 'errors': errors}, ensure_ascii=False, indent=2))
    return errors


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cached', action='store_true', help='Also check private acquisition cache')
    raise SystemExit(bool(audit(parser.parse_args().cached)))
