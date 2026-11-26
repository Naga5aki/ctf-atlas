import importlib.util
import json
from pathlib import Path
import plistlib
import re
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CORE = 'forensic-ios-forensics'
TOOLS = 'forensic-ios-tools'

class IOSContentTests(unittest.TestCase):
    def test_provenance_is_durable_and_exception_is_narrow(self):
        registry = json.loads((ROOT/'src/data/forensics-supplements.json').read_text('utf-8'))
        for ident in (CORE, TOOLS):
            body = (ROOT/f'src/content-curation/{ident}.md').read_text('utf-8')
            urls = set(re.findall(r'\]\((https?://[^)]+)\)',body))
            sources = [s for s in registry['webSources'] if ident in s['articleIds']]
            self.assertEqual(urls, {s['url'] for s in sources})
            generated = (ROOT/f'src/content/knowledge/{ident}.md').read_text('utf-8').split('---', 2)[1]
            for source in sources: self.assertIn(source['id'], generated)
        audit = ROOT/'scripts/audit_site.py'
        spec = importlib.util.spec_from_file_location('ios_audit_contract', audit)
        helper = importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
        self.assertEqual(helper.CONTEST_PROVENANCE_PAGES, {f'/knowledge/{CORE}/index.html', '/knowledge/forensic-android-forensics/index.html'})
        self.assertIn('源文件', helper.FORBIDDEN)
        self.assertIn('数证杯', helper.FORBIDDEN)

    def test_ios_cluster_is_inside_mobile_and_retains_backup(self):
        taxonomy = (ROOT/'src/data/forensics-taxonomy.ts').read_text('utf-8')
        mobile = taxonomy.split("id: 'mobile'", 1)[1].split("id: 'network'", 1)[0]
        self.assertIn("name: 'iOS 取证'", mobile)
        self.assertIn("'iOS 与备份'", mobile)
        registry = json.loads((ROOT/'src/data/forensics-supplements.json').read_text('utf-8'))
        for ident in (CORE, TOOLS):
            article = next(a for a in registry['articles'] if a['id'] == ident)
            self.assertEqual(article['track'], '手机取证')
            body = (ROOT/f'src/content-curation/{ident}.md').read_text('utf-8').strip()
            rendered = (ROOT/f'src/content/knowledge/{ident}.md').read_text('utf-8').split('---', 2)[2].strip()
            self.assertEqual(body, rendered)
        old = (ROOT/'src/content-curation/forensic-ios-backup.md').read_text('utf-8')
        for term in ('Manifest.db', 'domain', 'relativePath', 'fileID', 'sms.db-wal', 'SHA1', 'DFU'):
            self.assertIn(term, old)

    def test_real_contests_limits_and_tool_steps(self):
        core = (ROOT/f'src/content-curation/{CORE}.md').read_text('utf-8')
        tools = (ROOT/f'src/content-curation/{TOOLS}.md').read_text('utf-8')
        for term in ('Magnet', '2021', '2022', '2023', '2024', '数证杯', 'ZRTCLLOCATIONMO',
                     'cloud_sync_stores', 'SUM(ZENDDATE-ZSTARTDATE)', '未复跑', '新增', '修订', '合并', '去重',
                     'BFU', 'AFU', 'Secure Enclave', 'App Group', 'NSKeyedArchiver', 'Biome'):
            self.assertIn(term, core)
        for term in ('2026.4.4', 'Plist_Editor', 'VOWSoft', 'View → Read only', 'Ctrl+O', 'Ctrl+Tab',
                     '-t itunes', '--itunes_password', '--html_row_limit', '-p', '-c', '--keychain',
                     '不等于', '未执行', 'TSV', 'LAVA', '构造样本', 'SystemVersion.plist'):
            self.assertIn(term, tools)
        self.assertNotIn('源文件', core + tools)
        self.assertNotIn('-t 12345', tools)

    def test_read_only_plist_inspector_preserves_types_and_uid(self):
        path = ROOT/'public/practice/ios_inspect.py'
        spec = importlib.util.spec_from_file_location('ios_inspect', path)
        helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(helper)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'sample.plist'
            p.write_bytes(plistlib.dumps({'a': True, 'b': 1, 'data': b'abc', 'ref': plistlib.UID(2)}, fmt=plistlib.FMT_BINARY))
            before = p.read_bytes()
            result = helper.inspect_plist(p)
            self.assertEqual(result['value']['value']['a']['type'], 'bool')
            self.assertEqual(result['value']['value']['b']['type'], 'int')
            self.assertEqual(result['value']['value']['ref'], {'type':'UID', 'value':2})
            self.assertEqual(p.read_bytes(), before)
            p.write_bytes(b'not a plist')
            with self.assertRaises(plistlib.InvalidFileException):
                helper.inspect_plist(p)

    def test_explicit_epoch_and_unit_are_not_auto_guessed(self):
        path = ROOT/'public/practice/ios_inspect.py'
        spec = importlib.util.spec_from_file_location('ios_time_inspect', path)
        helper = importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
        self.assertEqual(helper.convert_time('0','apple','s','UTC')['utc'], '2001-01-01T00:00:00+00:00')
        self.assertEqual(helper.convert_time('1000000000','apple','ns','UTC')['utc'], '2001-01-01T00:00:01+00:00')
        self.assertEqual(helper.convert_time('1000','unix','ms','UTC')['utc'], '1970-01-01T00:00:01+00:00')
        for invalid in ('NaN','Infinity','not-a-number'):
            with self.assertRaises(ValueError): helper.convert_time(invalid,'unix','s','UTC')

if __name__ == '__main__':
    unittest.main()
