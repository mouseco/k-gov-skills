#!/usr/bin/env python3
"""Download a research source to a local file when first-class tools cannot read it.

Usage:
  python scripts/source_fetch.py <url> --out <directory> [--name filename]

The script prints a small JSON object with path, content_type, and size.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) OpenClaw deep-research-pro/1.1"


def safe_name_from_url(url: str, content_type: str | None = None) -> str:
    parsed = urlparse(url)
    raw = Path(unquote(parsed.path)).name or "source"
    raw = re.sub(r"[^0-9A-Za-z가-힣._-]+", "_", raw).strip("._") or "source"
    if "." not in raw:
        if content_type and "pdf" in content_type.lower():
            raw += ".pdf"
        elif content_type and "html" in content_type.lower():
            raw += ".html"
        else:
            raw += ".bin"
    return raw[:160]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--out", required=True, help="Output directory")
    parser.add_argument("--name", help="Optional output filename")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    req = Request(args.url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=45) as resp:
        data = resp.read()
        content_type = resp.headers.get("Content-Type", "")
        final_url = resp.geturl()

    name = args.name or safe_name_from_url(final_url, content_type)
    path = out_dir / name
    path.write_bytes(data)

    print(json.dumps({
        "ok": True,
        "url": args.url,
        "final_url": final_url,
        "path": str(path),
        "content_type": content_type,
        "bytes": len(data),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)
