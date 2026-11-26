import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SITE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SITE/'scripts'))
import import_manuals


class ForensicWebSourceTests(unittest.TestCase):
    def test_web_sources_are_durable_without_changing_existing_body_or_category(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            notes, data = base/'notes', base/'data'
            notes.mkdir(); data.mkdir()
            page = notes/'existing.md'
            page.write_text('---\nmodule: Forensics\ntrack: 服务器取证\ntopic: 主机与应用\nsourceIds: [retained]\n---\n\n原有完整正文\n', encoding='utf-8')
            (data/'inventory.json').write_text('[]', encoding='utf-8')
            registry = {'sources': [], 'articles': [], 'webSources': [
                {'id': 'web-zhihu-712211191', 'url': 'https://zhuanlan.zhihu.com/p/712211191', 'reviewedAt': '2026-10-02',
                 'articleIds': ['existing', 'existing']} ]}
            (data/'forensics-supplements.json').write_text(json.dumps(registry), encoding='utf-8')
            with patch.object(import_manuals, 'NOTES', notes), patch.object(import_manuals, 'DATA', data):
                self.assertEqual(import_manuals.apply_forensics_supplements(), 0)
                body, metadata = import_manuals._body_and_meta(page)
                self.assertEqual(metadata['sourceIds'], ['retained', 'web-zhihu-712211191'])
                self.assertEqual(body, '原有完整正文')
                self.assertIn('topic: 主机与应用', page.read_text('utf-8'))
                before = page.read_bytes()
                import_manuals.apply_forensics_supplements()
                self.assertEqual(before, page.read_bytes())

                guide = base/'curation'
                guide.mkdir()
                (guide/'existing.md').write_text('## 01 保全正文\n\n独立讲解。\n', encoding='utf-8')
                with patch.object(import_manuals, 'CURATION', guide):
                    import_manuals.apply_forensics_curation()
                self.assertIn('updated: "2026-10-02"', page.read_text('utf-8'))

    def test_invalid_web_associations_fail_before_any_page_is_written(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            notes, data = base/'notes', base/'data'
            notes.mkdir(); data.mkdir()
            page = notes/'existing.md'
            page.write_text('---\nmodule: Forensics\nsourceIds: [retained]\n---\n\n完整正文\n', encoding='utf-8')
            foreign = notes/'web-note.md'
            foreign.write_text('---\nmodule: Web\n---\n\n其他模块\n', encoding='utf-8')
            (data/'inventory.json').write_text('[]', encoding='utf-8')
            before = {p.name:p.read_bytes() for p in notes.glob('*.md')}
            cases = [('missing', 'https://example.test/a'), ('web-note', 'https://example.test/a'),
                     ('existing', 'javascript:alert(1)'), ('existing', 'https://exa mple.test/a'),
                     ('existing', 'https://example.test:notaport/a'), ('existing', 'https://example.test:70000/a'),
                     ('existing', 'https://example.test/a\n')]
            with patch.object(import_manuals, 'NOTES', notes), patch.object(import_manuals, 'DATA', data):
                for identifier, url in cases:
                    with self.subTest(identifier=identifier, url=url):
                        registry = {'sources': [], 'articles': [], 'webSources': [
                            {'id':'web-test-valid', 'url':'https://example.test/a', 'articleIds':['existing']},
                            {'id':'web-test-invalid', 'url':url, 'articleIds':[identifier]}]}
                        (data/'forensics-supplements.json').write_text(json.dumps(registry), encoding='utf-8')
                        with self.assertRaises(ValueError):
                            import_manuals.apply_forensics_supplements()
                        self.assertEqual(before, {p.name:p.read_bytes() for p in notes.glob('*.md')})

    def test_supplement_id_collision_is_rejected_before_creating_other_articles(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            notes, data, guide = base/'notes', base/'data', base/'curation'
            for path in (notes, data, guide):
                path.mkdir()
            foreign = notes/'web-note.md'
            foreign.write_text('---\nmodule: Web\n---\n\n其他模块\n', encoding='utf-8')
            before = {p.name: p.read_bytes() for p in notes.glob('*.md')}
            for identifier in ('new-note', 'web-note'):
                (guide/f'{identifier}.md').write_text('## 01 独立正文\n\n完整讲解。\n', encoding='utf-8')
            (data/'inventory.json').write_text('[]', encoding='utf-8')
            registry = {'sources': [], 'articles': [
                {'id': identifier, 'module': 'Forensics'} for identifier in ('new-note', 'web-note')
            ]}
            (data/'forensics-supplements.json').write_text(json.dumps(registry), encoding='utf-8')
            with patch.object(import_manuals, 'NOTES', notes), patch.object(import_manuals, 'DATA', data), patch.object(import_manuals, 'CURATION', guide):
                with self.assertRaises(ValueError):
                    import_manuals.apply_forensics_supplements()
            self.assertEqual(before, {p.name: p.read_bytes() for p in notes.glob('*.md')})


if __name__ == '__main__':
    unittest.main()
