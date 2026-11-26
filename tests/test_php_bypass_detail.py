"""Historical constructed lab regressions remain independent of the retired four-bypass prose."""
from pathlib import Path
import importlib.util, subprocess, sys, unittest
ROOT = Path(__file__).resolve().parents[1]
def lab():
    spec = importlib.util.spec_from_file_location("bypass_detail_lab", ROOT / "public/practice/php_admin_evidence_lab.py")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result
class PHPBypassDetailTests(unittest.TestCase):
    def test_error_output_observation_never_authenticates(self):
        m = lab()
        with m.fixture() as db:
            before = m.snapshot(db)
            r = m.simulate_bypass(db, "observe", password="wrong")
            self.assertEqual(r["display_digest"], m.legacy_digest(m.REPLAY))
            self.assertFalse(r["login"])
            self.assertEqual(before, m.snapshot(db))
            self.assertIsNone(m.simulate_bypass(db, "observe", password="wrong", captcha=False)["display_digest"])
    def test_early_mode_requires_enabled_existing_privileged_uid(self):
        m = lab()
        with m.fixture() as db:
            self.assertTrue(m.simulate_bypass(db, "early", uid=9001)["login"])
            for uid in (None, 9999, 9002, 9003):
                self.assertFalse(m.simulate_bypass(db, "early", uid=uid)["login"])
            self.assertFalse(m.simulate_bypass(db, "early", uid=9001, session_ok=False)["login"])
    def test_inverted_comparison_keeps_other_gates_and_is_not_normal_auth(self):
        m = lab()
        with m.fixture() as db:
            self.assertFalse(m.simulate_bypass(db, "invert", password=m.ORIGINAL)["login"])
            self.assertTrue(m.simulate_bypass(db, "invert", password="wrong")["login"])
            for options in ({"captcha": False}, {"ip_allowed": False}, {"session_ok": False}, {"username": "missing_lab"}):
                self.assertFalse(m.simulate_bypass(db, "invert", password="wrong", **options)["login"])
    def test_matrix_cli_and_existing_selftest(self):
        for phase, expected in (("bypass-matrix", "PHP_BYPASS_MATRIX checks=22 passed=22 network_requests=0"), ("self-test", "PHP_ADMIN_SELFTEST checks=18 passed=18 network_requests=0")):
            p = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "public/practice/php_admin_evidence_lab.py"), phase], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertIn(expected, p.stdout)
    def test_legacy_php_links_survive_without_promoting_bypass_prose(self):
        text = (ROOT / "src/content-curation/forensic-website-reconstruction.md").read_text("utf-8")
        for old in ("065-四种常见改动的影响恢复观察与分支改变分开", "065-php网站后台密码绕过四种方法与副本复现"):
            self.assertEqual(text.count('id="' + old + '"'), 1)
        self.assertNotIn("#### 方法三：把Member", text)
        self.assertIn("不要通过网页错误提示输出摘要", text)
    def test_compatibility_anchors_survive_only_on_target_page(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        from import_manuals import normalize_forensic_markdown as normalize
        anchor = '<span id="065-php网站后台密码绕过四种方法与副本复现"></span>'
        self.assertEqual(normalize(anchor, article_id="forensic-website-reconstruction"), anchor)
        self.assertIn("&lt;span", normalize(anchor, article_id="fic-case-04"))
        self.assertIn("&lt;span", normalize('<span id="arbitrary"></span>', article_id="forensic-website-reconstruction"))
if __name__ == "__main__":
    unittest.main()
