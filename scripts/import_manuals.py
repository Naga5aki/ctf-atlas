"""Turn the two personal Word manuals into navigable, full-length site articles.

The source documents and D:\\CTF_MISC_Tools are read only. Generated files stay
inside ctf-atlas; re-running this script refreshes only its own numbered pages.
"""

from __future__ import annotations

import json
import hashlib
import mimetypes
import re
from itertools import count
from pathlib import Path
from urllib.parse import urlsplit
from datetime import date

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph


ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "ctf-atlas"
TOOL_ROOT = Path(r"D:\CTF_MISC_Tools")
NOTES = SITE / "src/content/knowledge"
DOCKER_ARCHIVE = SITE / "src/content-archive/docker"
TOOLS = SITE / "src/content/tools"
MEDIA = SITE / "public/doc-media"
DATA = SITE / "src/data"
CURATION = SITE / "src/content-curation"

MISC_NOTE_54_CORRECTIONS = {
    "TTL自动减1；": "TTL 通常递减，转发要求至少减 1；",
    "TTL=0时数据包丢弃。": "转发途中 TTL 降至 0 时，路由器丢弃该包。",
    "发送端主动自定义数据包初始TTL数值，利用TTL字段承载隐秘信息；接收方提取每个数据包的TTL值，还原原始数据。": "发送端可自定义初始 TTL 以承载信息；分析时需按会话提取观察值并考虑传输路径，再还原候选数据。",
    "每个数据包的TTL十进制值=字符ASCII码": "在未跨路由或已校正跳数时，可尝试将每个包的 TTL 值映射为 ASCII；需回到报文核对。",
    "数字直接当作ASCII码，依次转换为字符；": "只有在采集位置和跳数已明确时，才把校正后的 TTL 当作 ASCII 候选字节；",
    "TTL数值转二进制，按8bit分组，再转文本。": "若按低位或奇偶承载，应先说明取几位、比特顺序与分组长度，再转换为文本。",
    "存在大量独立ICMP/UDP小包，载荷为空或者无意义，信息不在数据包data里，秘密藏在IP头部TTL字段。": "大量独立 ICMP/UDP 小包且载荷很短可以作为候选特征；需对比正常业务流量，确认变化确实发生在 IPv4 TTL 字段。",
    "真实公网跨路由环境下TTL会逐跳减1，隐写失效；CTF题目默认同网段、无路由转发，TTL保持发送原值。": "跨路由采集时，观察到的 TTL 会被逐跳减少；若同一路径的跳数稳定且有独立基准，仍可能还原发送值。不能预设所有题目都在同网段。",
    "默认初始TTL=128，Linux默认TTL=64；隐写流量会出现大量多样化TTL数值，不会固定为64/128。": "部分 Windows、Linux 环境常见初始 TTL 为 128、64，但配置与路径会改变观察值；异常波动只是线索，还需按会话验证。",
    "给出pcap流量包，提取所有TTL序列，转ASCII得到flag；": "给出 PCAP 后，先筛选同一方向的候选序列，再验证 TTL 编码与完整输出；",
    "区分系统默认TTL干扰Windows": "区分常见 TTL 与异常波动",
}


def yaml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def clean_title(text: str, is_tool: bool) -> str:
    if is_tool:
        return re.sub(r"^\d+\s*[.、]\s*", "", text).strip().rstrip(".")
    return re.sub(r"^[（(][一二三四五六七八九十百]+[）)]\s*", "", text).strip()


def topic_for(title: str, is_tool: bool = False) -> str:
    t = title.lower()
    if any(s in t for s in ["流量", "wireshark", "tshark", "dns", "icmp", "snmp", "ntlm", "winrm", "蓝牙", "ceph", "ttl", "端口", "键鼠", "gps", "无线", "kindle", "cobalt", "udp", "network"]):
        return "流量与网络"
    if any(s in t for s in ["音频", "mp3", "midi", "dtmf", "afsk", "pt2242", "mmsstv", "multimon", "sox", "audacity", "sonic", "deepsound", "ffmpeg"]):
        return "音频与信号"
    if any(s in t for s in ["zip", "rar", "7z", "压缩", "爆破", "密码", "口令", "john", "hashcat", "crunch", "fcrack", "bkcrack", "passware", "pdfcrack", "rarcrack", "stegcracker", "stegseek"]):
        return "压缩与口令"
    if any(s in t for s in ["jpg", "jpeg", "png", "apng", "gif", "bmp", "图像", "图片", "像素", "水印", "二维码", "图层", "调色", "拼图", "piet", "bpg", "avif", "stegsolve", "zsteg", "stegdetect", "jphs", "silenteye", "openpuff", "deegger", "paperback", "depix", "montage", "convert", "identify", "zbar", "gnuplot", "tweakpng", "jsteg", "stegpy", "f5-"]):
        return "图像与视觉"
    if any(s in t for s in ["office", "pdf", "宏", "文档", "git", "disk", "磁盘", "testdisk", "oletools", "libreoffice", "alternatestream", "vba", "msoffcrypto", "pdfstream", "wbste", "snow"]):
        return "文档与取证"
    if any(s in t for s in ["base64", "编码", "进制", "异或", "xor", "零宽", "字频", "data uri", "cyberchef", "openssl", "basecrack", "文字", "文本", "ctrl+a"]):
        return "文本与编码"
    return "文件结构与提取"


def summary_for(parts: list[str], title: str) -> str:
    for part in parts:
        value = part.strip().replace("  \n", " ")
        if len(value) >= 32 and not value.startswith(("#", "|", "![", "```", "- ", ">")):
            value = value.replace("**", "").replace("`", "").lstrip("▸ ")
            if len(value) <= 85:
                return value
            sentence_end = re.search(r"[。；!?！？]", value[28:85])
            if sentence_end:
                return value[:28 + sentence_end.end()]
            return value[:82].rstrip("，、；;:： .") + "…"
    return title


def paragraph_markdown(paragraph: Paragraph, document: Document, stem: str, image_count: list[int]) -> list[str]:
    lines = []
    content = paragraph.text.strip().replace("源文件", "输入文件")
    if paragraph.style.name == "Heading 2":
        if content:
            lines.append("## " + content)
    elif paragraph.style.name.startswith("Heading"):
        if content:
            lines.append("### " + content)
    elif paragraph.style.name == "HTML Preformatted":
        if content:
            lines.append("```text\n" + content.replace("```", "` ` `") + "\n```")
    elif content and len(content) <= 45 and re.match(r"^(?:\d+[.、）)]|场景\d+[:：])\s*\S", content) and not re.match(r"^\d+\.[A-Za-z0-9]{1,5}(?:\s|$)", content):
        lines.append("### " + content)
    elif content:
        # Word's shell comments are examples, not article-level headings.
        # Escape only the Markdown marker; keep the complete paragraph text.
        content = re.sub(r"(?m)^# (?=[^#])", r"\# ", content)
        lines.append(content.replace("\n", "  \n"))

    for blip in paragraph._p.xpath(".//a:blip"):
        rel = blip.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed")
        if not rel or rel not in document.part.related_parts:
            continue
        part = document.part.related_parts[rel]
        image_count[0] += 1
        suffix = Path(str(part.partname)).suffix or mimetypes.guess_extension(part.content_type) or ".bin"
        filename = f"{stem}-{image_count[0]:03d}{suffix}"
        (MEDIA / filename).write_bytes(part.blob)
        lines.append(f"![示意图 {image_count[0]}](/doc-media/{filename})")
    return lines


def table_markdown(table: Table) -> str:
    rows = []
    for row in table.rows:
        cells = []
        for cell in row.cells:
            value = cell.text.strip().replace("源文件", "输入文件").replace("|", "\\|").replace("\n", "<br>")
            cells.append(value or " ")
        rows.append(cells)
    if not rows:
        return ""
    width = max(map(len, rows))
    rows = [row + [" "] * (width - len(row)) for row in rows]
    return "\n".join(["| " + " | ".join(rows[0]) + " |", "| " + " | ".join(["---"] * width) + " |"] + ["| " + " | ".join(row) + " |" for row in rows[1:]])


