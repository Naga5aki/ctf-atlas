import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SITE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SITE / 'scripts'))
import audit_forensics_web


class ForensicsCoverageAuditTests(unittest.TestCase):
    def run_with_module_field(self, field):
        manifest = json.loads((SITE / 'docs/forensics-web-coverage.json').read_text('utf-8'))
        for row in manifest['records']:
            row['targets'] = ['knowledge/test-page'] if row['coverage'] != 'non-knowledge' else []
        standards = [row for row in manifest['records']
                     if row['site'] == 'DigiForensics' and row['id'].startswith(('sf-', 'gb-'))]
        codes = [row['id'].upper().replace('SF-T-', 'SF/T ').replace('SF-Z-JD-', 'SF/Z JD')
                 .replace('GB-T-', 'GB/T ') for row in standards]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'docs').mkdir()
            notes = root / 'src/content/knowledge'
            notes.mkdir(parents=True)
            (root / 'docs/forensics-web-coverage.json').write_text(json.dumps(manifest), 'utf-8')
            (notes / 'test-page.md').write_text(
                '---\n' + field + '\ntopic: "网站重构"\n---\n\n正文。\n', 'utf-8')
            (notes / 'forensic-quality.md').write_text('\n'.join(codes), 'utf-8')
            with patch.object(audit_forensics_web, 'ROOT', root), contextlib.redirect_stdout(io.StringIO()):
                return audit_forensics_web.audit()

    def test_generated_and_handwritten_module_scalars_are_accepted(self):
        for field in ('module: Forensics', 'module: "Forensics"', "module: 'Forensics'"):
            with self.subTest(field=field):
                self.assertEqual(self.run_with_module_field(field), [])

    def test_foreign_or_malformed_module_scalars_remain_rejected(self):
        for field in ('module: Web', 'module: "Forensics\'', 'summary: Forensics'):
            with self.subTest(field=field):
                errors = self.run_with_module_field(field)
                self.assertTrue(errors)
                self.assertTrue(all('落点不属Forensics' in error for error in errors))


if __name__ == '__main__':
    unittest.main()
