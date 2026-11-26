"""Check the built local site for missing links and unpublished material labels."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit


SITE = Path(__file__).resolve().parents[1]
DIST = SITE / "dist"
FORBIDDEN = ("源文件", "原始资料", "原 WP", "本卷", "Misc工具1", "Misc知识总结", "模块化复习手册", "_Git_Docker实战命令手册", "专项笔记", "数证杯")

# User explicitly requested real competition provenance in this iOS article.
# All other forbidden terms and all other pages retain the original checks.
CONTEST_PROVENANCE_PAGES = {"/knowledge/forensic-ios-forensics/index.html", "/knowledge/forensic-android-forensics/index.html"}


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self.ids: set[str] = set()
        self.visible: list[str] = []
        self.hidden_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        values = dict(attrs)
        if tag in {"script", "style", "head"}:
            self.hidden_depth += 1
        identifier = values.get("id")
        if identifier:
            self.ids.add(identifier)
        for attr in ("href", "src"):
            if values.get(attr):
                self.links.append(values[attr])

    def handle_endtag(self, tag: str):
        if tag in {"script", "style", "head"}:
            self.hidden_depth = max(0, self.hidden_depth - 1)

    def handle_data(self, data: str):
        if not self.hidden_depth:
            self.visible.append(data)


def target_file(url: str) -> Path | None:
    path = unquote(urlsplit(url).path)
    if not path.startswith("/"):
        return None
    return DIST / path.lstrip("/") / "index.html" if path.endswith("/") else DIST / path.lstrip("/")


def main() -> int:
    pages: dict[str, Page] = {}
    for path in DIST.rglob("*.html"):
        page = Page()
        page.feed(path.read_text(encoding="utf-8"))
        pages["/" + path.relative_to(DIST).as_posix()] = page

    errors: list[str] = []
    links_checked = 0
    for source, page in pages.items():
        visible = " ".join(page.visible)
        for term in FORBIDDEN:
            if term == "数证杯" and source in CONTEST_PROVENANCE_PAGES:
                continue
            if term in visible:
                errors.append(f"{source}: forbidden visible term {term}")
        for href in page.links:
            parsed = urlsplit(urljoin("http://local" + source, href))
            if parsed.netloc != "local" or parsed.scheme not in {"http", "https"}:
                continue
            target = target_file(parsed.path)
            if target is None:
                continue
            links_checked += 1
            if not target.is_file():
                errors.append(f"{source}: missing {href}")
                continue
            if parsed.fragment and target.suffix == ".html":
                key = "/" + target.relative_to(DIST).as_posix()
                destination = pages.get(key)
                if destination and unquote(parsed.fragment) not in destination.ids:
                    errors.append(f"{source}: missing anchor {href}")

    article_files = list((SITE / "src/content/knowledge").glob("*.md"))
    for path in article_files:
        text = path.read_text(encoding="utf-8")
        if not re.search(r'^module:\s*["\']?Forensics["\']?$', text, re.MULTILINE):
            continue
        page = pages.get(f"/knowledge/{path.stem}/index.html")
        if page and re.search(r"题例|FIC\s*2026|2026\s*FIC|本题|该题组|题号|判题|(?:服|计|网)[（(]?[0-9一二三四五六七八九十]+|强网杯|strange_forensics|flag\^galf|Symbolic Needs|oh-my-linux", " ".join(page.visible)):
            errors.append(f"Forensics article depends on an exercise: {path.stem}")
    for module in ("Web", "Misc", "Reverse", "Crypto", "Forensics"):
        index = pages[f"/module/{module.lower()}/index.html"]
        linked_articles = {urlsplit(href).path.split("/")[2] for href in index.links if href.startswith("/knowledge/")}
        module_articles = {
            path.stem for path in article_files
            if re.search(rf'^module:\s*["\']?{module}["\']?$', path.read_text(encoding="utf-8"), re.MULTILINE)
        }
        missing_articles = module_articles - linked_articles
        if missing_articles:
            errors.append(f"{module} articles missing from index: " + ", ".join(sorted(missing_articles)))

    tool_index = pages["/tools/index.html"]
    linked_guides = {urlsplit(href).path.split("/")[2] for href in tool_index.links if href.startswith("/tool/")}
    tool_guides = {path.stem for path in (SITE / "src/content/tools").glob("*.md")}
    missing_guides = tool_guides - linked_guides
    if missing_guides:
        errors.append("Tool guides missing from index: " + ", ".join(sorted(missing_guides)))

    print(f"Audited {len(pages)} pages, {links_checked} local links, {len(article_files)} knowledge articles, {len(tool_guides)} tool guides")
    for error in errors[:30]:
        print(error)
    if len(errors) > 30:
        print(f"... and {len(errors) - 30} more errors")
    print(f"Errors: {len(errors)}")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