def format_semantic_parts(parts: list[str]) -> list[str]:
    """Expose the note's own labels and ordered procedures without shortening it."""
    ordered = {"核心解法", "操作步骤", "解题步骤", "提取步骤", "验证步骤", "处理步骤", "操作流程"}
    bulleted = {"典型特征", "识别特征", "常见特征", "常见表现", "注意事项"}
    out = []
    mode = None
    group = []

    def flush():
        nonlocal mode, group
        if group:
            marker = "- " if mode == "bulleted" else None
            out.append("\n".join((marker or f"{i}. ") + value for i, value in enumerate(group, 1)))
        mode = None
        group = []

    for part in parts:
        value = part.strip()
        if not value:
            continue
        if value.startswith(("#", "|", "![", "```")):
            flush()
            out.append(value)
            continue
        label_only = re.fullmatch(r"([\u4e00-\u9fffA-Za-z0-9/]{2,12})[：:]", value)
        if label_only:
            flush()
            label = label_only.group(1)
            if label in ordered or label in bulleted:
                out.append("#### " + value)
                mode = "ordered" if label in ordered else "bulleted"
            else:
                out.append("**" + value + "**")
            continue
        inline_label = re.match(r"^([\u4e00-\u9fffA-Za-z0-9/]{2,12}[：:])(\S.*)$", value)
        if inline_label:
            flush()
            out.append("**" + inline_label.group(1) + "** " + inline_label.group(2))
            continue
        if mode:
            group.append(value)
        else:
            out.append(value)
    flush()
    return out


def sections_from_document(path: Path, prefix: str, is_tool: bool):
    document = Document(path)
    sections = []
    current = None
    image_count = [0]
    MEDIA.mkdir(parents=True, exist_ok=True)
    for block in document.iter_inner_content():
        if isinstance(block, Paragraph) and block.style.name == "Heading 1":
            if current:
                current["parts"] = format_semantic_parts(current["parts"])
                sections.append(current)
            number = len(sections) + 1
            title = clean_title(block.text, is_tool)
            current = {"id": f"{prefix}-{number:02d}", "title": title, "topic": topic_for(title, is_tool), "parts": [], "originalTitle": block.text.strip()}
            continue
        if current is None:
            continue
        stem = current["id"]
        if isinstance(block, Paragraph):
            current["parts"].extend(paragraph_markdown(block, document, stem, image_count))
        elif isinstance(block, Table):
            current["parts"].append(table_markdown(block))
    if current:
        current["parts"] = format_semantic_parts(current["parts"])
        sections.append(current)
    return sections


def tool_inventory():
    modules = {
        "Web": "Web", "reverse": "Reverse", "crypto": "Crypto", "Forensics": "Forensics",
        "流量分析": "Misc", "数据库": "Forensics", "hex_editor": "Misc",
    }
    ignored_dirs = {"config", "plugins", "logs", "resources", "runs", "scripts", "knowledge", "docs", "tests", "tools", "apps", "packages", "bin", "license", ".codex", ".hermes", ".git", "Byxs20-Data"}
    ignored_files = {"uninstall.exe", "INFO.exe"}
    items = []
    for parent in sorted(TOOL_ROOT.iterdir(), key=lambda p: p.name.lower()):
        if not parent.is_dir():
            continue
        module = modules.get(parent.name, "Misc")
        if parent.name in {"CTFAIO", "CTF-Script-Assistant", "PuzzleSolver_Pro"}:
            items.append({"name": parent.name, "module": "Misc", "path": str(parent), "kind": "工具套件", "group": parent.name})
            continue
        for child in sorted(parent.iterdir(), key=lambda p: p.name.lower()):
            item_module = "Forensics" if child.name.lower().startswith("mimikatz") else module
            if child.is_dir() and child.name.lower() not in {x.lower() for x in ignored_dirs}:
                items.append({"name": child.name, "module": item_module, "path": str(child), "kind": "程序目录", "group": parent.name})
            elif child.is_file() and child.suffix.lower() in {".exe", ".jar", ".bat", ".py", ".lnk"} and child.name not in ignored_files:
                items.append({"name": child.stem, "module": item_module, "path": str(child), "kind": "快捷方式" if child.suffix.lower() == ".lnk" else "程序文件", "group": parent.name})
    for item in items:
        item["id"] = "tool-" + hashlib.sha1(item["path"].encode("utf-8")).hexdigest()[:12]
    return items


def normalized(value: str) -> str:
    value = re.sub(r"^\d+[.、]", "", value.lower())
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", value)


ALIASES = {
    "convert": "imagemagick", "zbarimg": "zbar", "stegsolve": "stegsolve",
    "mp3stego": "mp3stego", "john the ripper": "john", "7z": "7zip", "stegcracker": "stegcracker",
    "jpegSnoop": "jpegsnoop", "apngdis": "apng", "pdfstreamdumper": "pdfstreamdumper",
    "stegsnow": "snow", "basecrack": "basecrack", "msoffcrypto-tool": "msoffcrypto",
    "tianTongEye": "tiantongeye",
}


def find_installations(title: str, inventory: list[dict]) -> list[dict]:
    key = normalized(title)
    alias = normalized(ALIASES.get(title.lower(), title))
    matches = []
    for item in inventory:
        name = normalized(item["name"])
        # Require a distinctive token; short CLI names otherwise collide accidentally.
        if len(key) >= 4 and (name.startswith(key) or (len(name) >= 5 and key.startswith(name))) or len(alias) >= 4 and name.startswith(alias):
            matches.append(item)
    return matches


def frontmatter(data: dict) -> str:
    values = ["---"]
    for key, value in data.items():
        values.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
    values.append("---")
    return "\n".join(values)


def curate_misc_note(section_id: str, body: str) -> str:
    """Preserve the imported examples and add hand-maintained practical guidance."""
    guide = CURATION / f"{section_id}.md"
    if not guide.is_file():
        return body
    supplement = guide.read_text(encoding="utf-8").strip()
    if section_id == "misc-note-54":
        for old, corrected in MISC_NOTE_54_CORRECTIONS.items():
            body = body.replace(old, corrected)
        body = body.replace(
            "tshark -r capture.pcap -T fields -e ip.ttl",
            "```bash\ntshark -r capture.pcap -T fields -e ip.ttl\n```",
        )
        number = count(3)
        body = re.sub(
            r"(?m)^## [一二三四五六七八九十]+[、.]\s*(.+)$",
            lambda match: f"## {next(number)}. {match.group(1)}",
            body,
        )
        body = re.sub(r"(?m)^### (\d+)\.(\S)", r"### \1. \2", body)
    if section_id == "misc-note-71":
        number = count(1)
        body = re.sub(
            r"(?m)^## (.+)$",
            lambda match: f"### {next(number)}. {match.group(1)}",
            body,
        )
        body = "## 3. 格式图例\n\n" + body
    return supplement + "\n\n" + body


def write_manual_pages():
    NOTES.mkdir(parents=True, exist_ok=True)
    TOOLS.mkdir(parents=True, exist_ok=True)
    for pattern in ("misc-note-*.md", "docker-case-*.md", "docker-evidence-*.md", "fic-case-*.md", "forensic-method-*.md", "git-docker-*.md"):
        for file in NOTES.glob(pattern):
            file.unlink()
    for file in TOOLS.glob("misc-tool-*.md"):
        file.unlink()
    inventory = tool_inventory()
    (DATA / "tool-inventory.json").write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    source_ids = {item["name"]: item["id"] for item in json.loads((DATA / "inventory.json").read_text(encoding="utf-8")) if item["kind"] == "source"}

    notes = sections_from_document(ROOT / "Misc知识总结.docx", "misc-note", False)
    for section in notes:
        body = curate_misc_note(section["id"], "\n\n".join(section["parts"]).strip())
        summary = summary_for(section["parts"], section["title"])
        if section["id"] == "misc-note-71":
            summary = "按定位图形与模块形态区分常见矩阵码，并验证解码结果。"
        elif section["id"] == "misc-note-54":
            summary = "按同源会话提取 TTL 序列，校正跳数并验证编码方式。"
        fm = frontmatter({"title": section["title"], "summary": summary, "module": "Misc", "topic": section["topic"], "tags": [], "status": "已整理", "sourceIds": [source_ids["Misc知识总结.docx"]], "challengeIds": [], "relatedIds": [], "updated": "2026-09-30" if section["id"] in {"misc-note-54", "misc-note-71"} else "2026-09-29"})
        text = fm + "\n\n" + body + "\n"
        (NOTES / f"{section['id']}.md").write_text(text, encoding="utf-8")

    tools = sections_from_document(ROOT / "Misc工具1.docx", "misc-tool", True)
    for section in tools:
        matches = find_installations(section["title"], inventory)
        body = "\n\n".join(section["parts"]).strip()
        summary = summary_for(section["parts"], section["title"])
        fm = frontmatter({"title": section["title"], "summary": summary, "module": "Misc", "topic": section["topic"], "locationPaths": [m["path"] for m in matches], "sourceIds": [source_ids["Misc工具1.docx"]], "updated": "2026-09-29"})
        (TOOLS / f"{section['id']}.md").write_text(fm + "\n\n" + body + "\n", encoding="utf-8")
    extra = write_forensics_pages(source_ids)
    print(f"Generated {len(notes)} Misc knowledge sections, {extra} Forensics sections, {len(tools)} tool guides, {len(inventory)} local tool entries")


