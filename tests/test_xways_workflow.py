import json
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
ID='forensic-xways-workflow'
URLS={
    'https://www.forensics-wiki.com/node/0197f5eb-59ea-7d5d-a88f-d997aac44bdc',
    'https://www.forensics-wiki.com/node/0197f603-6725-7f16-9edb-87c885033916',
    'https://www.forensics-wiki.com/node/0197f606-44de-70fa-840c-6ed2c0462d5c',
    'https://wenku.csdn.net/column/45z64793a5',
    'https://www.cnblogs.com/suv789/p/18304375',
    'https://www.forensics-wiki.com/node/0197f612-4279-7699-a18b-3ca961f7b7bb',
    'https://www.forensics-wiki.com/node/0197fd30-0ac9-7077-b4a6-bb8badd8accf',
    'https://www.forensics-wiki.com/node/0197fd4e-1ec0-7f00-a3a9-aa54a0705086',
}

class XwaysWorkflowTests(unittest.TestCase):
    def test_independent_home_and_all_supplied_source_urls(self):
        registry=json.loads((ROOT/'src/data/forensics-supplements.json').read_text('utf-8'))
        entries=[x for x in registry['articles'] if x['id']==ID]
        self.assertEqual(len(entries),1)
        self.assertEqual((entries[0]['module'],entries[0]['track'],entries[0]['topic']),('Forensics','综合取证','工具与路径'))
        body=(ROOT/f'src/content-curation/{ID}.md').read_text('utf-8')
        self.assertEqual(set(re.findall(r'\]\((https?://[^)]+)\)',body)),URLS)
        sections=re.findall(r'^## (.+)$',body,re.M)
        self.assertEqual(len(sections),18)
        self.assertEqual(sections[-1],'18 来源说明')
        self.assertEqual({x['url'] for x in registry['webSources'] if ID in x['articleIds']},URLS)

    def test_durable_body_and_existing_tool_entry(self):
        body=(ROOT/f'src/content-curation/{ID}.md').read_text('utf-8')
        generated=(ROOT/f'src/content/knowledge/{ID}.md').read_text('utf-8')
        self.assertEqual(generated.split('---',2)[2].strip(),body.strip())
        tool=(ROOT/'src/content/tools/forensic-xways.md').read_text('utf-8')
        self.assertIn(f'/knowledge/{ID}/',tool)
        self.assertIn('/knowledge/forensic-usb-evidence/',tool)

    def test_conflict_limits_and_high_value_workflows_present(self):
        body=(ROOT/f'src/content-curation/{ID}.md').read_text('utf-8')
        for term in ['Alt+C','Ctrl+I','Alt+F10','Ctrl+F2','Refine Volume Snapshot','不是另做一份完整磁盘镜像',
                     'Events List','20.7','Ctrl+0','三态','只读','marker-help','Long Gun','Nude Photography',
                     'Live RAM Memory','未被指定 Wiki 确认','标签文件会被删除','恢复','本文不编造步骤',
                     'Source of program Uninstall','Content created (Exif)','导入关联报告表(I)','`.rtd`',
                     'Carving','多次快照','坏道扫描','Compare hash values']:
            self.assertIn(term,body)
        self.assertNotIn('源文件',body)

if __name__=='__main__':
    unittest.main()
