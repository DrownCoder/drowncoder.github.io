from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = ROOT / "_posts"


def main() -> None:
    for path in sorted(POSTS_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            continue

        _, head, body = text.split("---\n", 2)
        lines = head.strip().splitlines()
        source_name = None

        for line in lines:
            if line.startswith("source_name:"):
                source_name = line.split(":", 1)[1].strip().strip('"')
                break

        if not source_name:
            continue

        replaced = False
        for i, line in enumerate(lines):
            if line.startswith("title:"):
                lines[i] = f'title: "{source_name}"'
                replaced = True
                break

        if not replaced:
            lines.insert(0, f'title: "{source_name}"')

        path.write_text("---\n" + "\n".join(lines) + "\n---\n" + body, encoding="utf-8")


if __name__ == "__main__":
    main()
