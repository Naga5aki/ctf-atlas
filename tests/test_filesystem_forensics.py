import hashlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IDS = [
    "forensic-fs-volume",
    "forensic-fs-ntfs",
    "forensic-fs-fat",
    "forensic-fs-exfat",
    "forensic-fs-ext",
    "forensic-fs-other",
    "forensic-fs-gui",
]
TOPICS = {
    "forensic-fs-volume": "卷与引导扇区",
    "forensic-fs-ntfs": "NTFS",
    "forensic-fs-fat": "FAT",
    "forensic-fs-exfat": "exFAT",
    "forensic-fs-ext": "ext",
    "forensic-fs-other": "其他文件系统",
    "forensic-fs-gui": "图形工具",
}


class FilesystemForensicsTests(unittest.TestCase):
    def body(self, ident):
        curation = (ROOT / "src/content-curation" / f"{ident}.md").read_text(encoding="utf-8")
        knowledge = (ROOT / "src/content/knowledge" / f"{ident}.md").read_text(encoding="utf-8")
        self.assertNotIn("\r", curation)
        self.assertNotIn("\r", knowledge)
        page = knowledge.split("---", 2)[2].strip()
        self.assertEqual(page, curation.strip())
        return page

    def test_cluster_lists_one_page_per_filesystem(self):
        taxonomy = (ROOT / "src/data/forensics-taxonomy.ts").read_text(encoding="utf-8")
        computer = taxonomy.split("id: 'computer'", 1)[1].split("id: 'memory'", 1)[0]
        self.assertIn(
            "{ name: '文件系统取证', topics: ['卷与引导扇区', 'NTFS', 'FAT', 'exFAT', 'ext', '其他文件系统', '图形工具'] }",
            computer,
        )
        self.assertIn("{ name: '磁盘与文件系统', topics: ['镜像与文件系统'] }", computer)

    def test_pages_stay_under_computer_forensics(self):
        for ident, topic in TOPICS.items():
            meta = (ROOT / "src/content/knowledge" / f"{ident}.md").read_text(encoding="utf-8").split("---", 2)[1]
            self.assertIn("module: Forensics", meta)
            self.assertIn("track: 计算机取证", meta)
            self.assertIn(f"topic: {topic}", meta)
            self.assertIn("tags: [文件系统]", meta)
            body = self.body(ident)
            self.assertIn("实战", body)
            self.assertRegex(body, r"验证|核验|复核")
            numbers = [int(item) for item in re.findall(r"(?m)^## (\d+)\s", body)]
            self.assertEqual(numbers, list(range(1, len(numbers) + 1)))

    def test_required_corrections_are_present(self):
        ntfs = self.body("forensic-fs-ntfs")
        self.assertIn("0xF6", ntfs)
        self.assertIn("4096", ntfs)
        self.assertIn("21 02 00 05 11 01 F0 00", ntfs)
        self.assertIn("1264", ntfs)
        self.assertNotIn("istat -o \"$start\" disk.dd 49-7", ntfs)
        fat = self.body("forensic-fs-fat")
        self.assertIn("虚拟元数据地址", fat)
        self.assertIn("FF D9", fat)
        ext = self.body("forensic-fs-ext")
        self.assertIn("--output-dir ./work/ext-recovery/", ext)
        self.assertIn("`0x6C`", ext)
        self.assertNotIn("这里不是文件大小", ext.replace("generation。这里不是文件大小", ""))
        exfat = self.body("forensic-fs-exfat")
        self.assertIn("`0x6C`", exfat)
        self.assertIn("`0x6D`", exfat)
        self.assertIn("0xA0", exfat)
        volume = self.body("forensic-fs-volume")
        self.assertIn("F8 FF FF 0F", volume)
        self.assertIn("46 49 4C 45", volume)
