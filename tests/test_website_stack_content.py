"""The user-approved six independent recovery workflows replace the old eight-step matrix."""
from pathlib import Path
import re, shutil, subprocess, sys, tempfile, unittest
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
ID = "forensic-website-reconstruction"
def body():
    return (ROOT / "src/content-curation" / f"{ID}.md").read_text("utf-8")
def articles():
    return re.split(r"(?m)^## ", body())[1:]
class WebsiteStackContentTests(unittest.TestCase):
    def test_six_named_stacks_replace_the_eight_mixed_steps(self):
        self.assertEqual(re.findall(r"(?m)^## \d\d ([^：]+)：", body()), ["PHP", "Java", "Python", "Node.js", "IIS", "静态站"])
    def test_each_article_starts_with_its_own_three_element_table(self):
        for value in articles():
            intro = value.split("### ", 1)[0]
            for label in ("| 三要素 |", "| 浏览器入口 |", "| 实际程序 |", "| 实际数据库 |"):
                self.assertIn(label, intro)
    def test_each_step_returns_to_all_three_grids(self):
        for value in articles():
            steps = re.split(r"(?m)^### \d\d\.\d+ ", value)[1:]
            self.assertGreaterEqual(len(steps), 5)
            for step in steps:
                self.assertRegex(step, r"三格回填：入口＝.*程序＝.*数据库＝")
    def test_each_stack_has_independent_snapshot_and_acceptance(self):
        for value in articles():
            for token in ("快照", "外联", "副本", "金额", "状态", "编号"):
                self.assertIn(token, value)
            self.assertNotIn("见另一篇", value)
    def test_markers_do_not_prove_backend_or_database(self):
        self.assertIn("不能证明它是后端", articles()[3])
        self.assertIn("不一定是静态目录", articles()[3])
        self.assertIn("不是纯静态产物", articles()[5])
    def test_runtime_and_protocol_follow_actual_project(self):
        text = body()
        for token in ("运行目录", "活动 profile", "原 Tomcat", "uwsgi_pass", "WSGI", "ASGI", "应用程序池", "纯静态"):
            self.assertIn(token, text)
    def test_short_shell_commands_parse_without_execution(self):
        exe = shutil.which("bash") or "C:/Program Files/Git/bin/bash.exe"
        for command in re.findall(r"(?ms)^```bash\n(.*?)^```", body()):
            self.assertLessEqual(len(command.splitlines()), 3)
            self.assertNotIn(" | ", command)
            run = subprocess.run([exe, "-n"], input=command, text=True, capture_output=True, encoding="utf-8")
            self.assertEqual(run.returncode, 0, run.stderr)
    def test_only_iis_uses_powershell_examples(self):
        for i, value in enumerate(articles()):
            self.assertEqual("```powershell" in value, i == 4)
    def test_curation_and_new_metadata_survive_two_import_applications(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        import import_manuals
        with tempfile.TemporaryDirectory() as td:
            notes = Path(td)
            shutil.copy2(ROOT / "src/content/knowledge" / f"{ID}.md", notes)
            with patch.object(import_manuals, "NOTES", notes):
                import_manuals.apply_forensics_curation()
                first = (notes / f"{ID}.md").read_bytes()
                import_manuals.apply_forensics_curation()
                self.assertEqual(first, (notes / f"{ID}.md").read_bytes())
            text = (notes / f"{ID}.md").read_text("utf-8")
            self.assertIn('title: "网站重构：PHP、Java、Python、Node.js、IIS 与静态站"', text)
            self.assertIn('topic: "网站重构"', text)
            self.assertEqual(text.split("---", 2)[2].strip(), body().strip())
if __name__ == "__main__":
    unittest.main()
