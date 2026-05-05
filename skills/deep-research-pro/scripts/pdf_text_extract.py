#!/usr/bin/env python3
"""Extract text from a PDF when the native pdf tool is unavailable.

Usage:
  python scripts/pdf_text_extract.py <pdf> --pages 1-5 --max-chars 12000
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def parse_pages(spec: str | None, total: int) -> list[int]:
    if not spec:
        return list(range(total))
    pages: set[int] = set()
    for part in spec.split(','):
        part = part.strip()
        if not part:
            continue
        if '-' in part:
            a, b = part.split('-', 1)
            pages.update(range(max(1, int(a)), min(total, int(b)) + 1))
        else:
            pages.add(int(part))
    return [p - 1 for p in sorted(pages) if 1 <= p <= total]


def clean(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_with_pypdf(path: Path, pages_spec: str | None) -> tuple[str, int]:
    from pypdf import PdfReader
    reader = PdfReader(str(path))
    pages = parse_pages(pages_spec, len(reader.pages))
    chunks = []
    for i in pages:
        chunks.append(f"\n\n--- page {i+1} ---\n" + (reader.pages[i].extract_text() or ""))
    return clean("".join(chunks)), len(reader.pages)


def extract_with_pdfplumber(path: Path, pages_spec: str | None) -> tuple[str, int]:
    import pdfplumber
    with pdfplumber.open(str(path)) as pdf:
        pages = parse_pages(pages_spec, len(pdf.pages))
        chunks = []
        for i in pages:
            chunks.append(f"\n\n--- page {i+1} ---\n" + (pdf.pages[i].extract_text() or ""))
        return clean("".join(chunks)), len(pdf.pages)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf")
    parser.add_argument("--pages")
    parser.add_argument("--max-chars", type=int, default=12000)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    path = Path(args.pdf)
    errors = []
    text = ""
    total_pages = 0
    for extractor in (extract_with_pypdf, extract_with_pdfplumber):
        try:
            text, total_pages = extractor(path, args.pages)
            if text:
                break
        except Exception as exc:
            errors.append(f"{extractor.__name__}: {exc}")
    text = text[: args.max_chars]
    result = {"ok": bool(text), "path": str(path), "pages": total_pages, "chars": len(text), "errors": errors, "text": text}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(text)
        if errors and not text:
            print("\nErrors:\n" + "\n".join(errors), file=sys.stderr)
    return 0 if text else 1


if __name__ == "__main__":
    raise SystemExit(main())
