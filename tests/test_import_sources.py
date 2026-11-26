import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.import_sources import build_external_links, build_inventory, classify_archive


class ImportSourcesTests(unittest.TestCase):
    def test_classifies_competition_directories_without_forcing_pwn_into_five_modules(self):
        self.assertEqual(classify_archive(Path("Misc题收集/HKCERT CTF 2025/Web Exploitation/nettool/nettool.zip")), "Web")
        self.assertEqual(classify_archive(Path("Misc题收集/HKCERT CTF 2025/Binary Exploitation/stop/stop.zip")), "Archive")
        self.assertEqual(classify_archive(Path("Misc题收集/“古剑山”/Crypto/Crypto-sol.zip")), "Crypto")

    def test_inventory_keeps_every_file_and_stable_ids(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            item = root / "Misc题收集" / "比赛" / "Misc" / "Misc-test.zip"
            item.parent.mkdir(parents=True)
            with zipfile.ZipFile(item, "w") as archive:
                archive.writestr("hello.txt", "hello")
            note = root / "guide.md"
            note.write_text("# Hello\nBody", encoding="utf-8")
            first = build_inventory(root)
            second = build_inventory(root)
            self.assertEqual(len(first), 2)
            self.assertEqual([entry["id"] for entry in first], [entry["id"] for entry in second])
            self.assertEqual({entry["kind"] for entry in first}, {"challenge", "source"})
            self.assertTrue(all(entry["sha256"] for entry in first))

    def test_external_wp_links_are_kept_without_importing_wp_text(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            contest = root / "Misc题收集" / "比赛"
            contest.mkdir(parents=True)
            (contest / "wp.txt").write_text("https://example.org/wp\n", encoding="utf-8")
            rows = build_inventory(root)
            links = build_external_links(root, rows)
            self.assertEqual(list(links.values()), ["https://example.org/wp"])


if __name__ == "__main__":
    unittest.main()
