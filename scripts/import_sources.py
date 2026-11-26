"""Read-only file inventory for the adjacent source archive."""

import argparse
import hashlib
import json
import zipfile
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_DIR.parent
DATA_DIR = PROJECT_DIR / "src" / "data"
MODULES = {
    "Web Exploitation": "Web",
    "Miscellaneous": "Misc",
    "Misc": "Misc",
    "Reverse Engineering": "Reverse",
    "Reverse": "Reverse",
    "Cryptography": "Crypto",
    "Crypto": "Crypto",
    "Binary Exploitation": "Archive",
    "Pwn": "Archive",
}


def stable_id(relative_path):
    key = relative_path.as_posix().casefold().encode("utf-8")
    return hashlib.sha256(key).hexdigest()[:12]


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def classify_archive(relative_path):
    parts = relative_path.parts
    if len(parts) >= 4 and parts[0] == "Misc题收集":
        return MODULES.get(parts[2], "Misc")
    return "Misc"


def classify_source(relative_path):
    name = relative_path.name.lower()
    if relative_path.parts[0] == "取证" or "docker" in name or "git_" in name:
        return "Forensics"
    if relative_path.suffix.lower() == ".txt" and relative_path.parts[0] == "Misc题收集":
        return "Archive"
    return "Misc"


def contest_for(relative_path):
    parts = relative_path.parts
    return parts[1] if len(parts) >= 3 and parts[0] == "Misc题收集" else "个人资料"


def title_for(relative_path):
    if relative_path.suffix.lower() == ".zip":
        parent = relative_path.parent.name
        name = relative_path.stem
        if parent in {"Web Exploitation", "Miscellaneous", "Reverse Engineering", "Cryptography", "Binary Exploitation", "Misc", "Reverse", "Crypto", "Pwn"}:
            return name
        return parent if name in {"attachment", "attachments", "task", "chall", "challenge", "main"} else name
    return relative_path.stem


def wp_status(root, relative_path):
    parent = root / relative_path.parent
    if any((parent / filename).exists() for filename in ("WRITEUP.md", "haha-wp.pdf", "wkm的保险箱-wp.pdf")):
        return "local"
    if relative_path.parts[0] == "Misc题收集" and len(relative_path.parts) > 1:
        if (root / "Misc题收集" / relative_path.parts[1] / "wp.txt").exists():
            return "external"
    return "none"


def build_inventory(root):
    rows = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if rel.parts[0] == "ctf-atlas" or any(part.startswith(".") for part in rel.parts):
            continue
        kind = "challenge" if path.suffix.lower() == ".zip" else "source"
        row = {
            "id": stable_id(rel),
            "kind": kind,
            "title": title_for(rel),
            "name": path.name,
            "relativePath": rel.as_posix(),
            "extension": path.suffix.lower(),
            "module": classify_archive(rel) if kind == "challenge" else classify_source(rel),
            "contest": contest_for(rel),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        if kind == "challenge":
            row["wpStatus"] = wp_status(root, rel)
            try:
                with zipfile.ZipFile(path) as archive:
                    infos = archive.infolist()
                    row["archiveEntries"] = len(infos)
                    row["encrypted"] = any(info.flag_bits & 1 for info in infos)
            except zipfile.BadZipFile:
                row["archiveEntries"] = None
                row["encrypted"] = None
        rows.append(row)
    return rows


def build_external_links(root, inventory):
    links = {}
    for row in inventory:
        if row["name"] != "wp.txt":
            continue
        value = (root / row["relativePath"]).read_text(encoding="utf-8-sig", errors="replace").strip()
        if value.startswith("https://") and "\n" not in value:
            links[row["id"]] = value
    return links


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=SOURCE_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DATA_DIR)
    args = parser.parse_args()
    inventory = build_inventory(args.source_root)
    links = build_external_links(args.source_root, inventory)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for filename, data in (("inventory.json", inventory), ("external-links.json", links)):
        (args.output_dir / filename).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Cataloged %d files: %d challenge archives, %d external WP links" % (
        len(inventory), sum(item["kind"] == "challenge" for item in inventory), len(links)))


if __name__ == "__main__":
    main()
