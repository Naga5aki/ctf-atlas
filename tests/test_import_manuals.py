import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SITE = Path(__file__).resolve().parents[1]
ROOT = SITE.parent
sys.path.insert(0, str(SITE / "scripts"))


class ManualImportTests(unittest.TestCase):
    def test_every_catalog_location_exists_and_excludes_project_metadata(self):
        items = json.loads((SITE / "src/data/tool-inventory.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(items), 140)
        self.assertTrue(all(Path(item["path"]).exists() for item in items))
        self.assertEqual(len({item["id"] for item in items}), len(items))
        self.assertFalse(any(".git" in Path(item["path"]).parts for item in items))
        self.assertEqual({item["module"] for item in items}, {"Web", "Misc", "Reverse", "Crypto", "Forensics"})

    def test_major_sections_are_present(self):
        notes = SITE / "src/content/knowledge"
        tools = SITE / "src/content/tools"
        self.assertEqual(len(list(notes.glob("misc-note-*.md"))), 82)
        self.assertEqual(len(list(notes.glob("docker-case-*.md"))), 0)
        self.assertEqual(len(list(notes.glob("docker-evidence-*.md"))), 5)
        self.assertEqual(len(list(notes.glob("fic-case-*.md"))), 14)
        self.assertEqual(len(list(notes.glob("forensic-method-*.md"))), 2)
        self.assertEqual(len(list(notes.glob("git-docker-*.md"))), 6)
        self.assertEqual(len(list(tools.glob("misc-tool-*.md"))), 67)

    def test_curated_misc_pages_survive_reimport(self):
        from import_manuals import ROOT, curate_misc_note, sections_from_document

        sections = {
            section["id"]: section
            for section in sections_from_document(ROOT / "Misc知识总结.docx", "misc-note", False)
        }
        for identifier in ("misc-note-54", "misc-note-71"):
            original = "\n\n".join(sections[identifier]["parts"]).strip()
            expected = curate_misc_note(identifier, original)
            rendered = (SITE / "src/content/knowledge" / f"{identifier}.md").read_text(encoding="utf-8").split("---", 2)[2].strip()
            self.assertEqual(rendered, expected, identifier)
        self.assertEqual(expected.count("!["), 7)

    def test_word_command_comments_do_not_create_article_titles(self):
        from import_manuals import sections_from_document

        for name, prefix, is_tool in [
            ("Misc知识总结.docx", "misc-note", False),
            ("Misc工具1.docx", "misc-tool", True),
        ]:
            for section in sections_from_document(ROOT / name, prefix, is_tool):
                for part in section["parts"]:
                    self.assertFalse(re.search(r"(?m)^# [^#]", part), section["id"])
        self.assertIn("\\# ImageMagick 7 (Windows)",
                      "\n".join(sections_from_document(ROOT / "Misc知识总结.docx", "misc-note", False)[52]["parts"]))
        self.assertIn("1.png → 10.png → 11.png → 2.png → 3.png",
                      "\n".join(sections_from_document(ROOT / "Misc知识总结.docx", "misc-note", False)[52]["parts"]))
        self.assertNotIn("### 1.png →", "\n".join(
            sections_from_document(ROOT / "Misc知识总结.docx", "misc-note", False)[52]["parts"]))

    def test_forensic_pilot_rewrite_survives_reimport_without_restoring_case_references(self):
        from import_manuals import CURATION, curate_forensic_note, markdown_sections, normalize_forensic_markdown, relocate_fic_container_detail

        section = markdown_sections(ROOT / "取证/2026FIC初赛-取证知识点-模块化复习手册.md")[2]
        original = "\n".join(section["body"]).strip()
        relocated, transfer = relocate_fic_container_detail("fic-case-03", original)
        expected = normalize_forensic_markdown(curate_forensic_note("fic-case-03", relocated), article_id="fic-case-03")
        rendered = (SITE / "src/content/knowledge/fic-case-03.md").read_text(encoding="utf-8").split("---", 2)[2].strip()
        self.assertEqual(rendered, expected)
        self.assertEqual(expected, (CURATION / "fic-case-03.md").read_text(encoding="utf-8").strip())
        self.assertIsNotNone(transfer)
        self.assertEqual(transfer[0], "docker-evidence-01")
        self.assertNotRegex(rendered, r"题例|服(?:全卷|\d+)|计\d+|网\d+|判题|答案")
        self.assertGreater(len(rendered), len(relocated))
        self.assertEqual(curate_forensic_note("forensic-unmaintained-example", original), original)

    def test_complete_curation_applies_only_to_forensics_and_preserves_metadata(self):
        import import_manuals

        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            notes, curation = base / "notes", base / "curation"
            notes.mkdir()
            curation.mkdir()
            metadata = 'title: "示例"\nmodule: "Forensics"\ntrack: "计算机取证"\ntopic: "内存与程序"\nsourceIds: ["internal"]\nrelatedIds: ["retained-link"]\nupdated: "2026-09-29"'
            forensic = notes / "forensic-example.md"
            forensic.write_text(f"---\n{metadata}\n---\n\n旧正文\n", encoding="utf-8")
            misc = notes / "misc-example.md"
            unchanged = '---\ntitle: "Misc"\nmodule: Misc\n---\n\n原有正文\n'
            misc.write_text(unchanged, encoding="utf-8")
            replacement = "## 01 独立实战\n\n保留步骤与验证。\n"
            (curation / forensic.name).write_text(replacement, encoding="utf-8")
            (curation / misc.name).write_text("不应应用", encoding="utf-8")
            with patch.object(import_manuals, "NOTES", notes), patch.object(import_manuals, "CURATION", curation):
                self.assertEqual(import_manuals.apply_forensics_curation(), 1)
                self.assertEqual(import_manuals.apply_forensics_curation(), 1)
                result = forensic.read_text(encoding="utf-8")
                self.assertEqual(result.split("---", 2)[2].strip(), replacement.strip())
                for field in metadata.splitlines()[:-1]:
                    self.assertIn(field, result)
                self.assertIn('updated: "2026-10-01"', result)
                self.assertEqual(misc.read_text(encoding="utf-8"), unchanged)
                (curation / forensic.name).write_text(" \n", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "Empty forensic curation"):
                    import_manuals.apply_forensics_curation()

    def test_catalog_disclosures_survive_import_without_hiding_placeholders(self):
        import import_manuals

        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            notes, curation = base / 'notes', base / 'curation'
            notes.mkdir()
            curation.mkdir()
            source = '<details>\n<summary>参数</summary>\n\n对象 <FILE_OBJECT>\n\n</details>\n\n<summary onclick="run()">字面标签</summary>\n'
            for identifier in ('forensic-memory-volatility', 'forensic-example'):
                (notes / f'{identifier}.md').write_text('---\ntitle: "示例"\nmodule: "Forensics"\n---\n\n旧正文\n', encoding='utf-8')
                (curation / f'{identifier}.md').write_text(source, encoding='utf-8')
            with patch.object(import_manuals, 'NOTES', notes), patch.object(import_manuals, 'CURATION', curation):
                import_manuals.apply_forensics_curation()
            catalog = (notes / 'forensic-memory-volatility.md').read_text('utf-8')
            ordinary = (notes / 'forensic-example.md').read_text('utf-8')
            self.assertIn('<details>\n<summary>参数</summary>', catalog)
            self.assertIn('&lt;FILE_OBJECT&gt;', catalog)
            self.assertIn('&lt;summary onclick="run()"&gt;', catalog)
            self.assertIn('&lt;details&gt;', ordinary)

    def test_all_forensics_bodies_are_independent_and_survive_curation(self):
        from import_manuals import CURATION, normalize_forensic_markdown

        articles = []
        for path in (SITE / "src/content/knowledge").glob("*.md"):
            text = path.read_text(encoding="utf-8")
            if not re.search(r'^module:\s*["\']?Forensics["\']?$', text, re.MULTILINE):
                continue
            articles.append(path)
            body = text.split("---", 2)[2].strip()
            guide = CURATION / path.name
            self.assertTrue(guide.is_file(), path.name)
            self.assertEqual(body, normalize_forensic_markdown(guide.read_text(encoding="utf-8").strip(), article_id=path.stem), path.name)
            self.assertNotRegex(body, r"题例|FIC\s*2026|2026\s*FIC|本题|本卷|该题组|判题|题号|(?:服|计|网)[（(]?[0-9一二三四五六七八九十]+|强网杯|strange_forensics|flag\^galf|Symbolic Needs|oh-my-linux", path.name)
            self.assertEqual(len(re.findall(r"(?m)^\s*```", body)) % 2, 0, path.name)
            self.assertIn("实战", body, path.name)
            self.assertRegex(body, r"验证|核验|复核", path.name)
            sections = re.findall(r"(?m)^## (\d+)\s", body)
            self.assertEqual([int(number) for number in sections], list(range(1, len(sections) + 1)), path.name)
            prose = re.sub(r"(?ms)^```[^\n]*\n.*?^```[ \t]*$", "", body)
            self.assertNotRegex(prose, r"(?m)^# [^#]", path.name)
        registry = json.loads((SITE / "src/data/forensics-supplements.json").read_text(encoding="utf-8"))
        # Supplemental metadata may override a generated FIC page without adding a page.
        supplemental_ids = {row["id"] for row in registry["articles"]}
        metadata_override_ids = {f"fic-case-{number:02d}" for number in range(1, 15)} | {"forensic-memory", "forensic-memory-unix"}
        self.assertEqual(len(articles), 63 + len(supplemental_ids - metadata_override_ids))

    def test_supplement_import_is_durable_and_checks_provenance_before_writing(self):
        import import_manuals

        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            notes, guides, data = (base / name for name in ("notes", "guides", "data"))
            for path in (notes, guides, data):
                path.mkdir()
            existing = notes / "existing.md"
            existing.write_text('---\ntitle: 示例\nmodule: Forensics\ntrack: 计算机取证\nsourceIds: [retained]\n---\n\n既有正文\n', encoding="utf-8")
            (guides / "wireless.md").write_text('## 01 独立实战\n\n验证记录。\n', encoding="utf-8")
            (data / "inventory.json").write_text(json.dumps([{"kind": "source", "relativePath": "folder/new.md", "id": "new-source"}]), encoding="utf-8")
            registry = {"sources": [{"relativePath": "folder/new.md", "articleIds": ["existing", "wireless"]}],
                        "articles": [{"id": "wireless", "title": "无线", "module": "Forensics", "sourceIds": []}]}
            registry_path = data / "forensics-supplements.json"
            registry_path.write_text(json.dumps(registry), encoding="utf-8")
            with patch.object(import_manuals, "NOTES", notes), patch.object(import_manuals, "CURATION", guides), patch.object(import_manuals, "DATA", data):
                self.assertEqual(import_manuals.apply_forensics_supplements(), 1)
                before = {path.name: path.read_bytes() for path in notes.glob("*.md")}
                self.assertEqual(import_manuals.apply_forensics_supplements(), 0)
                self.assertEqual(before, {path.name: path.read_bytes() for path in notes.glob("*.md")})
                body, metadata = import_manuals._body_and_meta(existing)
                self.assertEqual(body, "既有正文")
                self.assertEqual(metadata["sourceIds"], ["retained", "new-source"])
                self.assertIn("track: 计算机取证", existing.read_text(encoding="utf-8"))
                registry["sources"][0]["articleIds"].append("missing")
                registry_path.write_text(json.dumps(registry), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "Unknown supplemental association"):
                    import_manuals.apply_forensics_supplements()
                self.assertEqual(before, {path.name: path.read_bytes() for path in notes.glob("*.md")})

    def test_imported_summaries_are_short_but_body_is_kept(self):
        from import_manuals import sections_from_document, summary_for

        for name, prefix, is_tool in [
            ("Misc知识总结.docx", "misc-note", False),
            ("Misc工具1.docx", "misc-tool", True),
        ]:
            for section in sections_from_document(ROOT / name, prefix, is_tool):
                self.assertLessEqual(len(summary_for(section["parts"], section["title"])), 85,
                                     section["id"])

    def test_forensics_articles_have_clear_two_level_categories(self):
        categories = {
            "计算机取证": {"镜像与文件系统", "卷与引导扇区", "NTFS", "FAT", "exFAT", "ext", "其他文件系统", "图形工具", "系统与用户痕迹", "程序与恶意代码"},
            "内存取证": {"采集与识别", "进程与攻击行为", "对象与数据恢复", "Linux 与 macOS", "工具参数与插件", "综合实战"},
            "服务器取证": {"主机与服务", "Web 与数据库", "网站重构", "Docker 与容器", "服务器集群", "版本与源码", "云与虚拟化"},
            "手机取证": {"Android 原理与流程", "Android", "Android 工具与实战", "iOS 与备份", "iOS 原理与流程", "iOS 工具与实战", "应用与通信"},
            "网络取证": {"流量与协议", "连接与隧道"},
            "虚拟币取证": {"基础与证据", "钱包与本地痕迹", "UTXO 交易", "账户链与代币", "平台与资金追踪", "账本复核与实战"},
            "文件与多媒体取证": {"文件恢复与格式", "文档与隐写", "图像音视频"},
            "综合取证": {"证据保全与流程", "时间线与关联", "密码与资金", "工具与路径"},
        }
        covered = set()
        articles = []
        for path in (SITE / "src/content/knowledge").glob("*.md"):
            text = path.read_text(encoding="utf-8")
            if not re.search(r'^module: ["]?Forensics', text, re.MULTILINE):
                continue
            track = re.search(r'^track: ["]?([^"\n]+)', text, re.MULTILINE)
            topic = re.search(r'^topic: ["]?([^"\n]+)', text, re.MULTILINE)
            self.assertIsNotNone(track, path.name)
            self.assertIsNotNone(topic, path.name)
            self.assertIn(track.group(1), categories, path.name)
            self.assertIn(topic.group(1), categories[track.group(1)], path.name)
            covered.add((track.group(1), topic.group(1)))
            articles.append(path)
        self.assertGreaterEqual(len(articles), 43)
        self.assertEqual(covered, {(track, topic) for track, topics in categories.items() for topic in topics})

    def test_docker_sections_are_consolidated_without_dropping_body_text(self):
        import import_manuals
        from import_manuals import DOCKER_ARCHIVE, DOCKER_GROUPS, _body_and_meta, _nested_headings, forensics_title, frontmatter, markdown_sections, normalize_forensic_markdown, sections_from_document

        notes = SITE / "src/content/knowledge"
        bodies = {}
        for index, section in enumerate(markdown_sections(ROOT / "Docker_服务器取证信息定位指南.md"), 1):
            identifier = f"docker-case-{index:02d}"
            body = "\n".join(section["body"]).strip().replace("源文件", "输入文件")
            if index == 1:
                body = re.sub(r"^# [^\n]+\n+", "", body, count=1)
            bodies[identifier] = (forensics_title(identifier, section["title"]), normalize_forensic_markdown(body))
        for section in sections_from_document(ROOT / "_Git_Docker实战命令手册.docx", "git-docker", False):
            identifier = section["id"]
            if identifier == "git-docker-02" or (identifier.startswith("git-docker-") and 9 <= int(identifier[-2:]) <= 24):
                bodies[identifier] = (forensics_title(identifier, section["title"]), normalize_forensic_markdown("\n\n".join(section["parts"]).strip()))
        with tempfile.TemporaryDirectory() as directory:
            temporary_notes = Path(directory)
            for identifier, (title, body) in bodies.items():
                metadata = frontmatter({"title": title, "module": "Forensics", "sourceIds": ["internal"]})
                (temporary_notes / f"{identifier}.md").write_text(metadata + "\n\n" + body, encoding="utf-8")
            with patch.object(import_manuals, "NOTES", temporary_notes):
                import_manuals.consolidate_docker_pages({}, "internal-fic")
            for group in DOCKER_GROUPS:
                merged = (temporary_notes / f"{group['id']}.md").read_text(encoding="utf-8")
                identifiers = [*group.get("archive", []), *group["ids"]]
                for index, identifier in enumerate(identifiers, 1):
                    if identifier in group.get("archive", []):
                        body, _ = _body_and_meta(DOCKER_ARCHIVE / f"{identifier}.md")
                        self.assertIn(_nested_headings(normalize_forensic_markdown(body), index), merged, identifier)
                        continue
                    title, body = bodies[identifier]
                    self.assertIn(title, merged)
                    self.assertIn(_nested_headings(body, index), merged, identifier)
        self.assertNotIn("–no-trunc", (notes / "docker-evidence-02.md").read_text(encoding="utf-8"))

    def test_container_details_have_one_home_and_contextual_backlinks(self):
        notes = SITE / "src/content/knowledge"
        moved = {
            "fic-case-03.md": ("docker-evidence-01.md", "按元数据独立识别 Docker 与 LXC", "模板"),
            "fic-case-10.md": ("docker-evidence-05.md", "容器网桥与通信归属", "桥名、子网和 DHCP 服务都可以修改"),
            "fic-case-13.md": ("docker-evidence-02.md", "容器地址归属核对（回链主线）", "app-db LXC 租约识别的完整主线"),
        }
        for article, (destination, heading, retained_detail) in moved.items():
            original_location = (notes / article).read_text(encoding="utf-8")
            canonical = (notes / destination).read_text(encoding="utf-8")
            self.assertIn(f"/knowledge/{destination[:-3]}/", original_location)
            self.assertIn(heading, canonical)
            self.assertIn(retained_detail, canonical)
        self.assertNotIn("| Docker | LXC / LXD |", (notes / "fic-case-03.md").read_text(encoding="utf-8"))
        self.assertNotIn("| `docker ps` |", (notes / "fic-case-13.md").read_text(encoding="utf-8"))
        self.assertNotIn("- Docker：`docker0`", (notes / "fic-case-10.md").read_text(encoding="utf-8"))
        self.assertIn('track: "服务器取证"', (notes / "fic-case-03.md").read_text(encoding="utf-8"))
        self.assertNotIn("排除 Docker（其网段为 172.x）", (notes / "docker-evidence-05.md").read_text(encoding="utf-8"))

    def test_overlapping_methods_merge_without_losing_examples(self):
        import import_manuals
        from import_manuals import METHOD_GROUPS, _nested_headings, frontmatter, markdown_sections, normalize_forensic_markdown

        sections = markdown_sections(ROOT / "取证/2026FIC初赛-取证知识点-模块化复习手册.md")
        notes = SITE / "src/content/knowledge"
        with tempfile.TemporaryDirectory() as directory:
            temporary_notes = Path(directory)
            for group in METHOD_GROUPS:
                for identifier in group["ids"]:
                    source = "\n".join(sections[int(identifier[-2:]) - 1]["body"]).strip().replace("源文件", "输入文件")
                    metadata = frontmatter({"title": identifier, "module": "Forensics", "sourceIds": ["internal"]})
                    (temporary_notes / f"{identifier}.md").write_text(metadata + "\n\n" + normalize_forensic_markdown(source), encoding="utf-8")
            with patch.object(import_manuals, "NOTES", temporary_notes):
                import_manuals.consolidate_method_pages()
            for group in METHOD_GROUPS:
                merged = (temporary_notes / f"{group['id']}.md").read_text(encoding="utf-8")
                for index, identifier in enumerate(group["ids"], 1):
                    self.assertFalse((notes / f"{identifier}.md").exists())
                    source = "\n".join(sections[int(identifier[-2:]) - 1]["body"]).strip().replace("源文件", "输入文件")
                    self.assertIn(_nested_headings(normalize_forensic_markdown(source), index), merged)

    def test_word_paragraphs_and_table_cells_survive_conversion(self):
        from import_manuals import MISC_NOTE_54_CORRECTIONS

        try:
            from docx import Document
        except ImportError:
            self.skipTest("python-docx is needed for a full source-content audit")
        for name, folder, pattern in [
            ("Misc知识总结.docx", "knowledge", "misc-note-*.md"),
            ("Misc工具1.docx", "tools", "misc-tool-*.md"),
        ]:
            document = Document(ROOT / name)
            merged = "\n".join(path.read_text(encoding="utf-8") for path in (SITE / "src/content" / folder).glob(pattern))
            plain = re.sub(r"\*\*([^*]{2,15}[：:])\*\*", r"\1", merged).replace("#### ", "").replace("### ", "")
            plain = re.sub(r"([：:])\s+", r"\1", plain)
            current_section = ""
            for paragraph in document.paragraphs:
                if paragraph.style.name == "Heading 1":
                    current_section = paragraph.text.strip()
                value = paragraph.text.strip().replace("源文件", "输入文件")
                if value and paragraph.style.name != "Heading 1":
                    if "TTL隐写" in current_section:
                        for old, corrected in MISC_NOTE_54_CORRECTIONS.items():
                            value = value.replace(old, corrected)
                        if paragraph.style.name == "Heading 2":
                            value = re.sub(r"^[一二三四五六七八九十]+[、.]\s*", "", value)
                        value = re.sub(r"^(\d+)\.(\S)", r"\1. \2", value)
                    normalized = re.sub(r"([：:])\s+", r"\1", value)
                    self.assertTrue(normalized in plain or normalized.replace("\n", "  \n") in plain, value[:80])
            for table in document.tables:
                for row in table.rows:
                    for cell in row.cells:
                        value = cell.text.strip().replace("源文件", "输入文件")
                        if value:
                            self.assertIn(value.replace("|", "\\|").replace("\n", "<br>"), merged)


if __name__ == "__main__":
    unittest.main()
