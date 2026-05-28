#!/usr/bin/env python3
"""Lightweight validation for deep-research-pro markdown reports."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REQUIRED_HEADINGS = [
    "Executive Summary",
    "출처",
    "조사 방법",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report")
    parser.add_argument("--min-sources", type=int, default=3)
    parser.add_argument(
        "--require-pdf-evidence",
        action="store_true",
        help="Require evidence that at least one PDF or attachment body was inspected.",
    )
    args = parser.parse_args()

    path = Path(args.report)
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    missing = [h for h in REQUIRED_HEADINGS if h not in text]
    links = re.findall(r'https?://[^\s)>"\']+', text)
    md_links = re.findall(r"\[[^\]]+\]\(https?://[^)]+\)", text)
    source_count = max(len(set(links)), len(set(md_links)))
    single_source_flag = any(k in text for k in ["단일 출처", "추가 확인 필요", "한계"])
    pdf_evidence = any(
        k in text
        for k in [
            "PDF 본문 확인",
            "PDF 텍스트 추출",
            "첨부 PDF 확인",
            "pdf_text_extract.py",
            "source_fetch.py",
        ]
    )

    ok = not missing and source_count >= args.min_sources and single_source_flag
    if args.require_pdf_evidence:
        ok = ok and pdf_evidence
    result = {
        "ok": ok,
        "report": str(path),
        "missing_headings": missing,
        "source_count_estimate": source_count,
        "has_limit_or_single_source_flag": single_source_flag,
        "has_pdf_evidence": pdf_evidence,
        "require_pdf_evidence": args.require_pdf_evidence,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
