import hashlib
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
ID='forensic-registry'

class RegRipperContentTests(unittest.TestCase):
    def body(self):return (ROOT/f'src/content-curation/{ID}.md').read_text('utf-8')

    def test_existing_body_and_other_topics_preserved(self):
        from test_baota_binding_content import reviewed_preservation_hash
        rec=json.loads((ROOT/'docs/forensics-regripper-preservation.json').read_text('utf-8'))
        old=rec['original_page'];now=(ROOT/old['path']).read_bytes()
        self.assertEqual(hashlib.sha256(now[:old['bytes']]).hexdigest(),old['sha256'])
        for n,h in rec['protected_files'].items():
            self.assertEqual(hashlib.sha256((ROOT/n).read_bytes()).hexdigest(),reviewed_preservation_hash(n,h),n)

    def test_unique_durable_page_and_sources(self):
        now=(ROOT/f'src/content/knowledge/{ID}.md').read_text('utf-8')
        self.assertEqual(self.body().strip(),now.split('---',2)[2].strip())
        self.assertIn('## 10 RegRipper',self.body())
        self.assertIn('track: 计算机取证',now.split('---',2)[1])
        self.assertIn('topic: 系统与用户痕迹',now.split('---',2)[1])
        sources=json.loads((ROOT/'src/data/forensics-supplements.json').read_text('utf-8'))['webSources']
        urls=' '.join(s['url'] for s in sources if ID in s['articleIds'])
        for host in ('RegRipper3.0','RegRipper4.0','kali.org/tools/regripper'):
            self.assertIn(host,urls)

    def test_actual_parameters_and_version_boundaries(self):
        b=self.body().split('## 10 RegRipper',1)[1]
        for f in ('-r','-d','-g','-a','-aT','-f','-p','-l','-c','-s','-u','-uP','-h'):
            self.assertIn('`'+f,b)
        for term in ('3.0','4.0','不是联网更新','不是注册表数据 CSV','事务日志','--help','插件代码'):
            self.assertIn(term,b)

    def test_plugins_are_source_checked_and_operational(self):
        b=self.body().split('## 10 RegRipper',1)[1]
        inv=json.loads((ROOT/'docs/forensics-regripper-plugins.json').read_text('utf-8'))
        self.assertEqual(inv['plugin_count'],257)
        self.assertEqual(inv['profile_count'],9)
        names={p['basename'] for p in inv['plugins']}
        for name in ('typedpaths','typedpaths_tln','userassist','runmru','recentdocs','samparse','usbstor','winver'):
            self.assertIn(name,names);self.assertIn('`'+name+'`',b)
        self.assertIn('.pl',b);self.assertIn('.pm',b)
        self.assertIn('adoberdr',b)
        self.assertIn('getVersion',b)

    def test_tln_and_synthetic_output_not_overclaimed(self):
        b=self.body().split('## 10 RegRipper',1)[1]
        for term in ('epoch|source|system|user|description','1704067200|REG|HOST_SAMPLE|USER_SAMPLE|TypedPaths - E:\\Lab\\Reports','只输出','url1','自建','未运行 GUI','不是逐次访问'):
            self.assertIn(term,b)
        self.assertNotIn('Transaction Log Notification',b)

    def test_workflow_errors_and_evidence_interpretation(self):
        b=self.body().split('## 10 RegRipper',1)[1]
        for term in ('sudo apt install regripper','2>','sha256sum','not found','STDERR','exit','ControlSet','Select','SID','追加','LastWrite','CSV','-r','-p'):
            self.assertIn(term,b)

if __name__=='__main__':unittest.main()
