#!/usr/bin/env python3
"""
Example Korail receipt connector for transport-receipt-collector.

This public example documents the connector contract without publishing Korail
mobile internal endpoint URLs, request parameter names, captured payloads, or
ticket tokens.

To enable KTX/Korail receipt collection, copy this file to a private location,
implement `collect_receipt`, and point the wrapper to that private file:

PowerShell:
  $env:KGOV_KORAIL_CONNECTOR="C:\\Users\\<you>\\.openclaw\\private-connectors\\korail_receipt_connector.py"

The private connector should reuse your installed `ktx-booking` helper and must
print a JSON summary to stdout.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Example Korail receipt connector contract. Copy and implement privately before use."
    )
    parser.add_argument("--start-date", required=True, help="Start date, YYYY-MM-DD")
    parser.add_argument("--end-date", required=True, help="End date, YYYY-MM-DD")
    parser.add_argument("--row-index", type=int, default=1, help="1-based row index from the purchase-history list")
    parser.add_argument("--output-dir", help="Directory where redacted JSON and PNG should be saved")
    parser.add_argument("--base-name", help="Optional output file base name")
    parser.add_argument("--list-only", action="store_true", help="List receipt candidates only")
    parser.add_argument("--render-local", action="store_true", help="Render a local receipt PNG from official receipt data")
    return parser


def collect_receipt(args: argparse.Namespace) -> dict[str, Any]:
    """Implement this function in a private connector.

    Expected behavior:
      1. Authenticate with locally configured Korail/KTX credentials.
      2. Query purchase-history rows for the requested date range.
      3. If --list-only is set, return redacted row candidates only.
      4. Select --row-index.
      5. Save redacted JSON and KorailTalk-style PNG outputs.
      6. Return a JSON-serializable summary.

    Do not write raw credentials, ticket tokens, card numbers, approval numbers,
    or unredacted server payloads to stdout, logs, or committed files.
    """
    output_dir = Path(args.output_dir) if args.output_dir else Path("outputs") / "receipts" / args.end_date[:7]
    return {
        "provider": "korail-local-connector-example",
        "range": {"startDate": args.start_date, "endDate": args.end_date},
        "rowIndex": args.row_index,
        "output": {
            "jsonPath": str(output_dir / "example-redacted.json"),
            "pngPath": str(output_dir / "example-receipt.png"),
            "imageSource": "not-implemented",
        },
        "status": "not_implemented_public_example",
        "message": (
            "This is a public connector template only. Copy it to a private path, "
            "implement the Korail receipt lookup with your installed ktx-booking helper, "
            "then set KGOV_KORAIL_CONNECTOR to that private .py file."
        ),
    }


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    result = collect_receipt(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
