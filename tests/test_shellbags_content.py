import hashlib
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
ID = 'forensic-shellbags'
PRESERVATION = ROOT/'docs/forensics-shellbags-preservation.json'


class ShellBagsContentTests(unittest.TestCase):
    def body(self):
        return (ROOT/f'src/content-curation/{ID}.md').read_text('utf-8')

    def test_unique_durable_home_and_existing_category(self):
        body = self.body()
        generated = (ROOT/f'src/content/knowledge/{ID}.md').read_text('utf-8')
        self.assertEqual(body.strip(), generated.split('---',2)[2].strip())
        meta=generated.split('---',2)[1]
        for value in ('module: "Forensics"','track: "计算机取证"','topic: "系统与用户痕迹"'):
            self.assertIn(value,meta)
        registry=json.loads((ROOT/'src/data/forensics-supplements.json').read_text('utf-8'))
        self.assertEqual(sum(a['id']==ID for a in registry['articles']),1)

    def test_structures_locations_and_time_boundaries_are_covered(self):
        body=self.body()
        for value in ('NTUSER.DAT','UsrClass.dat','ShellNoRoam','BagMRU','Bags','MRUListEx','NodeSlot',
                      'Shell Item','PIDL','LastWrite','First Interacted','Last Interacted',
                      '0xBEEF0004','2 秒','MRU=0','HasExplored','24H2','同级','UTC'):
            self.assertIn(value,body)
        self.assertGreaterEqual(len(re.findall(r'^## \d\d ',body,re.M)),10)
        self.assertIn('不是',body)
        self.assertIn('文件被打开',body)
        self.assertIn('盘符',body)
        self.assertIn('复制',body)

    def test_gui_cli_and_cross_checks_are_operational(self):
        body=self.body()
        for value in ('ShellBagsExplorer.exe','SBECmd.exe','.NET 9','离线','事务日志','筛选','递归','CSV',
                      'MFT','序列号','Jump List','LNK','UNC','Get-FileHash','--csv','--csvf','-d'):
            self.assertIn(value,body)
        self.assertNotRegex(body,r'SBECmd\.exe[^\n]*\s-f\s')
        self.assertIn('true 是忽略日志',body)
        self.assertIn('自建',body)
        self.assertIn('原始',body)

    def test_old_registry_usb_and_other_pages_preserved(self):
        preservation=json.loads(PRESERVATION.read_text('utf-8'))
        for ident,record in preservation['old_pages'].items():
            now=(ROOT/record['path']).read_bytes()
            self.assertEqual(hashlib.sha256(now[:record['old_bytes']]).hexdigest(),record['old_sha256'])
            self.assertIn('/knowledge/forensic-shellbags/',now.decode('utf-8'))
        for n,h in preservation['protected_files'].items():
            self.assertEqual(hashlib.sha256((ROOT/n).read_bytes()).hexdigest(),h,n)

    def test_reviewed_primary_sources_are_durable(self):
        registry=json.loads((ROOT/'src/data/forensics-supplements.json').read_text('utf-8'))
        sources=[s for s in registry['webSources'] if ID in s['articleIds']]
        self.assertGreaterEqual(len(sources),5)
        urls=' '.join(s['url'] for s in sources)
        for host in ('microsoft.com','ericzimmerman','libyal','4n6k.com','ilyakobzar.com'):
            self.assertIn(host,urls)
        rendered=(ROOT/f'src/content/knowledge/{ID}.md').read_text('utf-8')
        for source in sources:
            self.assertIn(source['id'],rendered.split('---',2)[1])

    def test_published_mru_example_has_correct_order_and_terminator(self):
        body=self.body()
        match=re.search(r'```python\n(# MRUListEx[^`]+)```',body)
        self.assertIsNotNone(match)
        namespace={}
        exec(compile(match.group(1),'published_mru_example','exec'),namespace)
        self.assertEqual(namespace['order'],[2,0,5])
        self.assertEqual(namespace['data'][-4:],b'\xff'*4)


if __name__=='__main__':
    unittest.main()
