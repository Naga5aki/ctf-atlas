import json
import re
import unittest
from pathlib import Path


SITE = Path(__file__).resolve().parents[1]
TARGET = 'forensic-kubernetes-cluster'


class KubernetesContentTests(unittest.TestCase):
    def test_cluster_has_one_home_and_old_entries_link_to_it(self):
        notes = SITE / 'src/content/knowledge'
        homes = []
        for path in notes.glob('*.md'):
            text = path.read_text(encoding='utf-8')
            if re.search(r'^topic:\s*["\']?服务器集群["\']?$', text, re.M):
                homes.append(path)
                self.assertIsNotNone(re.search(r'^track: "服务器取证"$', text, re.M), path.name)
            if path.stem != TARGET:
                body = text.split('---', 2)[-1]
                self.assertNotRegex(body, r'(?m)^\s*kubectl\s|<code>kubectl\s', path.name)
                self.assertNotRegex(body, r'(?m)^#{2,4} .*Kubernetes.*(?:取证|关系|实战)', path.name)
        self.assertEqual([p.stem for p in homes], [TARGET])
        for identifier in (
            'docker-evidence-01', 'docker-evidence-02', 'docker-evidence-03',
            'docker-evidence-04', 'docker-evidence-05', 'fic-case-13',
            'fic-case-14', 'forensic-guide-server',
        ):
            self.assertIn(f'/knowledge/{TARGET}/', (notes/f'{identifier}.md').read_text(encoding='utf-8'))
        self.assertEqual(len(list(notes.glob('docker-evidence-*.md'))), 5)

    def test_canonical_body_registry_and_provenance_are_durable(self):
        notes = SITE / 'src/content/knowledge'
        rendered = (notes/f'{TARGET}.md').read_text(encoding='utf-8')
        maintained = (SITE/f'src/content-curation/{TARGET}.md').read_text(encoding='utf-8').strip()
        import sys
        sys.path.insert(0, str(SITE/'scripts'))
        from import_manuals import normalize_forensic_markdown
        self.assertEqual(rendered.split('---', 2)[2].strip(), normalize_forensic_markdown(maintained, article_id=TARGET))
        registry = json.loads((SITE/'src/data/forensics-supplements.json').read_text(encoding='utf-8'))
        definition = next(a for a in registry['articles'] if a['id'] == TARGET)
        self.assertEqual((definition['track'], definition['topic']), ('服务器取证', '服务器集群'))
        ids = json.loads(re.search(r'^sourceIds: (.+)$', rendered, re.M)[1])
        self.assertTrue(set(definition['sourceIds']).issubset(ids))
        self.assertTrue(any(TARGET in group['articleIds'] for group in registry['sources']))
        self.assertNotRegex(maintained, r'题例|本题|本卷|数证杯|源文件|答案格式|(?:服|计|网)[（(]?\d+')


if __name__ == '__main__':
    unittest.main()
