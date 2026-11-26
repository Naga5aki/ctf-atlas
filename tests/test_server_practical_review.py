"""Preservation and operational-content gates for the reviewed server module."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
REPORT = 'docs/server-forensics-review-20261006.json'


def digest(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def headings(text):
    result, fence = [], None
    for line in text.splitlines():
        m = re.match(r'^\s*(`{3,}|~{3,})', line)
        if m:
            char = m[1][0]
            fence = None if fence == char else char if fence is None else fence
        elif fence is None and re.match(r'^#{2,6} ', line):
            result.append(line)
    return result


def blocks(text):
    return re.findall(r'(?ms)^```[^\n]*\n.*?^```[^\n]*$', text)


def tables(text):
    return re.findall(r'(?m)(?:^\|[^\n]*\n)+', text)


class ServerPracticalReviewTests(unittest.TestCase):
    def report(self):
        path = ROOT / REPORT
        self.assertTrue(path.is_file(), 'module review record must exist after the review')
        return json.loads(path.read_text('utf-8'))

    def body(self, article):
        return (ROOT / article['curation']).read_text('utf-8')

    def test_scope_is_the_existing_server_track_only(self):
        report = self.report()
        self.assertEqual(len(report['articles']), 21)
        self.assertEqual(len({a['id'] for a in report['articles']}), 21)
        for a in report['articles']:
            page = (ROOT / a['generated']).read_text('utf-8')
            header = page.split('---', 2)[1]
            self.assertRegex(header, r'track: ["\']?服务器取证')
            self.assertEqual(digest(header), a['preservation']['metadata_sha256'])

    def test_all_real_sections_have_individual_review_decisions(self):
        report = self.report()
        # 533 baseline + 1 new section (fic-case-04 §04.4, batch B3) = 534
        self.assertEqual(sum(len(a['sections']) for a in report['articles']), report['real_sections'])
        self.assertTrue(report['website_layout_20261014']['user_approved_replacement'])
        for a in report['articles']:
            self.assertEqual([s['heading'] for s in a['sections']], headings(self.body(a)))
            for s in a['sections']:
                self.assertTrue(s['summary'] and s['decision'] and s['reason'])

    def test_every_existing_code_block_is_preserved_in_order(self):
        for a in self.report()['articles']:
            self.assertEqual([digest(b) for b in blocks(self.body(a))], a['preservation']['code_sha256'])
            raw = (ROOT / a['curation']).read_bytes().decode('utf-8')
            self.assertEqual([digest(b) for b in blocks(raw)], a['preservation']['raw_code_sha256'])

    def test_every_existing_table_is_preserved_in_order(self):
        for a in self.report()['articles']:
            self.assertEqual([digest(t) for t in tables(self.body(a))], a['preservation']['table_sha256'])

    def test_existing_inline_technical_tokens_are_retained(self):
        for a in self.report()['articles']:
            now = Counter(re.findall(r'(?<!`)`([^`\n]+)`(?!`)', self.body(a)))
            missing = Counter(a['preservation']['inline_tokens']) - now
            self.assertFalse(missing, f"{a['id']}: {dict(missing)}")

    def test_generated_bodies_are_synchronized_with_durable_curation(self):
        for a in self.report()['articles']:
            generated = (ROOT / a['generated']).read_text('utf-8').split('---', 2)[2]
            self.assertEqual(generated.strip(), self.body(a).strip())
            self.assertEqual(digest(self.body(a)), a['preservation']['modified_text_sha256'])

    def test_each_change_is_unique_traceable_and_not_a_parallel_article(self):
        report = self.report()
        self.assertEqual(report['new_articles'], 0)
        self.assertEqual(report['deleted_sections'], 0)
        self.assertGreaterEqual(sum(len(a['edits']) for a in report['articles']), 50)
        for a in report['articles']:
            text = self.body(a)
            for e in a['edits']:
                self.assertEqual(text.count(e['new']), 1, a['id'])
                self.assertTrue(e['reason'] and e['source_basis'] and e['preserved'])

    def test_user_approved_six_workflows_replace_old_four_method_prose(self):
        report = self.report()
        a = next(a for a in report['articles'] if a['id'] == 'forensic-website-reconstruction')
        value = self.body(a)
        self.assertEqual(re.findall(r'^## \d\d ([^：]+)：', value, re.M), ['PHP', 'Java', 'Python', 'Node.js', 'IIS', '静态站'])
        self.assertIn('065-四种常见改动的影响恢复观察与分支改变分开', value)
        self.assertIn('自己的 `salt`', value)
        self.assertNotIn('#### 方法三：把Member', value)
        self.assertTrue(report['website_layout_20261014']['user_approved_replacement'])

    def test_source_limits_are_explicit_and_no_uncertain_content_is_deleted(self):
        report = self.report()
        self.assertTrue(report['pending'])
        self.assertEqual(report['uncertain_deletions'], 0)
        for a in report['articles']:
            self.assertTrue(a['sources'], a['id'])
            for source in a['sources']:
                self.assertTrue(source['read_status'] and source['findings'])
        for row in report['pending']:
            self.assertTrue(row['article_id'] and row['item'] and row['retained'])

    def test_non_server_evidence_tools_and_historical_reports_are_unchanged(self):
        for path, expected in self.report()['unaffected_hashes'].items():
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), expected, path)


if __name__ == '__main__':
    unittest.main()
