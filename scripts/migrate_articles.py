from __future__ import annotations

from datetime import date, timedelta
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "user-7866586-1775056047"
TARGET = ROOT / "_posts"


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = value.replace(" ", "-")
    value = re.sub(r"[\\/]+", "-", value)
    value = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value or "article"


def extract_title(text: str, fallback: str) -> str:
    for line in text.splitlines()[:6]:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or fallback
        break
    return fallback


def remove_leading_heading(text: str, title: str) -> str:
    lines = text.splitlines()
    if not lines:
        return text

    for index, line in enumerate(lines[:6]):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            heading = stripped.lstrip("#").strip()
            if heading == title:
                remaining = lines[index + 1 :]
                return "\n".join(remaining).lstrip("\n")
        break

    return text


def main() -> None:
    if TARGET.exists():
        shutil.rmtree(TARGET)
    TARGET.mkdir(parents=True, exist_ok=True)

    files = sorted(SOURCE.rglob("*.md"))
    start_date = date(2016, 1, 1)

    for index, src in enumerate(files, start=1):
        relative = src.relative_to(SOURCE)
        category = relative.parts[0] if len(relative.parts) > 1 else "未分类"
        source_name = src.stem
        body = src.read_text(encoding="utf-8")
        title = source_name
        body = remove_leading_heading(body, extract_title(body, source_name))
        slug = slugify(source_name)
        post_date = start_date + timedelta(days=index - 1)
        target_file = TARGET / f"{post_date.isoformat()}-{slug}.md"

        front_matter = "\n".join(
            [
                "---",
                f'title: "{title.replace(chr(34), chr(39))}"',
                f"date: {post_date.isoformat()} 08:00:00 +0800",
                f'categories: ["{category}"]',
                f'source_name: "{source_name.replace(chr(34), chr(39))}"',
                "---",
                "",
            ]
        )
        target_file.write_text(front_matter + body, encoding="utf-8")


if __name__ == "__main__":
    main()
