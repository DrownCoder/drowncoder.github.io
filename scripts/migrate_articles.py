from __future__ import annotations

import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "user-7866586-1775056047"
TARGET = ROOT / "_articles"


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


def main() -> None:
    if TARGET.exists():
        shutil.rmtree(TARGET)
    TARGET.mkdir(parents=True, exist_ok=True)

    files = sorted(SOURCE.rglob("*.md"))
    for index, src in enumerate(files, start=1):
        relative = src.relative_to(SOURCE)
        category = relative.parts[0] if len(relative.parts) > 1 else "未分类"
        source_name = src.stem
        body = src.read_text(encoding="utf-8")
        title = extract_title(body, source_name)
        slug = slugify(source_name)
        category_slug = slugify(category)
        target_dir = TARGET / category_slug
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / f"{slug}.md"

        front_matter = "\n".join(
            [
                "---",
                f'title: "{title.replace(chr(34), chr(39))}"',
                f'category: "{category}"',
                f'category_slug: "{category_slug}"',
                f'source_name: "{source_name.replace(chr(34), chr(39))}"',
                f"sort_key: {index:04d}",
                "---",
                "",
            ]
        )
        target_file.write_text(front_matter + body, encoding="utf-8")


if __name__ == "__main__":
    main()
