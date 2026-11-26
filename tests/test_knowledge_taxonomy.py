"""Keep the visible knowledge index in a small, predictable set of topics."""

from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
TOPICS = {
    "Web": {"协议与抓包", "Web漏洞", "源码与环境"},
    "Misc": {"文件结构与提取", "图像与视觉", "压缩与口令", "文本与编码", "音频与信号", "流量与网络", "文档与取证"},
    "Reverse": {"程序结构", "逻辑逆推", "验证与复现"},
    "Crypto": {"参数与表示", "公钥密码", "对称与实现"},
}


def frontmatter_value(text: str, key: str) -> str | None:
    head = text.split("---", 2)[1]
    match = re.search(rf"(?m)^{key}:\s*(.*?)\s*$", head)
    return match.group(1).strip("\"'") if match else None


class KnowledgeTaxonomyTest(unittest.TestCase):
    def test_each_non_forensics_article_has_a_clear_module_topic(self):
        misplaced = []
        for path in (ROOT / "src/content/knowledge").glob("*.md"):
            text = path.read_text(encoding="utf-8")
            module = frontmatter_value(text, "module")
            if module in TOPICS:
                topic = frontmatter_value(text, "topic")
                if topic not in TOPICS[module]:
                    misplaced.append(f"{path.name}: {module} / {topic}")
        self.assertEqual([], misplaced)


if __name__ == "__main__":
    unittest.main()
