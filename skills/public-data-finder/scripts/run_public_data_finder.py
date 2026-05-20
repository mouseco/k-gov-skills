#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import textwrap
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


OAS_URL = "https://infuser.odcloud.kr/oas/docs?namespace=15062804/v1"
API_BASE = "https://api.odcloud.kr/api"
FALLBACK_PATH = "/15062804/v1/uddi:27a52f84-d64f-438d-bc59-e4f705ebd386"
FALLBACK_LABEL = "공공데이터활용지원센터_공공데이터포털 목록개방현황_20260430"
ENV_NAME = "DATA_GO_KR_API_KEY"


class PublicDataError(RuntimeError):
    pass


@dataclass
class Endpoint:
    path: str
    label: str
    date: str
    source: str


def request_json(url: str, timeout: int = 30) -> Any:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "k-gov-skills-public-data-finder/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            body = resp.read().decode(charset, errors="replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise PublicDataError(f"HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise PublicDataError(f"request failed: {exc.reason}") from exc
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise PublicDataError(f"JSON parse failed: {exc}") from exc


def discover_latest_endpoint(timeout: int = 30) -> Endpoint:
    try:
        oas = request_json(OAS_URL, timeout=timeout)
        paths = oas.get("paths") or {}
        candidates: list[Endpoint] = []
        for path, spec in paths.items():
            get_spec = spec.get("get") if isinstance(spec, dict) else {}
            label = str((get_spec or {}).get("summary") or (get_spec or {}).get("description") or path)
            match = re.search(r"(20\d{6})", label)
            if not match or "목록개방현황" not in label:
                continue
            candidates.append(Endpoint(path=path, label=label, date=match.group(1), source="oas"))
        if candidates:
            return sorted(candidates, key=lambda item: item.date)[-1]
    except Exception:
        pass
    return Endpoint(path=FALLBACK_PATH, label=FALLBACK_LABEL, date="20260430", source="fallback")


def get_service_key(args: argparse.Namespace) -> str:
    if getattr(args, "service_key", None):
        return args.service_key.strip()
    value = os.environ.get(ENV_NAME)
    if value:
        return value.strip()
    raise PublicDataError(f"{ENV_NAME} environment variable is missing")


def build_url(endpoint: Endpoint, key: str, args: argparse.Namespace) -> str:
    params: dict[str, str | int] = {
        "page": args.page,
        "perPage": args.per_page,
        "serviceKey": key,
    }
    if args.query:
        params["cond[목록명::LIKE]"] = args.query
    if args.org:
        params["cond[제공기관::LIKE]"] = args.org
    if args.category:
        params["cond[분류체계::LIKE]"] = args.category
    if args.list_type:
        params["cond[목록유형::EQ]"] = args.list_type.upper()
    return f"{API_BASE}{endpoint.path}?{urllib.parse.urlencode(params)}"


def redact_url(url: str, key: str) -> str:
    if not key:
        return url
    return url.replace(urllib.parse.quote_plus(key), "<REDACTED>").replace(key, "<REDACTED>")


def normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": row.get("목록명") or row.get("파일데이터명") or "",
        "file_name": row.get("파일데이터명") or "",
        "organization": row.get("제공기관") or "",
        "list_type": row.get("목록유형") or "",
        "api_type": row.get("API 유형") or "",
        "category": row.get("분류체계") or "",
        "update_cycle": row.get("업데이트 주기") or "",
        "next_update": row.get("차기 등록 예정일") or "",
        "traffic": row.get("신청가능 트래픽") or "",
        "review_type": row.get("심의 유형") or "",
        "views": row.get("조회수") or "",
        "url": row.get("목록 URL") or "",
        "description": row.get("설명") or "",
        "raw": row,
    }


def search(args: argparse.Namespace) -> dict[str, Any]:
    endpoint = discover_latest_endpoint(timeout=args.timeout)
    key = get_service_key(args)
    url = build_url(endpoint, key, args)
    if args.dry_run:
        return {
            "endpoint": endpoint.__dict__,
            "url": redact_url(url, key),
            "note": "dry-run only; no API request was sent",
        }
    payload = request_json(url, timeout=args.timeout)
    rows = [normalize_row(row) for row in payload.get("data", [])]
    if args.limit:
        rows = rows[: args.limit]
    return {
        "endpoint": endpoint.__dict__,
        "page": payload.get("page"),
        "per_page": payload.get("perPage"),
        "current_count": payload.get("currentCount"),
        "total_count": payload.get("totalCount"),
        "results": rows,
        "source_url": redact_url(url, key),
    }


def latest(args: argparse.Namespace) -> dict[str, Any]:
    endpoint = discover_latest_endpoint(timeout=args.timeout)
    return {"endpoint": endpoint.__dict__, "oas_url": OAS_URL}


def as_text(result: dict[str, Any]) -> str:
    if "results" not in result:
        ep = result["endpoint"]
        return f"최신 endpoint: {ep['label']}\npath: {ep['path']}\nsource: {ep['source']}"

    ep = result["endpoint"]
    lines = [
        f"기준 데이터: {ep['label']} ({ep['source']})",
        f"검색 결과: {result.get('current_count')}건 표시 / 전체 {result.get('total_count')}건",
    ]
    for idx, row in enumerate(result["results"], start=1):
        desc = " ".join(str(row.get("description") or "").split())
        lines.extend(
            [
                "",
                f"{idx}. {row.get('name')}",
                f"- 제공기관: {row.get('organization')}",
                f"- 유형: {row.get('list_type') or '-'} / API 유형: {row.get('api_type') or '-'}",
                f"- 분류: {row.get('category') or '-'}",
                f"- 갱신: {row.get('update_cycle') or '-'} / 다음 등록: {row.get('next_update') or '-'}",
                f"- 조회수: {row.get('views') or '-'}",
                f"- URL: {row.get('url') or '-'}",
            ]
        )
        if desc:
            lines.append("- 설명: " + textwrap.shorten(desc, width=180, placeholder="..."))
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search data.go.kr public dataset listing API")
    parser.add_argument("--timeout", type=int, default=30)
    sub = parser.add_subparsers(dest="command", required=True)

    latest_parser = sub.add_parser("latest", help="show latest monthly listing endpoint")
    latest_parser.add_argument("--text", action="store_true")

    search_parser = sub.add_parser("search", help="search public data listings")
    search_parser.add_argument("--query", required=True, help="keyword for 목록명 LIKE search")
    search_parser.add_argument("--org", help="provider organization LIKE filter")
    search_parser.add_argument("--category", help="classification LIKE filter")
    search_parser.add_argument("--list-type", choices=["FILE", "API", "STANDARD", "file", "api", "standard"])
    search_parser.add_argument("--page", type=int, default=1)
    search_parser.add_argument("--per-page", type=int, default=20)
    search_parser.add_argument("--limit", type=int, default=10)
    search_parser.add_argument("--service-key", help="override service key; prefer DATA_GO_KR_API_KEY env")
    search_parser.add_argument("--dry-run", action="store_true")
    search_parser.add_argument("--text", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = latest(args) if args.command == "latest" else search(args)
    except PublicDataError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if getattr(args, "text", False):
        print(as_text(result))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
