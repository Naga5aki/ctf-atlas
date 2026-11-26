"""Short PHP runtime diagnosis retains Apache instance identity without the retired command catalog."""
from pathlib import Path
import re, unittest
ROOT = Path(__file__).resolve().parents[1]
def body(name):
    return (ROOT / "src/content-curation" / f"{name}.md").read_text("utf-8")
class ApacheEnvironmentContentTests(unittest.TestCase):
    def test_panel_and_system_instances_are_not_conflated(self):
        value = body("forensic-website-reconstruction").split("## 02 Java：", 1)[0]
        for token in ("系统 Apache 与宝塔 Apache 是不同实例", "原服务启动参数", "不另启系统 Apache"):
            self.assertIn(token, value)
    def test_syntax_gate_and_vhost_diagnosis_remain_short(self):
        value = body("forensic-website-reconstruction")
        self.assertIn("/www/server/apache/bin/httpd -t", value)
        self.assertIn("/www/server/apache/bin/httpd -S", value)
        self.assertIn("`-t` 通过后才重载原服务", value)
        self.assertIn("同一组参数", value)
    def test_old_apache_route_still_resolves_to_php(self):
        value = body("forensic-website-reconstruction")
        old = 'id="044-apachehttpd-与-apachectl-的实例核对与恢复"'
        self.assertEqual(value.count(old), 1)
        self.assertLess(value.index(old), value.index("## 02 Java："))
        self.assertIn("/knowledge/forensic-website-reconstruction/#044-", body("fic-case-04"))
    def test_web_evidence_page_keeps_evidence_not_second_runtime_catalog(self):
        value = body("fic-case-04")
        self.assertNotRegex(value, r"(?m)^httpd -(V|t|S)\b")
        self.assertIn("PHP 篇的 Web 实例核对", value)
    def test_both_generated_bodies_are_synchronized(self):
        for name in ("forensic-website-reconstruction", "fic-case-04"):
            generated = (ROOT / "src/content/knowledge" / f"{name}.md").read_text("utf-8").split("---", 2)[2].strip()
            self.assertEqual(generated, body(name).strip())
if __name__ == "__main__":
    unittest.main()
