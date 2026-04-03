from __future__ import annotations

import hashlib
import mimetypes
import re
from pathlib import Path
from urllib.parse import urlparse

import requests


ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = ROOT / "_posts"
IMAGE_DIR = ROOT / "assets" / "img" / "posts"
HEADERS = {"User-Agent": "Mozilla/5.0"}

PATTERN = re.compile(r'(?P<prefix>!\[[^\]]*\]\()(?P<url>https?://upload-images\.jianshu\.io/[^\s)]+)(?P<suffix>\))')


def infer_extension(url: str, content_type: str) -> str:
    path = urlparse(url).path
    suffix = Path(path).suffix.lower()
    if suffix:
        return suffix
    guessed = mimetypes.guess_extension(content_type.split(";")[0].strip()) if content_type else None
    return guessed or ".jpg"


def download(url: str) -> str:
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    ext = infer_extension(url, response.headers.get("Content-Type", ""))
    filename = f"{digest}{ext}"
    target = IMAGE_DIR / filename
    if not target.exists():
      target.write_bytes(response.content)
    return f"/assets/img/posts/{filename}"


def main() -> None:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    cache: dict[str, str] = {}
    total = 0

    for path in sorted(POSTS_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")

        def repl(match: re.Match[str]) -> str:
            nonlocal total
            url = match.group("url")
            if url not in cache:
                cache[url] = download(url)
                total += 1
            return f'{match.group("prefix")}{cache[url]}{match.group("suffix")}'

        updated = PATTERN.sub(repl, text)
        if updated != text:
            path.write_text(updated, encoding="utf-8")

    print(f"downloaded={total}")


if __name__ == "__main__":
    main()
