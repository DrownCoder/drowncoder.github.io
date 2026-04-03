#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content"
POSTS_DIR = ROOT / "_posts"


@dataclass
class SourcePost:
    source_path: Path
    filename: str
    content: str


def ensure_dirs() -> None:
    CONTENT_DIR.mkdir(exist_ok=True)
    POSTS_DIR.mkdir(exist_ok=True)


def iter_markdown_files() -> list[Path]:
    return sorted(
        path
        for path in CONTENT_DIR.rglob("*.md")
        if path.is_file() and not any(part.startswith(".") for part in path.parts)
    )


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def split_title_and_body(text: str, fallback_title: str) -> tuple[str, str]:
    lines = text.splitlines()
    idx = 0

    while idx < len(lines) and not lines[idx].strip():
        idx += 1

    if idx < len(lines) and lines[idx].startswith("# "):
        title = lines[idx][2:].strip() or fallback_title
        body_lines = lines[:idx] + lines[idx + 1 :]
        while body_lines and not body_lines[0].strip():
            body_lines = body_lines[1:]
        body = "\n".join(body_lines).strip()
        return title, body

    return fallback_title, text.strip()


def slugify(text: str) -> str:
    base = text.lower().strip()
    base = re.sub(r"[《》【】（）()\[\]，。！？：；、“”‘’'\"`]+", "-", base)
    base = re.sub(r"[^a-z0-9\u4e00-\u9fff\-_ ]+", "-", base)
    base = base.replace("_", "-").replace(" ", "-")
    base = re.sub(r"-{2,}", "-", base).strip("-")

    ascii_only = re.sub(r"[^a-z0-9-]+", "", base)
    if ascii_only:
        return ascii_only

    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]
    return f"post-{digest}"


def relative_categories(path: Path) -> list[str]:
    rel_parent = path.relative_to(CONTENT_DIR).parent
    if str(rel_parent) == ".":
        return ["未分类"]
    return [part for part in rel_parent.parts if part and not part.startswith(".")]


def git_first_commit_date(path: Path) -> str | None:
    rel_path = os.path.relpath(path, ROOT)
    try:
        result = subprocess.run(
            ["git", "log", "--follow", "--format=%aI", "--", rel_path],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if not lines:
        return None
    return lines[-1]


def fallback_now() -> str:
    now = datetime.now().astimezone()
    return now.strftime("%Y-%m-%d %H:%M:%S %z")


def normalize_git_date(value: str) -> str:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return dt.astimezone().strftime("%Y-%m-%d %H:%M:%S %z")


def split_front_matter(text: str) -> tuple[dict[str, str], str] | None:
    if not text.startswith("---\n"):
        return None

    end = text.find("\n---\n", 4)
    if end == -1:
        return None

    front_matter_text = text[4:end]
    body = text[end + 5 :]
    data: dict[str, str] = {}

    for line in front_matter_text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()

    return data, body


def update_categories_line(raw: str, categories: list[str]) -> str:
    categories_text = ", ".join(yaml_quote(item) for item in categories)
    replacement = f"categories: [{categories_text}]"

    if re.search(r"^categories:\s*\[.*?\]\s*$", raw, re.M):
        return re.sub(r"^categories:\s*\[.*?\]\s*$", replacement, raw, count=1, flags=re.M)

    if raw.startswith("---\n"):
        end = raw.find("\n---\n", 4)
        if end != -1:
            front_matter = raw[4:end]
            body = raw[end + 5 :]
            if front_matter and not front_matter.endswith("\n"):
                front_matter += "\n"
            front_matter += replacement + "\n"
            return "---\n" + front_matter + "---\n" + body

    return raw


def yaml_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def normalize_title(title: str, categories: list[str]) -> str:
    normalized = title.strip()

    if "年度总结" in categories and not normalized.startswith("【"):
        match = re.match(r"^(\d{4}年度总结)(.*)$", normalized)
        if match:
            prefix, suffix = match.groups()
            suffix = suffix.strip()

            if not suffix:
                return f"【{prefix}】"

            if suffix.startswith("-") or suffix.startswith("—"):
                return f"【{prefix}】{suffix}"

            return f"【{prefix}】-{suffix}"

    return normalized


def build_post(path: Path) -> SourcePost:
    raw = read_text(path)
    folder_categories = relative_categories(path)
    parsed = split_front_matter(raw)

    if parsed:
        if folder_categories != ["未分类"]:
            raw = update_categories_line(raw, folder_categories)

        filename = path.name if re.match(r"^\d{4}-\d{2}-\d{2}-.+\.md$", path.name) else ""

        if not filename:
            metadata = split_front_matter(raw)[0]
            raw_date = metadata.get("date", "")
            normalized_date = raw_date[:10] if re.match(r"^\d{4}-\d{2}-\d{2}", raw_date) else fallback_now()[:10]
            filename = f"{normalized_date}-{path.stem}.md"

        return SourcePost(path, filename, raw if raw.endswith("\n") else raw + "\n")

    fallback_title = path.stem
    title, body = split_title_and_body(raw, fallback_title)
    commit_date = git_first_commit_date(path)
    date_str = normalize_git_date(commit_date) if commit_date else fallback_now()
    slug = slugify(path.stem)
    filename = f"{date_str[:10]}-{path.stem}.md"
    title = normalize_title(title, folder_categories)
    content = render_front_matter(title, date_str, folder_categories, path, slug) + body.strip() + "\n"
    return SourcePost(path, filename, content)


def render_front_matter(
    title: str,
    date_str: str,
    categories: list[str],
    source_path: Path,
    slug: str,
) -> str:
    categories_text = ", ".join(yaml_quote(item) for item in categories)
    return "\n".join(
        [
            "---",
            f"title: {yaml_quote(title)}",
            f"date: {date_str}",
            f"categories: [{categories_text}]",
            f"source_name: {yaml_quote(source_path.stem)}",
            f"slug: {yaml_quote(slug)}",
            f"content_source: {yaml_quote(source_path.relative_to(ROOT).as_posix())}",
            "---",
            "",
        ]
    )


def write_generated_posts(posts: list[SourcePost]) -> None:
    for existing in POSTS_DIR.glob("*.md"):
        existing.unlink()

    for post in posts:
        output_path = POSTS_DIR / post.filename
        output_path.write_text(post.content, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    posts = [build_post(path) for path in iter_markdown_files()]
    write_generated_posts(posts)
    print(f"published {len(posts)} content markdown file(s)")


if __name__ == "__main__":
    main()
