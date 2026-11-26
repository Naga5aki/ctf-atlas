import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sqlite3
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CORE, STORAGE, TOOLS = 'forensic-android-forensics', 'forensic-android-storage', 'forensic-android-tools'


def helper():
    spec = importlib.util.spec_from_file_location('android_inspect', ROOT/'public/practice/android_inspect.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class AndroidContentTests(unittest.TestCase):
    def read(self, ident):
        return (ROOT/f'src/content-curation/{ident}.md').read_text('utf-8')

    def test_peer_cluster_and_durable_pages(self):
        taxonomy = (ROOT/'src/data/forensics-taxonomy.ts').read_text('utf-8')
        mobile = taxonomy.split("id: 'mobile'", 1)[1].split("id: 'network'", 1)[0]
        self.assertIn("{ name: 'Android 取证', topics: ['Android 原理与流程', 'Android', 'Android 工具与实战'] }", mobile)
        self.assertIn("{ name: 'iOS 取证'", mobile)
        registry = json.loads((ROOT/'src/data/forensics-supplements.json').read_text('utf-8'))
        for ident in (CORE, STORAGE, TOOLS):
            if ident != STORAGE:
                row = next(a for a in registry['articles'] if a['id'] == ident)
                self.assertEqual(row['track'], '手机取证')
            self.assertEqual(self.read(ident).strip(), (ROOT/f'src/content/knowledge/{ident}.md').read_text('utf-8').split('---',2)[2].strip())

    def test_all_provided_article_topics_have_real_target_sections(self):
        data = json.loads((ROOT/'docs/forensics-android-coverage.json').read_text('utf-8'))
        self.assertGreaterEqual(len(data['items']), 65)
        self.assertEqual(data['source']['url'], 'https://tqandjdc.github.io/2026/06/08/Android-Forensic-Analysis-Reference-Guide/')
        self.assertEqual(data['uncovered_headings'], [])
        self.assertEqual(len(data['headings']), 73)
        known = {item['id'] for item in data['items']}
        for heading in data['headings']:
            self.assertTrue(heading['item_ids'])
            self.assertTrue(set(heading['item_ids']) <= known)
        for item in data['items']:
            body = self.read(item['target'])
            self.assertIn(item['heading'], body, item['id'])
            block = body.split(item['heading'], 1)[1].split('\n## ', 1)[0]
            self.assertIn(item['status'], ('expanded', 'merged', 'corrected', 'qualified'))
            self.assertTrue(item['terms'])
            for term in item['terms']: self.assertIn(term, block, item['id'])

    def test_primary_and_contest_sources_are_registered_without_relaxing_global_audit(self):
        registry = json.loads((ROOT/'src/data/forensics-supplements.json').read_text('utf-8'))
        for ident in (CORE, TOOLS):
            urls=set(re.findall(r'\]\((https?://[^)]+)\)', self.read(ident)))
            sources=[s for s in registry['webSources'] if ident in s['articleIds']]
            self.assertEqual(urls, {s['url'] for s in sources})
            meta=(ROOT/f'src/content/knowledge/{ident}.md').read_text('utf-8').split('---',2)[1]
            for source in sources: self.assertIn(source['id'],meta)
        spec=importlib.util.spec_from_file_location('android_audit',ROOT/'scripts/audit_site.py')
        audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
        self.assertEqual(audit.CONTEST_PROVENANCE_PAGES,
                         {'/knowledge/forensic-ios-forensics/index.html','/knowledge/forensic-android-forensics/index.html'})
        self.assertIn('源文件',audit.FORBIDDEN)
        self.assertIn('数证杯',audit.FORBIDDEN)

    def test_existing_android_sections_and_cross_platform_topics_are_kept(self):
        preservation = json.loads((ROOT/'docs/forensics-android-preservation.json').read_text('utf-8'))
        sections = re.split(r'(?m)(?=^## \d\d )', self.read(STORAGE))[1:8]
        self.assertEqual(len(sections), 7)
        for section, expected in zip(sections, preservation['android_sections']):
            self.assertEqual(hashlib.sha256(section.strip().encode()).hexdigest(), expected['sha256'])
        for entry in preservation['unchanged_files']:
            self.assertEqual(hashlib.sha256((ROOT/entry['path']).read_bytes()).hexdigest(), entry['sha256'])
        for term in ('com.yiqiang.xmaster', 'vprom/sys/sys01', 'importFile'):
            self.assertIn(term, self.read(STORAGE))

    def test_real_competitions_and_corrected_claims(self):
        core, tools, storage = map(self.read, (CORE, TOOLS, STORAGE))
        for term in ('Magnet Virtual Summit 2022', 'Magnet User Summit 2023', 'Magnet Virtual Summit 2024',
                     '2024 数证杯', 'arroyo.db', 'personalsafety_db', '未复跑', '新增', '修订', '合并', '去重',
                     'FBE 从 Android 7.0', 'Android 10', 'Keystore'):
            self.assertIn(term, core)
        for term in ('ASCII', 'zlib', '不是固定 24 字节', 'apps/<package>/<domain>/', 'PKCS#8',
                     'ABE_PASSWD', 'run-as com.example.chat --user 0', '2026.4.3', 'Base64url',
                     '不是解密', '未执行设备采集'):
            self.assertIn(term, tools)
        for term in ('com.ss.android.ugc.aweme', 'cache4.db', 'app_chrome/Default', 'mmssms.db',
                     'pdu', 'canonical_addresses', 'calllog.db', 'bt_config.conf', 'packages.list',
                     'scan_ssid', '64 位十六进制', 'thumbnails.db', '账户库'):
            self.assertIn(term, storage)
        for unsafe in ('tail -c +25', 'python -m libab unpack', 'cat /proc/kmsg', 'find -L', 'VACUUM;'):
            self.assertNotIn(unsafe, core+tools+storage)

    def test_ab_header_is_variable_ascii_and_never_decrypts(self):
        h = helper()
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'input.ab'
            p.write_bytes(b'ANDROID BACKUP\n5\n1\nnone\nPAYLOAD')
            before = p.read_bytes()
            a = h.inspect_ab(p)
            self.assertEqual((a['version'],a['compressed'],a['payload_offset']), (5,True,24))
            self.assertEqual(p.read_bytes(), before)
            p.write_bytes(b'ANDROID BACKUP\n5\n1\nAES-256\n' + b'00\n'*2 + b'10000\n' + b'11'*16+b'\n'+b'22'*32+b'\nPAYLOAD')
            a = h.inspect_ab(p)
            self.assertGreater(a['payload_offset'],24)
            self.assertEqual(a['payload_status'], 'not_decrypted_or_decompressed')
            for bad in (b'bad', b'ANDROID BACKUP\n5\n2\nnone\n', b'ANDROID BACKUP\n5\n1\nnone'):
                p.write_bytes(bad)
                with self.assertRaises(ValueError): h.inspect_ab(p)

    def test_preferences_keep_types_and_input_hash(self):
        h = helper()
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'sample.xml'
            p.write_text('<map><string name="account">A &amp; B</string><boolean name="flag" value="true"/><long name="time" value="123"/><set name="tags"><string>x</string><string>y</string></set></map>', 'utf-8')
            before=p.read_bytes(); rows=h.inspect_prefs(p)['entries']
            self.assertEqual(rows[0]['value'], 'A & B')
            self.assertEqual(rows[1]['value'], True)
            self.assertEqual(rows[2]['type'], 'long')
            self.assertEqual(rows[3]['value'], ['x','y'])
            self.assertEqual(p.read_bytes(),before)
            p.write_text('<!DOCTYPE map [<!ENTITY e "xx">]><map/>','utf-8')
            with self.assertRaises(ValueError): h.inspect_prefs(p)

    def test_unverified_jwt_and_explicit_time_units(self):
        h=helper()
        enc=lambda b:base64.urlsafe_b64encode(b).decode().rstrip('=')
        result=h.inspect_jwt(enc(b'{"alg":"none"}')+'.'+enc(b'{"sub":"example","exp":1000}')+'.')
        self.assertFalse(result['signature_verified'])
        self.assertEqual(result['payload']['sub'],'example')
        with self.assertRaises(ValueError): h.inspect_jwt('not-jwt')
        self.assertEqual(h.convert_time('1000','unix','ms')['utc'],'1970-01-01T00:00:01+00:00')
        self.assertEqual(h.convert_time('11644473600000000','webkit','us')['utc'],'1970-01-01T00:00:00+00:00')
        for bad in ('NaN','Infinity','oops'):
            with self.assertRaises(ValueError): h.convert_time(bad,'unix','s')

    def test_published_sms_query_counts_messages_not_mms_parts(self):
        body=self.read(STORAGE)
        query=re.search(r'```sql\n(SELECT _id, address, date, type, read, body\nFROM sms.*?);\n```',body,re.S)
        self.assertIsNotNone(query)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'mmssms.db'; c=sqlite3.connect(p)
            c.executescript("CREATE TABLE sms(_id INTEGER,address TEXT,date INTEGER,type INTEGER,read INTEGER,body TEXT); INSERT INTO sms VALUES (1,'sample',1000,1,0,'example'),(2,'sample',2000,2,1,NULL);")
            c.close(); before=p.read_bytes(); c=sqlite3.connect(p.as_uri()+'?mode=ro',uri=True)
            self.assertEqual(len(c.execute(query.group(1)).fetchall()),2)
            with self.assertRaises(sqlite3.OperationalError): c.execute('DELETE FROM sms')
            c.close(); self.assertEqual(p.read_bytes(),before)

    def test_adversarial_large_exponent_and_nested_jwt_have_controlled_errors(self):
        h=helper()
        with self.assertRaises(ValueError): h.convert_time('1e1000000','unix','s')
        enc=lambda b:base64.urlsafe_b64encode(b).decode().rstrip('=')
        deep=b'{"a":'+b'['*1100+b'0'+b']'*1100+b'}'
        with self.assertRaises(ValueError): h.inspect_jwt(enc(b'{"alg":"none"}')+'.'+enc(deep)+'.')


if __name__=='__main__': unittest.main()
