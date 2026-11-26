"""Folding tags stay stable for the reviewed server articles and nowhere else."""
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from import_manuals import normalize_forensic_markdown as normalize

PANEL = "forensic-server-panel"
SERVICES = "forensic-server-services"
FIC03 = "fic-case-03"
GUIDE = "forensic-guide-server"
FIC04 = "fic-case-04"
FIC05 = "fic-case-05"
DBREC = "forensic-database-recovery"
DOCKER01 = "docker-evidence-01"
DOCKER02 = "docker-evidence-02"
DOCKER03 = "docker-evidence-03"
DOCKER04 = "docker-evidence-04"
DOCKER05 = "docker-evidence-05"
GIT03 = "git-docker-03"
UNRELATED = "fic-case-01"


class ServerClearFlowTests(unittest.TestCase):
    def test_bare_disclosures_survive_first_import(self):
        source = "<details>\n<summary>展开日志路径与轮转排查</summary>\n\n正文 <FILE_OBJECT>\n\n</details>"
        result = normalize(source, article_id=PANEL)
        self.assertIn("<details>\n<summary>展开日志路径与轮转排查</summary>", result)
        self.assertIn("&lt;FILE_OBJECT&gt;", result)

    def test_fixed_old_anchor_survives_and_arbitrary_span_does_not(self):
        allowed = '<span id="01-先识别面板与实际服务"></span>'
        self.assertEqual(normalize(allowed, article_id=PANEL), allowed)
        blocked = '<span id="01-先识别面板与实际服务" onclick="x"></span>'
        self.assertIn("&lt;", normalize(blocked, article_id=PANEL))
        self.assertIn("&lt;span id=\"other\"&gt;", normalize('<span id="other"></span>', article_id=PANEL))

    def test_attributes_events_and_other_html_stay_escaped(self):
        samples = (
            "<details open>",
            '<summary onclick="alert(1)">',
            "<script>alert(1)</script>",
            "<img src=x onerror=alert(1)>",
        )
        for sample in samples:
            escaped = normalize(sample, article_id=PANEL)
            self.assertIn("&lt;", escaped, sample)
            self.assertNotIn("<script", escaped)
            self.assertNotIn("<details open>", escaped)

    def test_unrelated_article_still_escapes_disclosures(self):
        source = "<details>\n<summary>参数</summary>\n\n正文\n\n</details>"
        escaped = normalize(source, article_id=UNRELATED)
        self.assertIn("&lt;details&gt;", escaped)
        self.assertIn("&lt;summary&gt;", escaped)
        self.assertNotIn("<details>", escaped)

    def test_code_blocks_are_not_rewritten(self):
        source = "```html\n<details onclick=\"example\">\n<span id=\"01-先识别面板与实际服务\"></span>\n```"
        self.assertEqual(normalize(source, article_id=PANEL), source)
        self.assertEqual(normalize(source, article_id=SERVICES), source)
        self.assertEqual(normalize(source, article_id=UNRELATED), source)

    def test_services_fold_and_old_anchor_survive_and_body_matches(self):
        source = "<details>\n<summary>展开 SSH日志取证</summary>\n\n正文 <FILE_OBJECT>\n\n</details>"
        result = normalize(source, article_id=SERVICES)
        self.assertIn("<details>\n<summary>展开 SSH日志取证</summary>", result)
        self.assertIn("&lt;FILE_OBJECT&gt;", result)
        allowed = '<span id="08-实战验证一项可疑定时任务"></span>'
        self.assertEqual(normalize(allowed, article_id=SERVICES), allowed)
        self.assertIn("&lt;details open&gt;", normalize("<details open>", article_id=SERVICES))
        curation = (ROOT / "src/content-curation" / f"{SERVICES}.md").read_text(encoding="utf-8").strip()
        page = (ROOT / "src/content/knowledge" / f"{SERVICES}.md").read_text(encoding="utf-8").split("---", 2)[2].strip()
        once = normalize(curation, article_id=SERVICES)
        twice = normalize(once, article_id=SERVICES)
        self.assertEqual(once, page)
        self.assertEqual(twice, page)
        self.assertIn("<details>", page)
        self.assertIn(allowed, page)
        self.assertNotIn("这次要留下的结论", page)
        self.assertNotIn("**对上了什么：**", page)

    def test_fic03_fold_and_old_anchor_survive_and_body_matches(self):
        source = "<details>\n<summary>展开 os-release 字段逐项判读</summary>\n\n正文 <FILE_OBJECT>\n\n</details>"
        result = normalize(source, article_id=FIC03)
        self.assertIn("<details>\n<summary>展开 os-release 字段逐项判读</summary>", result)
        self.assertIn("&lt;FILE_OBJECT&gt;", result)
        allowed = '<span id="03-服务清单与状态判定"></span>'
        self.assertEqual(normalize(allowed, article_id=FIC03), allowed)
        self.assertIn("&lt;details open&gt;", normalize("<details open>", article_id=FIC03))
        curation = (ROOT / "src/content-curation" / f"{FIC03}.md").read_text(encoding="utf-8").strip()
        page = (ROOT / "src/content/knowledge" / f"{FIC03}.md").read_text(encoding="utf-8").split("---", 2)[2].strip()
        once = normalize(curation, article_id=FIC03)
        twice = normalize(once, article_id=FIC03)
        self.assertEqual(once, page)
        self.assertEqual(twice, page)
        self.assertIn("<details>", page)
        self.assertIn(allowed, page)
        self.assertNotIn("这次要留下的结论", page)
        self.assertNotIn("**对上了什么：**", page)

    def test_guide_fold_and_old_anchor_survive_and_body_matches(self):
        source = "<details>\n<summary>展开五层证据定位表</summary>\n\n正文 <FILE_OBJECT>\n\n</details>"
        result = normalize(source, article_id=GUIDE)
        self.assertIn("<details>\n<summary>展开五层证据定位表</summary>", result)
        self.assertIn("&lt;FILE_OBJECT&gt;", result)
        allowed = '<span id="07-不同服务架构如何归入同一条主线"></span>'
        self.assertEqual(normalize(allowed, article_id=GUIDE), allowed)
        self.assertIn("&lt;details open&gt;", normalize("<details open>", article_id=GUIDE))
        curation = (ROOT / "src/content-curation" / f"{GUIDE}.md").read_text(encoding="utf-8").strip()
        page = (ROOT / "src/content/knowledge" / f"{GUIDE}.md").read_text(encoding="utf-8").split("---", 2)[2].strip()
        once = normalize(curation, article_id=GUIDE)
        twice = normalize(once, article_id=GUIDE)
        self.assertEqual(once, page)
        self.assertEqual(twice, page)
        self.assertIn("<details>", page)
        self.assertIn(allowed, page)
        self.assertNotIn("这次要留下的结论", page)
        self.assertNotIn("**对上了什么：**", page)

    def test_fic04_fold_and_old_anchor_survive_and_body_matches(self):
        source = "<details>\n<summary>展开 Nginx 配置位置表</summary>\n\n正文 <FILE_OBJECT>\n\n</details>"
        result = normalize(source, article_id=FIC04)
        self.assertIn("<details>\n<summary>展开 Nginx 配置位置表</summary>", result)
        self.assertIn("&lt;FILE_OBJECT&gt;", result)
        allowed = '<span id="04-访问日志与活动时间线"></span>'
        self.assertEqual(normalize(allowed, article_id=FIC04), allowed)
        self.assertIn("&lt;details open&gt;", normalize("<details open>", article_id=FIC04))
        curation = (ROOT / "src/content-curation" / f"{FIC04}.md").read_text(encoding="utf-8").strip()
        page = (ROOT / "src/content/knowledge" / f"{FIC04}.md").read_text(encoding="utf-8").split("---", 2)[2].strip()
        once = normalize(curation, article_id=FIC04)
        twice = normalize(once, article_id=FIC04)
        self.assertEqual(once, page)
        self.assertEqual(twice, page)
        self.assertIn("<details>", page)
        self.assertIn(allowed, page)
        self.assertNotIn("这次要留下的结论", page)
        self.assertNotIn("**对上了什么：**", page)

    def test_fic05_fold_and_old_anchor_survive_and_body_matches(self):
        source = "<details>\n<summary>展开存储对象解析表</summary>\n\n正文 <FILE_OBJECT>\n\n</details>"
        result = normalize(source, article_id=FIC05)
        self.assertIn("<details>\n<summary>展开存储对象解析表</summary>", result)
        self.assertIn("&lt;FILE_OBJECT&gt;", result)
        allowed = '<span id="04-服务不可用时读取原始页"></span>'
        self.assertEqual(normalize(allowed, article_id=FIC05), allowed)
        self.assertIn("&lt;details open&gt;", normalize("<details open>", article_id=FIC05))
        curation = (ROOT / "src/content-curation" / f"{FIC05}.md").read_text(encoding="utf-8").strip()
        page = (ROOT / "src/content/knowledge" / f"{FIC05}.md").read_text(encoding="utf-8").split("---", 2)[2].strip()
        once = normalize(curation, article_id=FIC05)
        twice = normalize(once, article_id=FIC05)
        self.assertEqual(once, page)
        self.assertEqual(twice, page)
        self.assertIn("<details>", page)
        self.assertIn(allowed, page)
        self.assertNotIn("这次要留下的结论", page)
        self.assertNotIn("**对上了什么：**", page)

    def test_dbrecovery_fold_and_old_anchor_survive_and_body_matches(self):
        source = "<details>\n<summary>展开数据库材料识别表</summary>\n\n正文 <FILE_OBJECT>\n\n</details>"
        result = normalize(source, article_id=DBREC)
        self.assertIn("<details>\n<summary>展开数据库材料识别表</summary>", result)
        self.assertIn("&lt;FILE_OBJECT&gt;", result)
        allowed = '<span id="19-时间ip字符串二进制与json字段"></span>'
        self.assertEqual(normalize(allowed, article_id=DBREC), allowed)
        self.assertIn("&lt;details open&gt;", normalize("<details open>", article_id=DBREC))
        curation = (ROOT / "src/content-curation" / f"{DBREC}.md").read_text(encoding="utf-8").strip()
        page = (ROOT / "src/content/knowledge" / f"{DBREC}.md").read_text(encoding="utf-8").split("---", 2)[2].strip()
        once = normalize(curation, article_id=DBREC)
        twice = normalize(once, article_id=DBREC)
        self.assertEqual(once, page)
        self.assertEqual(twice, page)
        self.assertIn("<details>", page)
        self.assertIn(allowed, page)
        self.assertNotIn("这次要留下的结论", page)
        self.assertNotIn("**对上了什么：**", page)

    def test_docker01_fold_and_old_anchor_survive_and_body_matches(self):
        source = "<details>\n<summary>展开运行时组件速查表</summary>\n\n正文 <FILE_OBJECT>\n\n</details>"
        result = normalize(source, article_id=DOCKER01)
        self.assertIn("<details>\n<summary>展开运行时组件速查表</summary>", result)
        self.assertIn("&lt;FILE_OBJECT&gt;", result)
        allowed = '<span id="02-docker-整体架构"></span>'
        self.assertEqual(normalize(allowed, article_id=DOCKER01), allowed)
        self.assertIn("&lt;details open&gt;", normalize("<details open>", article_id=DOCKER01))
        curation = (ROOT / "src/content-curation" / f"{DOCKER01}.md").read_text(encoding="utf-8").strip()
        page = (ROOT / "src/content/knowledge" / f"{DOCKER01}.md").read_text(encoding="utf-8").split("---", 2)[2].strip()
        once = normalize(curation, article_id=DOCKER01)
        twice = normalize(once, article_id=DOCKER01)
        self.assertEqual(once, page)
        self.assertEqual(twice, page)
        self.assertIn("<details>", page)
        self.assertIn(allowed, page)
        self.assertNotIn("**对上了什么：**", page)

    def test_docker02_fold_and_old_anchor_survive_and_body_matches(self):
        source = "<details>\n<summary>展开快速定位表</summary>\n\n正文 <FILE_OBJECT>\n\n</details>"
        result = normalize(source, article_id=DOCKER02)
        self.assertIn("<details>\n<summary>展开快速定位表</summary>", result)
        self.assertIn("&lt;FILE_OBJECT&gt;", result)
        allowed = '<span id="02-docker-服务器取证整体流程"></span>'
        self.assertEqual(normalize(allowed, article_id=DOCKER02), allowed)
        self.assertIn("&lt;details open&gt;", normalize("<details open>", article_id=DOCKER02))
        curation = (ROOT / "src/content-curation" / f"{DOCKER02}.md").read_text(encoding="utf-8").strip()
        page = (ROOT / "src/content/knowledge" / f"{DOCKER02}.md").read_text(encoding="utf-8").split("---", 2)[2].strip()
        once = normalize(curation, article_id=DOCKER02)
        twice = normalize(once, article_id=DOCKER02)
        self.assertEqual(once, page)
        self.assertEqual(twice, page)
        self.assertIn("<details>", page)
        self.assertIn(allowed, page)
        self.assertNotIn("**对上了什么：**", page)

    def test_docker03_fold_and_old_anchor_survive_and_body_matches(self):
        source = "<details>\n<summary>展开镜像命令副作用表</summary>\n\n正文 <FILE_OBJECT>\n\n</details>"
        result = normalize(source, article_id=DOCKER03)
        self.assertIn("<details>\n<summary>展开镜像命令副作用表</summary>", result)
        self.assertIn("&lt;FILE_OBJECT&gt;", result)
        allowed = '<span id="02-docker-镜像结构与取证"></span>'
        self.assertEqual(normalize(allowed, article_id=DOCKER03), allowed)
        self.assertIn("&lt;details open&gt;", normalize("<details open>", article_id=DOCKER03))
        curation = (ROOT / "src/content-curation" / f"{DOCKER03}.md").read_text(encoding="utf-8").strip()
        page = (ROOT / "src/content/knowledge" / f"{DOCKER03}.md").read_text(encoding="utf-8").split("---", 2)[2].strip()
        once = normalize(curation, article_id=DOCKER03)
        twice = normalize(once, article_id=DOCKER03)
        self.assertEqual(once, page)
        self.assertEqual(twice, page)
        self.assertIn("<details>", page)
        self.assertIn(allowed, page)
        self.assertNotIn("这次要留下的结论", page)
        self.assertNotIn("**对上了什么：**", page)

    def test_docker04_fold_and_old_anchor_survive_and_body_matches(self):
        source = "<details>\n<summary>展开数据根子目录总览表</summary>\n\n正文 <FILE_OBJECT>\n\n</details>"
        result = normalize(source, article_id=DOCKER04)
        self.assertIn("<details>\n<summary>展开数据根子目录总览表</summary>", result)
        self.assertIn("&lt;FILE_OBJECT&gt;", result)
        allowed = '<span id="02-docker-日志分析"></span>'
        self.assertEqual(normalize(allowed, article_id=DOCKER04), allowed)
        self.assertIn("&lt;details open&gt;", normalize("<details open>", article_id=DOCKER04))
        curation = (ROOT / "src/content-curation" / f"{DOCKER04}.md").read_text(encoding="utf-8").strip()
        page = (ROOT / "src/content/knowledge" / f"{DOCKER04}.md").read_text(encoding="utf-8").split("---", 2)[2].strip()
        once = normalize(curation, article_id=DOCKER04)
        twice = normalize(once, article_id=DOCKER04)
        self.assertEqual(once, page)
        self.assertEqual(twice, page)
        self.assertIn("<details>", page)
        self.assertIn(allowed, page)
        self.assertNotIn("这次要留下的结论", page)
        self.assertNotIn("**对上了什么：**", page)

    def test_docker05_fold_and_old_anchor_survive_and_body_matches(self):
        source = "<details>\n<summary>展开网络命令副作用表</summary>\n\n正文 <FILE_OBJECT>\n\n</details>"
        result = normalize(source, article_id=DOCKER05)
        self.assertIn("<details>\n<summary>展开网络命令副作用表</summary>", result)
        self.assertIn("&lt;FILE_OBJECT&gt;", result)
        allowed = '<span id="02-docker-网络分析命令"></span>'
        self.assertEqual(normalize(allowed, article_id=DOCKER05), allowed)
        self.assertIn("&lt;details open&gt;", normalize("<details open>", article_id=DOCKER05))
        curation = (ROOT / "src/content-curation" / f"{DOCKER05}.md").read_text(encoding="utf-8").strip()
        page = (ROOT / "src/content/knowledge" / f"{DOCKER05}.md").read_text(encoding="utf-8").split("---", 2)[2].strip()
        once = normalize(curation, article_id=DOCKER05)
        twice = normalize(once, article_id=DOCKER05)
        self.assertEqual(once, page)
        self.assertEqual(twice, page)
        self.assertIn("<details>", page)
        self.assertIn(allowed, page)
        self.assertNotIn("这次要留下的结论", page)
        self.assertNotIn("**对上了什么：**", page)

    def test_git03_fold_and_old_anchor_survive_and_body_matches(self):
        source = "<details>\n<summary>展开首轮判读表</summary>\n\n正文 <FILE_OBJECT>\n\n</details>"
        result = normalize(source, article_id=GIT03)
        self.assertIn("<details>\n<summary>展开首轮判读表</summary>", result)
        self.assertIn("&lt;FILE_OBJECT&gt;", result)
        allowed = '<span id="02-git-元数据与泄露判断"></span>'
        self.assertEqual(normalize(allowed, article_id=GIT03), allowed)
        self.assertIn("&lt;details open&gt;", normalize("<details open>", article_id=GIT03))
        curation = (ROOT / "src/content-curation" / f"{GIT03}.md").read_text(encoding="utf-8").strip()
        page = (ROOT / "src/content/knowledge" / f"{GIT03}.md").read_text(encoding="utf-8").split("---", 2)[2].strip()
        once = normalize(curation, article_id=GIT03)
        twice = normalize(once, article_id=GIT03)
        self.assertEqual(once, page)
        self.assertEqual(twice, page)
        self.assertIn("<details>", page)
        self.assertIn(allowed, page)
        self.assertNotIn("这次要留下的结论", page)
        self.assertNotIn("**对上了什么：**", page)

    def test_git04_to_08_fold_and_old_anchor_survive_and_body_matches(self):
        expected_anchors = {
            "git-docker-04": '<span id="01-提交记录与全局视图"></span>',
            "git-docker-05": '<span id="01-log-与-reflog"></span>',
            "git-docker-06": '<span id="01-git-对象模型"></span>',
            "git-docker-07": '<span id="01-分支与远程跟踪引用"></span>',
            "git-docker-08": '<span id="01-材料目录与首轮保全"></span>',
            "forensic-kubernetes-cluster": '<span id="01-阅读路线与取证主线"></span>',
            "forensic-cloud-vm": '<span id="01-先画资源边界"></span>',
        }
        for aid, allowed in expected_anchors.items():
            with self.subTest(aid=aid):
                self.assertEqual(normalize(allowed, article_id=aid), allowed)
                self.assertIn("&lt;details open&gt;", normalize("<details open>", article_id=aid))
                curation = (ROOT / "src/content-curation" / f"{aid}.md").read_text(encoding="utf-8").strip()
                page = (ROOT / "src/content/knowledge" / f"{aid}.md").read_text(encoding="utf-8").split("---", 2)[2].strip()
                once = normalize(curation, article_id=aid)
                twice = normalize(once, article_id=aid)
                self.assertEqual(once, page)
                self.assertEqual(twice, page)
                self.assertIn("<details>", page)
                self.assertIn(allowed, page)
                self.assertNotIn("这次要留下的结论", page)
                self.assertNotIn("**对上了什么：**", page)

    def test_panel_body_is_stable_after_two_normalizations_and_matches_page(self):
        curation = (ROOT / "src/content-curation" / f"{PANEL}.md").read_text(encoding="utf-8").strip()
        page = (ROOT / "src/content/knowledge" / f"{PANEL}.md").read_text(encoding="utf-8").split("---", 2)[2].strip()
        once = normalize(curation, article_id=PANEL)
        twice = normalize(once, article_id=PANEL)
        self.assertEqual(once, page)
        self.assertEqual(twice, page)
        self.assertIn("<details>", page)
        self.assertIn('<span id="02-宝塔常见数据落点"></span>', page)
        self.assertNotIn("这次要留下的结论", page)
        self.assertNotIn("**对上了什么：**", page)


if __name__ == "__main__":
    unittest.main()