def markdown_sections(path: Path):
    """Split at level-two headings while leaving each section's body unchanged."""
    content = path.read_text(encoding="utf-8")
    preamble = []
    sections = []
    current = None
    fenced = False
    for line in content.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
        if not fenced and line.startswith("## "):
            if current:
                sections.append(current)
            current = {"title": re.sub(r"^\d+\.\s*", "", line[3:].strip()), "body": []}
        elif current:
            current["body"].append(line)
        else:
            preamble.append(line)
    if current:
        sections.append(current)
    if sections and preamble:
        # Introductory notes belong with the first topic rather than a separate raw page.
        sections[0]["body"] = preamble + [""] + sections[0]["body"]
    return sections


def forensics_classification(identifier: str) -> tuple[str, str]:
    if identifier.startswith("docker-case-"):
        return "服务器取证", "Docker 与容器"
    if identifier.startswith("git-docker-"):
        number = int(identifier[-2:])
        return ("服务器取证", "版本与源码") if 3 <= number <= 8 else ("服务器取证", "Docker 与容器")
    number = int(identifier[-2:])
    assignments = {
        1: ("综合取证", "证据保全与流程"), 2: ("计算机取证", "镜像与文件系统"),
        3: ("服务器取证", "主机与服务"), 4: ("服务器取证", "Web 与数据库"),
        5: ("服务器取证", "Web 与数据库"), 6: ("手机取证", "Android"),
        7: ("计算机取证", "程序与恶意代码"), 8: ("综合取证", "密码与资金"),
        9: ("文件与多媒体取证", "文件恢复与格式"), 10: ("网络取证", "连接与隧道"),
        11: ("综合取证", "时间线与关联"), 12: ("综合取证", "密码与资金"),
        13: ("综合取证", "工具与路径"), 14: ("综合取证", "工具与路径"),
        15: ("综合取证", "证据保全与流程"), 16: ("综合取证", "证据保全与流程"),
        17: ("综合取证", "时间线与关联"), 18: ("综合取证", "时间线与关联"),
        19: ("综合取证", "时间线与关联"),
    }
    return assignments[number]


def forensics_title(identifier: str, title: str) -> str:
    aliases = {
        "fic-case-03": "Linux 系统与服务识别",
        "fic-case-06": "Android 应用与 APK 逆向取证",
        "fic-case-07": "程序样本与恶意代码取证：PE、Go、SO 与加密容器",
        "fic-case-17": "题型与知识点索引",
        "fic-case-18": "按考点检索题组",
        "fic-case-19": "跨检材证据路径与关联",
        "git-docker-02": "Git 与容器快速索引",
        "docker-case-09": "Docker 镜像结构与取证",
        "git-docker-10": "Docker 镜像分析命令",
        "docker-case-11": "Docker 网络证据定位",
        "git-docker-16": "Docker 网络分析命令",
        "docker-case-16": "Docker 参考规范",
        "fic-case-14": "跨平台系统目录与关键文件",
    }
    if identifier in aliases:
        return aliases[identifier]
    if identifier.startswith("fic-case-"):
        return re.sub(r"^模块[一二三四五六七八九十]+：", "", title)
    if identifier.startswith("git-docker-"):
        return re.sub(r"^\d+\s+", "", title)
    return title


def forensics_summary(identifier: str, title: str) -> str:
    summaries = {
        "fic-case-01": "以固定、解析、定位、还原和交叉印证五步建立可复核的取证流程。",
        "fic-case-02": "识别检材形态、分区与文件系统，并处理 Btrfs、LVM、ZFS 和嵌套镜像。",
        "fic-case-03": "核对 Linux 系统身份与文件系统，区分服务安装和运行痕迹，关联账户活动与启动配置。",
        "fic-case-04": "关联 Web 配置、程序目录、访问日志与版本记录，重建应用侧活动。",
        "fic-case-05": "定位数据库文件，读取原始页与关键字段，并核对统计结果。",
        "fic-case-06": "梳理 Android 目录、应用数据库、APK 与通信定位证据。",
        "fic-case-07": "识别程序格式与校验逻辑，分析执行、清理和逆向线索。",
        "fic-case-08": "辨认加密算法、密钥材料与哈希用途，复现受保护数据的解析过程。",
        "fic-case-09": "从媒体容器、文档结构、熵值与二维码中识别隐藏和损坏线索。",
        "fic-case-10": "结合代理、VPN、隧道和主机解析还原通信路径；容器网络详见服务器取证。",
        "fic-case-11": "统一时间基准，交叉比对系统、应用与文件痕迹以重建行为顺序。",
        "fic-case-12": "识别钱包、地址与交易记录，并核对资金流水的范围和口径。",
        "fic-case-13": "按取证任务检索常用命令、参数、工具用途与脚本处理方法。",
        "fic-case-14": "按 Linux、Windows、Android 和应用层检索目录、日志及证据落点。",
        "fic-case-15": "汇总路径、时间、格式和证据关联中的高频误判，明确判定边界。",
        "fic-case-16": "将常用判定原则压缩为可在现场快速核对的检查要点。",
        "fic-case-17": "用题型与知识点的对应关系快速定位相关分析方法。",
        "fic-case-18": "按考点组合关联题组，便于对照验证同类取证思路。",
        "fic-case-19": "串联计算机、手机、服务器、互联网与程序检材的命中路径。",
        "docker-case-01": "明确只读保全、时间记录和容器取证的操作边界。",
        "docker-case-02": "理解 Docker 客户端、守护进程、镜像、容器与存储的关系。",
        "docker-case-03": "按环境、服务、容器、镜像和持久化数据建立服务器取证顺序。",
        "docker-case-04": "结合包管理器、可执行文件和数据目录判断 Docker 的安装方式。",
        "docker-case-05": "从 systemd 单元、覆盖配置和日志确认 Docker 服务的实际启动方式。",
        "docker-case-06": "核对 daemon 配置、数据根目录、日志驱动和运行时参数。",
        "docker-case-07": "调查容器清单、配置、进程、挂载与文件变化。",
        "docker-case-08": "区分容器标准输出、应用日志与日志驱动记录，定位真实事件。",
        "docker-case-09": "从镜像元数据、层与构建历史还原容器运行基础。",
        "docker-case-10": "定位 Docker 数据根目录、可写层、Volume 与底层存储证据。",
        "docker-case-11": "通过网络配置、端口映射和连接关系核对容器通信。",
        "docker-case-12": "在 Kubernetes 节点区分 Docker、containerd 与 CRI 的证据落点。",
        "docker-case-13": "按取证问题快速对应服务、容器、日志、镜像和存储位置。",
        "docker-case-14": "用于现场首轮保全和排查的顺序化检查清单。",
        "docker-case-15": "以配置、日志、层、挂载和网络之间的关系归纳容器证据链。",
        "docker-case-16": "集中定位 Docker 与容器运行时的官方规范和参考资料。",
        "git-docker-02": "在分析前建立 Git 与容器的只读检查顺序和入口。",
        "git-docker-03": "识别仓库、工作树、裸仓库和 Git 元数据的实际位置。",
        "git-docker-04": "沿提交图核对作者、时间、变更文件与历史版本。",
        "git-docker-05": "从提交、引用和 reflog 恢复历史文件并验证内容。",
        "git-docker-06": "解析 Git 对象、悬空提交和残留数据，寻找未引用线索。",
        "git-docker-07": "区分分支、标签与 stash 的证据含义及修改风险。",
        "git-docker-08": "按仓库识别、历史检查和对象恢复完成源码取证。",
        "git-docker-09": "厘清 Dockerfile、镜像、容器与数据卷的生命周期。",
        "git-docker-10": "使用只读命令检查镜像层、摘要、历史和元数据。",
        "git-docker-11": "核对容器状态、端口、挂载和启动参数。",
        "git-docker-12": "定位容器内部文件、进程与配置，并记录进入容器的操作影响。",
        "git-docker-13": "关联容器日志、元数据与应用自有日志，重建事件时间线。",
        "git-docker-14": "从容器与镜像提取文件，并保留来源、路径与哈希。",
        "git-docker-15": "识别 Volume、Bind Mount 与容器可写层中的持久化数据。",
        "git-docker-16": "核对网络、别名、端口映射与容器间连接。",
        "git-docker-17": "检查环境变量和配置中的凭据线索，控制查看与记录范围。",
        "git-docker-18": "分析 Dockerfile、构建上下文与镜像历史中的线索。",
        "git-docker-19": "解析 Compose 服务、网络、环境变量和数据卷配置。",
        "git-docker-20": "区分镜像保存、容器导出及导入后的证据差异。",
        "git-docker-21": "识别清理命令对镜像、容器和数据卷造成的证据损失。",
        "git-docker-22": "按状态、配置、日志、进程和提取结果完成服务器取证。",
        "git-docker-23": "对照 Git 与 Docker 中名称相近但作用不同的命令。",
        "git-docker-24": "将仓库和容器的关键检查项组织成现场速查顺序。",
    }
    return summaries.get(identifier, f"围绕{title}梳理证据位置、分析步骤与判断边界。")


