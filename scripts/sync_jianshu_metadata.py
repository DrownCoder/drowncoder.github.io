from __future__ import annotations

import html
import re
from pathlib import Path
from urllib.parse import urljoin

import requests


ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = ROOT / "_posts"
JIANSU_USER_URL = "https://www.jianshu.com/u/9dbc9b308ddb?order_by=shared_at"
HEADERS = {"User-Agent": "Mozilla/5.0"}


def normalize(text: str) -> str:
    text = html.unescape(text).strip().lower()
    text = text.replace("（", "(").replace("）", ")")
    text = text.replace("【", "[").replace("】", "]")
    text = text.replace("——", "-").replace("—", "-")
    text = text.replace("《", "").replace("》", "")
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[^\w\u4e00-\u9fff]+", "", text)
    return text


def scrape_jianshu_items() -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    for page in range(1, 20):
        url = f"{JIANSU_USER_URL}&page={page}"
        text = requests.get(url, headers=HEADERS, timeout=20).text
        blocks = re.findall(r'<li id="note-.*?</li>', text, re.S)
        page_items = []

        for block in blocks:
            title_match = re.search(r'class="title"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', block, re.S)
            shared_match = re.search(r'data-shared-at="([^"]+)"', block)
            views_match = re.search(r'ic-list-read"></i>\s*([^<\s]+)', block)

            if not title_match or not shared_match:
                continue

            item = {
                "title": html.unescape(title_match.group(2).strip()),
                "url": urljoin("https://www.jianshu.com", title_match.group(1)),
                "date": shared_match.group(1).replace("T", " "),
                "views": views_match.group(1) if views_match else "0",
            }
            page_items.append(item)

        new_items = [item for item in page_items if item["url"] not in seen_urls]
        if not new_items:
            break

        items.extend(new_items)
        seen_urls.update(item["url"] for item in new_items)

    return items


def parse_front_matter(path: Path) -> tuple[list[str], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{path} missing front matter")

    _, head, body = text.split("---\n", 2)
    return head.strip().splitlines(), body


def front_matter_value(lines: list[str], key: str) -> str | None:
    prefix = f"{key}:"
    for line in lines:
        if line.startswith(prefix):
            return line.split(":", 1)[1].strip().strip('"')
    return None


def set_front_matter_value(lines: list[str], key: str, value: str) -> list[str]:
    prefix = f"{key}:"
    if key == "date":
        rendered = f"{key}: {value}"
    else:
        rendered = f'{key}: "{value}"' if any(ch in value for ch in [":", "/", "+", " ", "[", "]"]) else f"{key}: {value}"

    for i, line in enumerate(lines):
        if line.startswith(prefix):
            lines[i] = rendered
            return lines

    insert_at = 1 if lines and lines[0].startswith("title:") else 0
    lines.insert(insert_at, rendered)
    return lines


def sync() -> tuple[int, int]:
    items = scrape_jianshu_items()
    lookup = {normalize(item["title"]): item for item in items}
    matched = 0
    unmatched = 0

    for path in sorted(POSTS_DIR.glob("*.md")):
        lines, body = parse_front_matter(path)
        source_name = front_matter_value(lines, "source_name") or path.stem
        title = front_matter_value(lines, "title") or source_name

        item = lookup.get(normalize(source_name)) or lookup.get(normalize(title))
        if not item:
            unmatched += 1
            continue

        matched += 1
        lines = [line for line in lines if not line.startswith("jianshu_url:") and not line.startswith("jianshu_views:")]
        lines = set_front_matter_value(lines, "title", item["title"])
        lines = set_front_matter_value(lines, "date", item["date"])
        lines.append(f'jianshu_views: {item["views"]}')
        lines.append(f'jianshu_url: "{item["url"]}"')
        new_text = "---\n" + "\n".join(lines) + "\n---\n" + body
        path.write_text(new_text, encoding="utf-8")

    return matched, unmatched


if __name__ == "__main__":
    matched, unmatched = sync()
    print(f"matched={matched}")
    print(f"unmatched={unmatched}")
