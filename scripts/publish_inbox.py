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
INBOX_DIR = ROOT / "inbox"
POSTS_DIR = ROOT / "_posts"
AUTO_MARKER = "<!-- generated-from-inbox -->"


@dataclass
class SourcePost:
    source_path: Path
    title: str
    body: str
    categories: list[str]
    date_str: str
    slug: str
    filename: str


def ensure_dirs() -> None:
    INBOX_DIR.mkdir(exist_ok=True)
    POSTS_DIR.mkdir(exist_ok=True)


def iter_markdown_files() -> list[Path]:
    return sorted(
        path
        for path in INBOX_DIR.rglob("*.md")
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
    rel_parent = path.relative_to(INBOX_DIR).parent
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


def yaml_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def build_post(path: Path) -> SourcePost:
    raw = read_text(path)
    fallback_title = path.stem
    title, body = split_title_and_body(raw, fallback_title)
    categories = relative_categories(path)
    commit_date = git_first_commit_date(path)
    date_str = normalize_git_date(commit_date) if commit_date else fallback_now()
    slug = slugify(path.stem)
    date_prefix = date_str[:10]
    digest = hashlib.sha1(str(path.relative_to(INBOX_DIR)).encode("utf-8")).hexdigest()[:8]
    filename = f"{date_prefix}-{slug}-{digest}.md"
    return SourcePost(path, title, body, categories, date_str, slug, filename)


def render_front_matter(post: SourcePost) -> str:
    categories = ", ".join(yaml_quote(item) for item in post.categories)
    return "\n".join(
        [
            "---",
            f"title: {yaml_quote(post.title)}",
            f"date: {post.date_str}",
            f"categories: [{categories}]",
            f"source_name: {yaml_quote(post.source_path.stem)}",
            f"slug: {yaml_quote(post.slug)}",
            f"inbox_source: {yaml_quote(post.source_path.relative_to(ROOT).as_posix())}",
            "---",
            "",
        ]
    )


def write_generated_posts(posts: list[SourcePost]) -> None:
    generated_names = {post.filename for post in posts}

    for existing in POSTS_DIR.glob("*.md"):
        try:
            content = existing.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        if AUTO_MARKER in content and existing.name not in generated_names:
            existing.unlink()

    for post in posts:
        output_path = POSTS_DIR / post.filename
        content = render_front_matter(post) + AUTO_MARKER + "\n\n" + post.body.strip() + "\n"
        output_path.write_text(content, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    posts = [build_post(path) for path in iter_markdown_files()]
    write_generated_posts(posts)
    print(f"published {len(posts)} inbox markdown file(s)")


if __name__ == "__main__":
    main()