DOCKER_GROUPS = [
    {
        "id": "docker-evidence-01",
        "title": "Docker 取证 01｜环境、服务与配置",
        "summary": "确认运行时、安装方式、守护进程、配置和数据根目录，建立容器取证的基础边界。",
        "intro": "先识别实际运行时，再记录宿主机时间、Docker 版本、服务启动参数和数据根目录。镜像、容器、可写层和卷属于不同证据面；不能只凭默认路径或一条命令定位全部内容。",
        "ids": ["docker-case-01", "docker-case-02", "docker-case-04", "docker-case-05", "docker-case-06", "docker-case-16", "git-docker-02", "git-docker-09"],
    },
    {
        "id": "docker-evidence-02",
        "title": "Docker 取证 02｜现场流程与操作边界",
        "summary": "按保全、枚举、定位、提取、复核的顺序分析容器，并避开会改变证据的操作。",
        "intro": "**首轮顺序：** 固定主机时间和检材 → 辨认 Docker/containerd/CRI → 枚举全部容器与镜像 → 保存 inspect 配置 → 确认日志驱动、挂载和网络 → 在副本上提取。常用的 `docker ps -a --no-trunc`、`docker info`、`docker inspect <容器ID>` 只说明采集时可见状态；已删除对象还需磁盘和事件记录补充。进入容器、导出、停止或清理前，应评估对运行态和证据的影响。",
        "ids": ["docker-case-03", "docker-case-13", "docker-case-14", "docker-case-15", "git-docker-21", "git-docker-22", "git-docker-23", "git-docker-24"],
        "archive": ["docker-first-pass"],
    },
    {
        "id": "docker-evidence-03",
        "title": "Docker 取证 03｜容器与镜像",
        "summary": "区分容器运行态、可写层与镜像构建层，核对进程、文件变化和镜像来源。",
        "intro": "先保存完整容器 ID、镜像摘要、创建/启动时间及原始 inspect JSON，再分别分析容器可写层与镜像历史。`docker diff` 只描述可写层变化，挂载卷中的内容要回到卷或宿主机路径。",
        "ids": ["docker-case-07", "docker-case-09", "git-docker-10", "git-docker-11", "git-docker-12", "git-docker-18", "git-docker-20"],
    },
    {
        "id": "docker-evidence-04",
        "title": "Docker 取证 04｜日志、文件与持久化",
        "summary": "从日志驱动和 LogPath 找到真实日志，再核对应用文件、卷与宿主机持久化数据。",
        "tags": ["日志"],
        "intro": "先用 `docker inspect --format '{{.HostConfig.LogConfig.Type}} {{.LogPath}}' <容器ID>` 核对当前容器的日志驱动与路径。`json-file` 的常见位置不能代替实际配置；LogPath 为空时继续查 journald、其他驱动或编排平台。容器标准输出、应用自有日志和宿主机日志分开保全，再按时间及容器 ID 关联。",
        "ids": ["docker-case-08", "docker-case-10", "git-docker-13", "git-docker-14", "git-docker-15", "git-docker-17"],
        "archive": ["docker-logpath"],
    },
    {
        "id": "docker-evidence-05",
        "title": "Docker 取证 05｜网络与 Compose",
        "summary": "核对 Docker 网络、端口发布与 Compose 定义，关联服务名、IP、宿主机转发和通信记录。",
        "tags": ["流量"],
        "intro": "从 Docker 网络配置、端口发布、DNS 与宿主机连接记录建立通信关系。Kubernetes 资源、节点与存储分析统一见 [Kubernetes 集群取证](/knowledge/forensic-kubernetes-cluster/)。",
        "ids": ["docker-case-11", "docker-case-12", "git-docker-16", "git-docker-19"],
    },
]

METHOD_GROUPS = [
    {
        "id": "forensic-method-pitfalls",
        "title": "判定原则与易错点",
        "summary": "把高频误判和现场判定原则放在一起，按证据边界逐项核对。",
        "topic": "证据保全与流程",
        "ids": ["fic-case-15", "fic-case-16"],
    },
    {
        "id": "forensic-method-index",
        "title": "取证任务与证据路径索引",
        "summary": "按分析目标、证据对象和系统路径定位操作步骤、结果判读与交叉验证方法。",
        "topic": "时间线与关联",
        "ids": ["fic-case-17", "fic-case-18", "fic-case-19"],
    },
]


def _body_and_meta(path: Path) -> tuple[str, dict]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n\s*", text, re.DOTALL)
    if not match:
        raise ValueError(f"Missing frontmatter: {path}")
    metadata = {}
    for key in ("title", "sourceIds", "module"):
        value = re.search(rf"(?m)^{key}: (.+)$", match.group(1))
        if value:
            raw = value.group(1).strip()
            try:
                metadata[key] = json.loads(raw)
            except json.JSONDecodeError:
                # Handwritten YAML may use an unquoted title or bare list items.
                metadata[key] = [item.strip().strip("\"'") for item in raw[1:-1].split(",") if item.strip()] if key == "sourceIds" else raw.strip("\"'")
    return text[match.end():].strip(), metadata


def _nested_headings(body: str, outer_number: int) -> str:
    original = body.splitlines()
    levels, fenced = [], False
    for line in original:
        if line.lstrip().startswith("```"):
            fenced = not fenced
        if not fenced:
            heading = re.match(r"^(#{1,5}) (.*)$", line)
            if heading:
                levels.append(len(heading.group(1)))
    first_level = min(levels, default=2)
    lines, fenced = [], False
    counters = [0] * 7
    for line in original:
        if line.lstrip().startswith("```"):
            fenced = not fenced
        if not fenced:
            heading = re.match(r"^(#{1,5}) (.*)$", line)
            if heading:
                level = min(6, len(heading.group(1)) - first_level + 3)
                counters[level] += 1
                for deeper in range(level + 1, 7):
                    counters[deeper] = 0
                title = re.sub(r"^(?:(?:\d+(?:\.\d+)+(?:[.、．])?|[A-Za-z]\.\d+(?:\.\d+)*(?:[.、．])?|\d+[.、．])\s*)+", "", heading.group(2))
                sequence = [outer_number, *(counters[part] for part in range(3, level + 1))]
                line = "#" * level + " " + ".".join(f"{number:02d}" for number in sequence) + " " + title
        lines.append(line)
    return "\n".join(lines).strip()


