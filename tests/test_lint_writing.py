"""Rule-level tests for scripts/lint_writing.py.

Each case builds a tiny page in a temporary directory, so the rules are pinned
without depending on the content corpus.
"""
import tempfile
import unittest
from pathlib import Path

from scripts import lint_writing


class LintWritingTests(unittest.TestCase):
    def lint(self, body, rules=None):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            page = root / 'sample.md'
            page.write_text(body, encoding='utf-8')
            active = set(rules or lint_writing.WIDE_RULES)
            return lint_writing.lint_page(page, active, root)

    def rules_of(self, issues):
        return {item['rule'] for item in issues}

    def test_placeholder_words_in_prose(self):
        issues = self.lint('先执行命令，过程略，再看结果。')
        self.assertIn('placeholder', self.rules_of(issues))

    def test_placeholder_in_inline_code_is_ignored(self):
        issues = self.lint('参数写成`...`表示省略，正文不再提示。', rules=['placeholder'])
        self.assertNotIn('placeholder', self.rules_of(issues))

    def test_code_block_with_only_dots_is_flagged(self):
        issues = self.lint('```bash\n...\n```\n', rules=['code-placeholder'])
        self.assertIn('code-placeholder', self.rules_of(issues))

    def test_dots_inside_a_real_command_block_are_allowed(self):
        body = '```sql\nid=1 order by 1-- -\nid=1 order by 2-- -\n...\nid=1 order by 10-- -\n```\n'
        issues = self.lint(body, rules=['code-placeholder'])
        self.assertNotIn('code-placeholder', self.rules_of(issues))

    def test_explicit_payload_placeholder_is_flagged(self):
        issues = self.lint('```http\nGET /?id=<payload>\n```\n', rules=['code-placeholder'])
        self.assertIn('code-placeholder', self.rules_of(issues))

    def test_meta_sentence_is_flagged_but_plain_mention_is_not(self):
        flagged = self.lint('本页把原理、利用和防御分成三部分。', rules=['meta'])
        self.assertIn('meta', self.rules_of(flagged))
        clean = self.lint('本页的 Git 命令要在分析会话里执行。', rules=['meta'])
        self.assertNotIn('meta', self.rules_of(clean))

    def test_term_spelling(self):
        issues = self.lint('用 BurpSuite 抓包，再用 SQLMap 跑注入。', rules=['term'])
        messages = ' '.join(item['message'] for item in issues)
        self.assertIn('Burp Suite', messages)
        self.assertIn('sqlmap', messages)

    def test_half_width_punctuation_in_chinese(self):
        issues = self.lint('无;base64标记时,先解码。', rules=['punct'])
        self.assertIn('punct', self.rules_of(issues))

    def test_half_width_punctuation_in_code_is_ignored(self):
        issues = self.lint('执行`base64 -d; echo ok`后查看输出。', rules=['punct'])
        self.assertNotIn('punct', self.rules_of(issues))

    def test_wide_rules_stay_off_by_default(self):
        body = '先进行检查,然后继续。\n'
        default_issues = self.lint(body, rules=lint_writing.HIGH_RULES)
        self.assertEqual(default_issues, [])

    def test_heading_jump(self):
        issues = self.lint('## 二级\n\n#### 四级\n', rules=['heading-jump'])
        self.assertIn('heading-jump', self.rules_of(issues))

    def test_frontmatter_is_skipped(self):
        body = '---\ntitle: 测试\n---\n\n正文正常。\n'
        issues = self.lint(body)
        self.assertEqual(issues, [])


if __name__ == '__main__':
    unittest.main()