def normalize_forensic_markdown(body: str, *, article_id: str | None = None) -> str:
    """Keep command placeholders visible and repair Word's typographic CLI options."""
    body = body.replace("‘", "'").replace("’", "'")
    body = body.replace("本卷", "该题组").replace("本附录", "本索引")
    body = body.replace(
        "我实测 GBK/UTF-8/UTF-16 直查中文**均 0 命中**，改查拼音才命中。",
        "题例记录显示，按 GBK/UTF-8/UTF-16 直查中文**均未命中**，改查拼音才命中；复核时应同时确认数据库编码、字段值与查询条件。",
    )
    body = re.sub(
        r"(?<![\w])[–—]([A-Za-z][A-Za-z-]*)",
        lambda match: ("-" if len(match.group(1)) == 1 else "--") + match.group(1),
        body,
    )
    lines, fenced = [], False
    allowed_html = re.compile(r"^/?(?:pre|code|br)(?:\s|/|$)", re.IGNORECASE)
    # Bare disclosures are limited to the memory catalog, the reconstruction
    # template, and the server articles explicitly being given the same
    # two-layer reading structure. Attributes and other HTML stay escaped.
    catalog_html = re.compile(r"^/?(?:details|summary)$", re.IGNORECASE)
    disclosure_ids = {
        "forensic-memory-volatility",
        "forensic-website-reconstruction",
        "forensic-server-panel",
        "forensic-server-services",
        "fic-case-03",
        "forensic-guide-server",
        "fic-case-04",
        "fic-case-05",
        "forensic-database-recovery",
        "docker-evidence-01",
        "docker-evidence-02",
        "docker-evidence-03",
        "docker-evidence-04",
        "docker-evidence-05",
        "git-docker-03",
        "git-docker-04",
        "git-docker-05",
        "git-docker-06",
        "git-docker-07",
        "git-docker-08",
        "forensic-kubernetes-cluster",
        "forensic-cloud-vm",
        "forensic-method-index",
    }
    def preserve_html(tag: str) -> bool:
        return bool(allowed_html.match(tag) or
                    (article_id in disclosure_ids and catalog_html.fullmatch(tag)))
    # Exact full-line anchors only. A new article must be added here by id.
    legacy_anchors = {
        "forensic-website-reconstruction": {
            '<span id="01-先固定证据再恢复可解释的业务"></span>',
            '<span id="02-网站重构三要素三条匹配链"></span>',
            '<span id="03-数据盘与-www先证明映射再挂载副本"></span>',
            '<span id="04-按部署关系启动最小-web-环境"></span>',
            '<span id="05-数据库容器和访问地址一起匹配"></span>',
            '<span id="06-找到后台后区分身份恢复与离线依赖障碍"></span>',
            '<span id="07-三条匿名实战路线"></span>',
            '<span id="08-用业务-sql-验收并把每处变化带回结论"></span>',
            '<span id="065-四种常见改动的影响恢复观察与分支改变分开"></span>',
            '<span id="044-apachehttpd-与-apachectl-的实例核对与恢复"></span>',
            '<span id="061-php后台入口从url映射到认证代码"></span>',
            '<span id="062-旧式摘要复算函数名实际参数和字节链"></span>',
            '<span id="065-php网站后台密码绕过四种方法与副本复现"></span>',
            '<span id="071-宝塔数据盘从-www-映射恢复-php-业务"></span>',
            '<span id="072-面板列表为空从备份与操作记录找回-php-站点"></span>',
            '<span id="073-java-站库分离恢复入口应用与依赖网络"></span>',
            '<span id="方法三把member登录与成功分支提前并明确绑定uid"></span>',
            '<span id="方法二在密码错误分支输出预选口令摘要再接方法一"></span>',
        },
        "forensic-server-panel": {
            '<span id="01-先识别面板与实际服务"></span>',
            '<span id="02-宝塔常见数据落点"></span>',
            '<span id="03-加密字段的定位与验证"></span>',
            '<span id="04-网站数据库与上传行为"></span>',
            '<span id="05-网站重构的独立入口"></span>',
            '<span id="06-工具与结果表"></span>',
            '<span id="07-实战串联站点配置上传记录与落地文件"></span>',
            '<span id="08-面板-cli-功能识别与状态保全"></span>',
            '<span id="09-实战面板列表为空时追查网站与备份痕迹"></span>',
        },
        "forensic-server-services": {
            '<span id="01-从现状建立服务清单"></span>',
            '<span id="02-逐层定位配置和日志"></span>',
            '<span id="03-处理异常与输出"></span>',
            '<span id="04-活机首轮定位示例"></span>',
            '<span id="05-将服务异常接到登录与请求"></span>',
            '<span id="06-离线-linux-的发行版账户与定时任务"></span>',
            '<span id="07-登录sudo-与-systemd-journal"></span>',
            '<span id="08-实战验证一项可疑定时任务"></span>',
            '<span id="09-实战核对密码修改软件安装和服务代理配置"></span>',
            '<span id="10-实战独立读取-laravel-网站与机器人配置"></span>',
            '<span id="11-实战从定制密码校验中复算派生参数"></span>',
            '<span id="12-实战按业务状态软删与日期口径统计记录"></span>',
            '<span id="13-实战从-vsftpd-名单到认证与传输证据"></span>',
            '<span id="15-从目录挂载与历史命令复核任务路径"></span>',
        },
        "fic-case-03": {
            '<span id="01-分析目标与操作顺序"></span>',
            '<span id="02-系统身份与文件系统对应"></span>',
            '<span id="03-服务清单与状态判定"></span>',
            '<span id="04-账户活动与启动链路"></span>',
            '<span id="05-仿真观察与结果复核"></span>',
            '<span id="06-分析结果整理"></span>',
        },
        "forensic-guide-server": {
            '<span id="01-先画出服务链路"></span>',
            '<span id="02-有活机时建立最小现状清单"></span>',
            '<span id="03-从登录与请求追到数据变动"></span>',
            '<span id="04-容器场景转入专门的证据链"></span>',
            '<span id="05-云与虚拟化再补控制面"></span>',
            '<span id="06-输出结论与缺口"></span>',
            '<span id="07-不同服务架构如何归入同一条主线"></span>',
            '<span id="08-实战从一个-web-请求追到数据库变化"></span>',
        },
        "fic-case-04": {
            '<span id="01-从-web-配置建立应用范围"></span>',
            '<span id="02-cms-配置与业务属性"></span>',
            '<span id="03-文件改名删除与版本控制"></span>',
            '<span id="04-访问日志与活动时间线"></span>',
            '<span id="05-应用暴露面与结果整理"></span>',
            '<span id="06-实战java-服务配置代码位置与依赖证据"></span>',
        },
        "fic-case-05": {
            '<span id="01-先定位实例再查询数据"></span>',
            '<span id="02-sqlcipher-的识别与密钥验证"></span>',
            '<span id="03-表结构字段语义和检索条件"></span>',
            '<span id="04-服务不可用时读取原始页"></span>',
            '<span id="05-聚合统计与多表关联"></span>',
            '<span id="06-枚举所有端点与核对部署状态"></span>',
        },
        "forensic-database-recovery": {
            '<span id="01-先辨认拿到的材料"></span>',
            '<span id="02-frm-与-ibd-的旧版恢复路径"></span>',
            '<span id="03-压缩物理备份与增量链"></span>',
            '<span id="04-从恢复成功到可信记录"></span>',
            '<span id="05-实战恢复一张旧版-innodb-表并验证记录"></span>',
            '<span id="06-删除记录分析先分清软删硬删和日志覆盖"></span>',
            '<span id="07-实战阅读-row-binlog-中一笔删除前的订单"></span>',
            '<span id="08-阅读结果与实验恢复分开交付"></span>',
            '<span id="09-实战区分-ssh-隧道和数据库连接目标"></span>',
            '<span id="10-逻辑导入先检查版本编码与写入对象"></span>',
            '<span id="11-离线授权副本恢复访问区分产品与版本"></span>',
            '<span id="12-mysql-实战命令先选任务再选命令"></span>',
            '<span id="13-数据目录配置版本与日志位置"></span>',
            '<span id="14-mysql-客户端连接参数与交互操作"></span>',
            '<span id="15-实例账户变量状态与只读会话"></span>',
            '<span id="16-库表ddl字段索引与未知对象定位"></span>',
            '<span id="17-select实战条件排序去重与异常记录"></span>',
            '<span id="18-聚合排名与多表资金统计"></span>',
            '<span id="19-时间ip字符串二进制与json字段"></span>',
            '<span id="20-mysql-8窗口排名最新一条与会员层级"></span>',
            '<span id="21-逻辑备份导入结果文件与重导入核验"></span>',
            '<span id="22-物理目录表空间与损坏副本的操作入口"></span>',
            '<span id="23-binlog其他日志与时间点回放命令"></span>',
            '<span id="24-实战组合与自建sql练习"></span>',
            '<span id="25-排错易错命令与最终证据清单"></span>',
        },
        "docker-evidence-01": {
            '<span id="01-使用原则与取证边界"></span>',
            '<span id="02-docker-整体架构"></span>',
            '<span id="03-docker-安装信息定位"></span>',
            '<span id="04-docker-服务systemd分析"></span>',
            '<span id="05-docker-配置文件分析"></span>',
            '<span id="06-docker-参考规范"></span>',
            '<span id="07-从问题定位到证据对象"></span>',
            '<span id="08-docker-基础概念与环境识别"></span>',
            '<span id="09-docker-与-lxc-的独立识别流程"></span>',
            '<span id="10-安装服务与数据根的离线复核"></span>',
        },
        "docker-evidence-02": {
            '<span id="01-docker-服务器取证首轮定位"></span>',
            '<span id="02-docker-服务器取证整体流程"></span>',
            '<span id="03-服务器取证快速定位表"></span>',
            '<span id="04-现场检查清单"></span>',
            '<span id="05-docker-取证核心思想总结"></span>',
            '<span id="06-docker-清理与风险命令"></span>',
            '<span id="07-docker-服务器取证完整流程"></span>',
            '<span id="08-git-docker-易混命令对比"></span>',
            '<span id="09-现场命令与记录速查"></span>',
            '<span id="10-docker-与-lxc-的命令归属核对"></span>',
            '<span id="11-实战将首轮输出变成可复核清单"></span>',
        },
        "docker-evidence-03": {
            '<span id="01-docker-容器分析"></span>',
            '<span id="02-docker-镜像结构与取证"></span>',
            '<span id="03-docker-镜像分析命令"></span>',
            '<span id="04-docker-容器管理"></span>',
            '<span id="05-docker-容器内部分析"></span>',
            '<span id="06-dockerfile-与镜像构建"></span>',
            '<span id="07-docker-镜像与容器导入导出"></span>',
            '<span id="08-实战分别保全容器状态可写层与镜像历史"></span>',
            '<span id="09-实战把数据库容器配置对应到业务数据"></span>',
        },
        "docker-evidence-04": {
            '<span id="01-查找容器真实日志路径"></span>',
            '<span id="02-docker-日志分析"></span>',
            '<span id="03-docker-存储目录取证"></span>',
            '<span id="04-docker-日志与元数据取证"></span>',
            '<span id="05-docker-文件提取"></span>',
            '<span id="06-docker-volume-与数据持久化"></span>',
            '<span id="07-docker-环境变量与敏感信息排查"></span>',
            '<span id="08-实战将一次可疑请求对应到日志文件和卷"></span>',
        },
        "docker-evidence-05": {
            '<span id="01-docker-网络证据定位"></span>',
            '<span id="02-docker-网络分析命令"></span>',
            '<span id="03-docker-compose"></span>',
            '<span id="04-容器网桥与通信归属"></span>',
            '<span id="05-实战核对-docker-服务名ip-与发布端口"></span>',
            '<span id="06-实战用-lxc-定义与租约限定-ip-归属"></span>',
        },
        "forensic-kubernetes-cluster": {
            '<span id="01-阅读路线与取证主线"></span>',
            '<span id="02-架构控制平面节点与运行时"></span>',
            '<span id="03-工作负载层级与-pod-生命周期"></span>',
            '<span id="04-api-对象命名空间与-yaml"></span>',
            '<span id="05-网络podserviceingress-与-dns"></span>',
            '<span id="06-存储卷pvcpvstorageclass-与-nfs"></span>',
            '<span id="07-配置身份与权限"></span>',
            '<span id="08-kubectl-使用与状态采集"></span>',
            '<span id="09-节点证据apicri-与磁盘的关联"></span>',
            '<span id="10-实战一从业务容器追到-nfs-数据目录"></span>',
            '<span id="11-实战二恢复多节点应用并解释每个故障"></span>',
            '<span id="12-历史容器身份把当前-id-与镜像中的旧记录分开"></span>',
            '<span id="13-实战三把集群关系接到业务证据与时间线"></span>',
            '<span id="14-高频误区与交付清单"></span>',
        },
        "forensic-cloud-vm": {
            '<span id="01-先画资源边界"></span>',
            '<span id="02-分开看控制面与数据面"></span>',
            '<span id="03-分析顺序"></span>',
            '<span id="04-虚拟机常见陷阱"></span>',
            '<span id="05-先做资源与时间对照表"></span>',
            '<span id="06-回答问题时按证据层级写"></span>',
            '<span id="07-磁盘仿真的分层流程"></span>',
            '<span id="08-pve-集群与-ceph-的入口"></span>',
            '<span id="09-仿真副本中的口令恢复"></span>',
            '<span id="10-实战核对一次磁盘快照与实例事件"></span>',
        },
        "git-docker-03": {
            '<span id="01-判断目录是否属于仓库"></span>',
            '<span id="02-git-元数据与泄露判断"></span>',
            '<span id="03-常规-git-操作及其取证影响"></span>',
            '<span id="04-实战确认一份站点目录是否包含完整仓库"></span>',
        },
        "git-docker-04": {
            '<span id="01-提交记录与全局视图"></span>',
            '<span id="02-按文件与补丁缩小范围"></span>',
            '<span id="03-diff-比较的三个层次"></span>',
            '<span id="04-历史敏感内容搜索"></span>',
            '<span id="05-实战定位当前目录已删除的配置版本"></span>',
        },
        "git-docker-05": {
            '<span id="01-log-与-reflog"></span>',
            '<span id="02-reset-三种模式"></span>',
            '<span id="03-恢复整个版本与单个文件"></span>',
            '<span id="04-实战找回-reset-前的配置提交"></span>',
        },
        "git-docker-06": {
            '<span id="01-git-对象模型"></span>',
            '<span id="02-使用-fsck-检查对象"></span>',
            '<span id="03-cat-file-按类型读取"></span>',
            '<span id="04-枚举对象与路径"></span>',
            '<span id="05-深度恢复的顺序"></span>',
            '<span id="06-实战从悬空提交恢复历史配置"></span>',
        },
        "git-docker-07": {
            '<span id="01-分支与远程跟踪引用"></span>',
            '<span id="02-tag-的对象含义"></span>',
            '<span id="03-stash-中的未提交状态"></span>',
            '<span id="04-从可疑行反查-blame"></span>',
            '<span id="05-实战比较备份分支发布标签和临时修改"></span>',
        },
        "git-docker-08": {
            '<span id="01-材料目录与首轮保全"></span>',
            '<span id="02-清点引用并建立提交图"></span>',
            '<span id="03-搜索历史内容并确认上下文"></span>',
            '<span id="04-本地引用记录与临时修改"></span>',
            '<span id="05-不可达对象与内容恢复"></span>',
            '<span id="06-实战串起删除文件与保留对象"></span>',
        },
    }.get(article_id, frozenset())
    for line in body.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
            lines.append(line)
            continue
        if fenced:
            lines.append(line)
            continue
        # Preserve reviewed empty legacy anchors, not arbitrary attributed HTML.
        if line in legacy_anchors:
            lines.append(line)
            continue
        parts = re.split(r"(`+[^`]*`+)", line)
        for index, part in enumerate(parts):
            if part.startswith("`"):
                continue
            parts[index] = re.sub(
                r"<([^<>\n]{1,120})>",
                lambda match: match.group(0) if preserve_html(match.group(1)) else f"&lt;{match.group(1)}&gt;",
                part,
            )
        lines.append("".join(parts))
    return "\n".join(lines)


def curate_forensic_note(identifier: str, body: str) -> str:
    """Use a reviewed standalone body without restoring exercise-specific prose."""
    guide = CURATION / f"{identifier}.md"
    if not guide.is_file():
        return body
    replacement = guide.read_text(encoding="utf-8").strip()
    if not replacement:
        raise ValueError(f"Empty forensic curation: {identifier}")
    return replacement


def apply_forensics_supplements() -> int:
    """Register reviewed additions and durable provenance without duplicating bodies."""
    registry_path = DATA / "forensics-supplements.json"
    if not registry_path.is_file():
        return 0
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    inventory = json.loads((DATA / "inventory.json").read_text(encoding="utf-8"))
    sources = {row["relativePath"]: row["id"] for row in inventory if row["kind"] == "source"}
    additions = {}
    for article in registry["articles"]:
        identifier = article["id"]
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", identifier) or identifier in additions:
            raise ValueError(f"Invalid or duplicate supplemental article: {identifier}")
        if article["module"] != "Forensics":
            raise ValueError(f"Supplement must belong to Forensics: {identifier}")
        path = NOTES / f"{identifier}.md"
        if path.is_file():
            _, existing = _body_and_meta(path)
            if existing.get("module") != "Forensics":
                raise ValueError(f"Supplement ID already used by another module: {identifier}")
        body = curate_forensic_note(identifier, "")
        if not body.strip():
            raise ValueError(f"Missing forensic curation: {identifier}")
        additions[identifier] = (article, body)

    # Validate every association before writing any page.
    associations = {}
    groups = []
    for group in registry["sources"]:
        source_id = sources.get(group["relativePath"])
        if not source_id:
            raise ValueError(f"Uncataloged forensic supplement: {group['relativePath']}")
        groups.append((source_id, group))
    web_ids = set()
    for group in registry.get("webSources", []):
        source_id = group.get("id", "")
        raw_url = group.get("url", "")
        if not isinstance(raw_url, str) or re.search(r"[\s\x00-\x1f\x7f]", raw_url):
            raise ValueError(f"Invalid web source URL: {source_id}")
        try:
            url = urlsplit(raw_url)
            url.port  # Reject malformed and out-of-range port numbers.
        except ValueError as error:
            raise ValueError(f"Invalid web source URL: {source_id}") from error
        if (not re.fullmatch(r"web-[a-z0-9]+(?:-[a-z0-9]+)*", source_id)
                or source_id in web_ids or url.scheme not in {"https", "http"}
                or not url.hostname or url.username or url.password):
            raise ValueError(f"Invalid or duplicate web source: {source_id}")
        web_ids.add(source_id)
        if group.get("reviewedAt"):
            date.fromisoformat(group["reviewedAt"])
        groups.append((source_id, group))
    for source_id, group in groups:
        for identifier in group["articleIds"]:
            if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", identifier):
                raise ValueError(f"Invalid supplemental association: {identifier}")
            if identifier not in additions:
                path = NOTES / f"{identifier}.md"
                if not path.is_file():
                    raise ValueError(f"Unknown supplemental association: {identifier}")
                _, metadata = _body_and_meta(path)
                if metadata.get("module") != "Forensics":
                    raise ValueError(f"Supplement cannot modify another module: {identifier}")
            associations.setdefault(identifier, []).append(source_id)

    created = 0
    for identifier, (article, body) in additions.items():
        path = NOTES / f"{identifier}.md"
        if not path.is_file():
            created += 1
        metadata = {key: value for key, value in article.items() if key != "id"}
        path.write_text(frontmatter(metadata) + "\n\n" + normalize_forensic_markdown(body, article_id=identifier) + "\n", encoding="utf-8")
    for identifier, linked_sources in associations.items():
        path = NOTES / f"{identifier}.md"
        text = path.read_text(encoding="utf-8")
        match = re.match(r"\A---\n(.*?)\n---\n\s*", text, re.DOTALL)
        _, metadata = _body_and_meta(path)
        values = list(dict.fromkeys([*metadata.get("sourceIds", []), *linked_sources]))
        header = match.group(1)
        line = "sourceIds: " + json.dumps(values, ensure_ascii=False)
        if re.search(r"(?m)^sourceIds:", header):
            header = re.sub(r"(?m)^sourceIds:.*$", line, header)
        else:
            header += "\n" + line
        path.write_text("---\n" + header + "\n---\n\n" + text[match.end():].rstrip() + "\n", encoding="utf-8")
    return created


def apply_forensics_curation() -> int:
    """Apply complete reviewed bodies after all generated sections are consolidated."""
    applied = 0
    review_dates = {}
    registry_path = DATA / "forensics-supplements.json"
    if registry_path.is_file():
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        for group in registry.get("webSources", []):
            if group.get("reviewedAt"):
                reviewed = date.fromisoformat(group["reviewedAt"]).isoformat()
                for identifier in group["articleIds"]:
                    review_dates[identifier] = max(review_dates.get(identifier, ""), reviewed)
    for path in sorted(NOTES.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        match = re.match(r"\A---\n(.*?)\n---\n\s*", text, re.DOTALL)
        if not match or not re.search(r'^module:\s*[\"\']?Forensics[\"\']?$', match.group(1), re.MULTILINE):
            continue
        guide = CURATION / path.name
        if not guide.is_file():
            continue
        body = normalize_forensic_markdown(curate_forensic_note(path.stem, text[match.end():]), article_id=path.stem)
        metadata = match.group(1)
        current_date = re.search(r'(?m)^updated:\s*["\']?([0-9-]+)', metadata)
        updated = max("2026-10-01", current_date[1] if current_date else "", review_dates.get(path.stem, ""))
        if current_date:
            metadata = re.sub(r'(?m)^updated:.*$', f'updated: "{updated}"', metadata)
        else:
            metadata += f'\nupdated: "{updated}"'
        if path.stem == "forensic-website-reconstruction":
            metadata = re.sub(r'(?m)^title:.*$', 'title: "网站重构：PHP、Java、Python、Node.js、IIS 与静态站"', metadata)
            metadata = re.sub(r'(?m)^summary:.*$', 'summary: "六类站点各自从材料定位做到业务验收；每一步核对浏览器入口、实际程序和数据库，就地处理失败。"', metadata)
            metadata = re.sub(r'(?m)^updated:.*$', 'updated: "' + max(updated, "2026-10-14") + '"', metadata)
        if path.stem == "forensic-method-index":
            metadata = re.sub(r'(?m)^title:.*$', 'title: "取证任务与证据路径索引"', metadata)
            metadata = re.sub(r'(?m)^summary:.*$', 'summary: "按分析目标、证据对象和系统路径定位操作步骤、结果判读与交叉验证方法。"', metadata)
        path.write_text("---\n" + metadata + "\n---\n\n" + body + "\n", encoding="utf-8")
        applied += 1
    return applied


FIC_CONTAINER_TRANSFERS = {
    "fic-case-03": {
        "start": "### 2.2 容器识别",
        "end": "### 2.3 服务与端口清点",
        "group": "docker-evidence-01",
        "title": "Docker 与 LXC 的现场识别",
        "replacement": "### 2.2 容器识别\n\n运行时、元数据和网桥的完整对照集中在 [Docker 与 LXC 的现场识别](/knowledge/docker-evidence-01/)；本页继续分析主机服务与用户痕迹。",
    },
    "fic-case-10": {
        "start": "### 9.5 容器网络",
        "end": "\n---",
        "group": "docker-evidence-05",
        "title": "容器网桥与通信归属",
        "replacement": "### 9.5 容器网络\n\n容器网络的识别、通信归属与验证集中在 [Docker 网络与 Compose](/knowledge/docker-evidence-05/)；本页保留代理、隧道和主机名解析的通用方法。",
    },
    "fic-case-13": {
        "start": "**（3）容器**",
        "end": "**（4）服务与端口**",
        "group": "docker-evidence-02",
        "title": "Docker 与 LXC 命令速查",
        "replacement": "**（3）容器**\n\n容器命令的参数、用途与验证集中在 [Docker 现场流程与操作边界](/knowledge/docker-evidence-02/)；这里继续列其他取证任务的命令。\n\n",
    },
}


def relocate_fic_container_detail(identifier: str, body: str) -> tuple[str, tuple[str, str, str] | None]:
    """Keep the full case-specific detail in one Docker topic and leave a route at its old location."""
    spec = FIC_CONTAINER_TRANSFERS.get(identifier)
    if not spec:
        return body, None
    start = body.index(spec["start"])
    end = body.index(spec["end"], start)
    excerpt = body[start:end].strip()
    if identifier == "fic-case-03":
        excerpt = excerpt.replace("无镜像概念（模板化）", "LXC/LXD 可使用镜像或模板；组织方式与 Docker 不同")
        excerpt = excerpt.replace("docker ps                                   # 有无容器", "docker ps                                   # 仅列当前运行的 Docker 容器；再查 docker ps -a")
        excerpt = excerpt.replace(
            "若在\"仿真后的系统\"里发现命令行为异常，说明当前 shell 实际落在容器内 → `Ctrl+Alt+F2` 切到真实系统；切换前须卸载容器内的 ssh 服务，否则端口冲突。",
            "若在仿真系统中发现命令行为异常，先核对主机名、进程命名空间与挂载信息，确认当前 shell 属于宿主机还是容器。切换终端或连接目标前记录状态；不要在原检材中卸载 SSH 服务。",
        )
        excerpt = excerpt.replace(
            "仿真成功后用 FinalShell 连接，装完 ssh 发现系统命令异常 → 判断仍在 LXC 容器内 → `apt-get remove --purge openssh-server` 后切换真实系统重装。",
            "仿真后远程连接发现命令环境异常，应先核对会话所属命名空间和主机身份；确认处于 LXC 后，改在仿真副本中选择正确的连接目标，不在原检材中删除服务。",
        )
    elif identifier == "fic-case-10":
        excerpt = excerpt.replace(
            "看该 IP 落在哪个网桥网段 → 即知容器技术。",
            "结合网桥所属运行时配置、容器元数据和该 IP 的实际归属判断；网段只提供线索。",
        )
        excerpt = excerpt.replace(
            "`10.0.3.100` 属 `lxcbr0`（10.0.3.1/24）网段 → 排除 Docker（其网段为 172.x）→ 判定 **LXC**。",
            "`10.0.3.100` 与现场 `lxcbr0`（10.0.3.1/24）同网段，再结合 LXC 配置和容器元数据确认 **LXC**。网段可配置，仅凭 10.x 或 172.x 不能排除 Docker。",
        )
    elif identifier == "fic-case-13":
        excerpt = excerpt.replace("有无容器；**负向结论必须由 LXC 正向证据补全**。", "清点当前和已停止的 Docker 容器；空结果不能排除已删除容器或其他运行时。")
        excerpt = excerpt.replace("→ 定容器技术。", "→ 结合运行时配置与元数据识别容器技术；网桥名和网段可自定义。")
    rest = body[:start].rstrip() + "\n\n" + spec["replacement"].strip() + "\n\n" + body[end:].lstrip()
    return rest, (spec["group"], spec["title"], excerpt)


def consolidate_docker_pages(fic_transfers: dict[str, list[tuple[str, str]]], fic_source_id: str) -> int:
    """Build five subject pages while retaining every numbered section's body."""
    all_ids = [identifier for group in DOCKER_GROUPS for identifier in group["ids"]]
    expected = {f"docker-case-{n:02d}" for n in range(1, 17)} | {"git-docker-02"} | {f"git-docker-{n:02d}" for n in range(9, 25)}
    if len(all_ids) != len(set(all_ids)) or set(all_ids) != expected:
        raise ValueError("Docker sections must each belong to exactly one consolidated page")
    for identifier in all_ids:
        if not (NOTES / f"{identifier}.md").exists():
            raise FileNotFoundError(identifier)
    for group in DOCKER_GROUPS:
        parts = [group["intro"]]
        source_ids = set()
        identifiers = [*group.get("archive", []), *group["ids"]]
        for index, identifier in enumerate(identifiers, 1):
            path = DOCKER_ARCHIVE / f"{identifier}.md" if identifier in group.get("archive", []) else NOTES / f"{identifier}.md"
            body, metadata = _body_and_meta(path)
            if identifier in group.get("archive", []):
                body = normalize_forensic_markdown(body)
            source_ids.update(metadata.get("sourceIds", []))
            parts.append(f"## {index:02d} {metadata['title']}\n\n{_nested_headings(body, index)}")
        for title, excerpt in fic_transfers.get(group["id"], []):
            index = len(parts)
            source_ids.add(fic_source_id)
            parts.append(f"## {index:02d} {title}\n\n{_nested_headings(excerpt, index)}")
        fm = frontmatter({"title": group["title"], "summary": group["summary"], "module": "Forensics", "track": "服务器取证", "topic": "Docker 与容器", "tags": group.get("tags", []), "status": "已整理", "sourceIds": sorted(source_ids), "challengeIds": [], "relatedIds": [], "updated": "2026-09-29"})
        (NOTES / f"{group['id']}.md").write_text(fm + "\n\n" + "\n\n".join(parts) + "\n", encoding="utf-8")
    for identifier in all_ids:
        (NOTES / f"{identifier}.md").unlink()
    return len(all_ids)


def consolidate_method_pages() -> int:
    """Merge overlapping method/index articles without dropping their examples or evidence paths."""
    identifiers = [identifier for group in METHOD_GROUPS for identifier in group["ids"]]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("A method section was assigned more than once")
    for group in METHOD_GROUPS:
        parts = []
        source_ids = set()
        for index, identifier in enumerate(group["ids"], 1):
            body, metadata = _body_and_meta(NOTES / f"{identifier}.md")
            source_ids.update(metadata.get("sourceIds", []))
            parts.append(f"## {index:02d} {metadata['title']}\n\n{_nested_headings(body, index)}")
        fm = frontmatter({"title": group["title"], "summary": group["summary"], "module": "Forensics", "track": "综合取证", "topic": group["topic"], "tags": [], "status": "已整理", "sourceIds": sorted(source_ids), "challengeIds": [], "relatedIds": [], "updated": "2026-09-29"})
        (NOTES / f"{group['id']}.md").write_text(fm + "\n\n" + "\n\n".join(parts) + "\n", encoding="utf-8")
    for identifier in identifiers:
        (NOTES / f"{identifier}.md").unlink()
    return len(identifiers)


def write_forensics_pages(source_ids: dict[str, str]) -> int:
    total = 0
    fic_transfers: dict[str, list[tuple[str, str]]] = {}
    markdown_inputs = [
        (ROOT / "Docker_服务器取证信息定位指南.md", "docker-case", "Docker 与容器"),
        (ROOT / "取证/2026FIC初赛-取证知识点-模块化复习手册.md", "fic-case", "竞赛取证"),
    ]
    for path, prefix, _ in markdown_inputs:
        source_id = source_ids[path.name]
        for n, section in enumerate(markdown_sections(path), 1):
            identifier = f"{prefix}-{n:02d}"
            title = forensics_title(identifier, section["title"])
            track, topic = forensics_classification(identifier)
            body = "\n".join(section["body"]).strip().replace("源文件", "输入文件")
            if n == 1:
                # The article page supplies its own title; keep the introduction
                # while removing the document-level heading from the visible body.
                body = re.sub(r"^# [^\n]+\n+", "", body, count=1)
            if identifier == "fic-case-14":
                body = re.sub(
                    r"^> \*\*定位\*\*：.*?(?=\n\n### 13\.1)",
                    "### 阅读范围\n\n"
                    "本页是跨平台证据路径索引，用来回答某类系统中的文件、日志和痕迹通常位于何处、能提取什么。"
                    "它不依赖某场比赛或某台机器的固定路径；实际取证仍须在检材上核对。\n\n"
                    "Linux、Windows、Android 路径在此串联，"
                    "包括 FHS 目录、注册表配置单元和事件日志。"
                    "需要按分析目标定位时，请查看"
                    "[取证任务与证据路径索引](/knowledge/forensic-method-index/)。"
                    "通用路径仍须核对系统版本、实际挂载与采集范围。"
                    "iOS 内容另见[iOS 备份与系统痕迹分析](/knowledge/forensic-ios-backup/)。\n\n"
                    "**阅读顺序：** Linux（13.2–13.3）→ Windows（13.4–13.6）→ Android（13.7）→ "
                    "应用层（13.8）→ 按检材翻找（13.9）→ 关联模式、易混辨析、工具与顺序（13.10–13.12）。",
                    body,
                    count=1,
                    flags=re.MULTILINE | re.DOTALL,
                )
            body, transfer = relocate_fic_container_detail(identifier, body)
            if transfer:
                group_id, transfer_title, excerpt = transfer
                fic_transfers.setdefault(group_id, []).append((transfer_title, normalize_forensic_markdown(excerpt)))
            body = curate_forensic_note(identifier, body)
            body = normalize_forensic_markdown(body)
            summary = forensics_summary(identifier, title)
            fm = frontmatter({"title": title, "summary": summary[:145], "module": "Forensics", "track": track, "topic": topic, "tags": [], "status": "已整理", "sourceIds": [source_id], "challengeIds": [], "relatedIds": [], "updated": "2026-10-01" if identifier == "fic-case-03" else "2026-09-29"})
            (NOTES / f"{identifier}.md").write_text(fm + "\n\n" + body + "\n", encoding="utf-8")
            total += 1
    path = ROOT / "_Git_Docker实战命令手册.docx"
    for section in sections_from_document(path, "git-docker", False):
        if section["title"] in {"目录", "参考资料与版本说明"}:
            continue
        title = forensics_title(section["id"], section["title"])
        track, topic = forensics_classification(section["id"])
        body = normalize_forensic_markdown("\n\n".join(section["parts"]).strip())
        summary = forensics_summary(section["id"], title)
        fm = frontmatter({"title": title, "summary": summary, "module": "Forensics", "track": track, "topic": topic, "tags": [], "status": "已整理", "sourceIds": [source_ids[path.name]], "challengeIds": [], "relatedIds": [], "updated": "2026-09-29"})
        (NOTES / f"{section['id']}.md").write_text(fm + "\n\n" + body + "\n", encoding="utf-8")
        total += 1
    removed = consolidate_docker_pages(fic_transfers, source_ids["2026FIC初赛-取证知识点-模块化复习手册.md"])
    method_removed = consolidate_method_pages()
    added = apply_forensics_supplements()
    apply_forensics_curation()
    return total - removed - method_removed + len(DOCKER_GROUPS) + len(METHOD_GROUPS) + added


if __name__ == "__main__":
    write_manual_pages()
