#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


API_URL = "https://open.assembly.go.kr/portal/openapi/nzmimeepazxkubdpn"
ENV_NAME = "OPEN_ASSEMBLY_API_KEY"
MEETING_RECORD_URL = "https://likms.assembly.go.kr/record/"
LEGISLATIVE_NOTICE_URL = "https://pal.assembly.go.kr"
OPEN_ASSEMBLY_URL = "https://open.assembly.go.kr"


class AssemblyError(RuntimeError):
    pass


def request_json(url: str, timeout: int = 30) -> Any:
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "k-gov-skills-national-assembly-tracker/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            body = resp.read().decode(charset, errors="replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise AssemblyError(f"HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise AssemblyError(f"request failed: {exc.reason}") from exc
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise AssemblyError(f"JSON parse failed: {exc}") from exc


def get_key(args: argparse.Namespace) -> str:
    if getattr(args, "key", None):
        return args.key.strip()
    value = os.environ.get(ENV_NAME)
    if value:
        return value.strip()
    raise AssemblyError(f"{ENV_NAME} environment variable is missing")


def build_bills_url(key: str, args: argparse.Namespace) -> str:
    params = {
        "KEY": key,
        "Type": "json",
        "pIndex": args.page,
        "pSize": args.page_size,
        "AGE": args.age,
    }
    if args.query:
        params["BILL_NAME"] = args.query
    return f"{API_URL}?{urllib.parse.urlencode(params)}"


def redact_url(url: str, key: str) -> str:
    return url.replace(urllib.parse.quote_plus(key), "<REDACTED>").replace(key, "<REDACTED>")


def parse_bill_response(payload: Any) -> tuple[int, list[dict[str, Any]], dict[str, Any]]:
    data = payload.get("nzmimeepazxkubdpn")
    if not isinstance(data, list) or len(data) < 2:
        raise AssemblyError(f"unexpected response shape: {payload}")
    head = data[0].get("head") or []
    total = 0
    result: dict[str, Any] = {}
    for item in head:
        if "list_total_count" in item:
            total = int(item["list_total_count"])
        if "RESULT" in item:
            result = item["RESULT"]
    if result and result.get("CODE") != "INFO-000":
        raise AssemblyError(f"API error: {result}")
    rows = data[1].get("row") or []
    if isinstance(rows, dict):
        rows = [rows]
    return total, rows, result


def normalize_bill(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "bill_id": row.get("BILL_ID") or "",
        "bill_no": row.get("BILL_NO") or "",
        "bill_name": row.get("BILL_NAME") or "",
        "committee": row.get("COMMITTEE") or "",
        "proposed_at": row.get("PROPOSE_DT") or "",
        "process_result": row.get("PROC_RESULT") or "",
        "age": row.get("AGE") or "",
        "detail_link": row.get("DETAIL_LINK") or "",
        "proposer": row.get("PROPOSER") or "",
        "lead_proposer": row.get("RST_PROPOSER") or "",
        "co_proposers": row.get("PUBL_PROPOSER") or "",
        "committee_presented_at": row.get("CMT_PRESENT_DT") or "",
        "committee_processed_at": row.get("CMT_PROC_DT") or "",
        "law_judiciary_processed_at": row.get("LAW_PROC_DT") or "",
        "plenary_processed_at": row.get("PROC_DT") or "",
        "raw": row,
    }


def official_links(query: str) -> dict[str, str]:
    encoded = urllib.parse.quote(query or "")
    return {
        "open_assembly": OPEN_ASSEMBLY_URL,
        "meeting_record": MEETING_RECORD_URL,
        "legislative_notice": LEGISLATIVE_NOTICE_URL,
        "bill_search_hint": f"{OPEN_ASSEMBLY_URL}/portal/data/service/selectServicePage.do?infId=OK7XM1000938DS17215",
        "query_encoded": encoded,
    }


def bills(args: argparse.Namespace) -> dict[str, Any]:
    key = get_key(args)
    url = build_bills_url(key, args)
    if args.dry_run:
        return {"dry_run": True, "request_url": redact_url(url, key), "links": official_links(args.query)}
    payload = request_json(url, timeout=args.timeout)
    total, rows, api_result = parse_bill_response(payload)
    normalized = [normalize_bill(row) for row in rows]
    if args.limit:
        normalized = normalized[: args.limit]
    return {
        "query": args.query,
        "age": args.age,
        "total_count": total,
        "api_result": api_result,
        "results": normalized,
        "request_url": redact_url(url, key),
        "links": official_links(args.query),
    }


def links(args: argparse.Namespace) -> dict[str, Any]:
    return {"query": args.query, "links": official_links(args.query)}


def impact_hint(item: dict[str, Any]) -> str:
    name = item.get("bill_name", "")
    if "인공지능" in name or "AI" in name.upper():
        return "AI 도입·활용·책임 기준 변화 가능성 확인"
    if "청년" in name:
        return "청년지원 사업·대상자 기준 변화 가능성 확인"
    if "고용" in name or "직업" in name:
        return "고용지원·직업훈련·장애인고용 업무 영향 확인"
    if "학자금" in name or "장학" in name:
        return "학자금·장학 지원 기준 변화 가능성 확인"
    return "소관 업무와 시행 의무 여부 확인"


def as_text(result: dict[str, Any]) -> str:
    if result.get("dry_run"):
        return f"요청 URL: {result['request_url']}"
    if "results" not in result:
        links_data = result["links"]
        return "\n".join(
            [
                f"검색어: {result.get('query') or '-'}",
                f"- 열린국회정보: {links_data['open_assembly']}",
                f"- 회의록시스템: {links_data['meeting_record']}",
                f"- 국회입법예고: {links_data['legislative_notice']}",
            ]
        )

    lines = [
        f"검색어: {result.get('query') or '-'} / 국회 대수: {result.get('age')}",
        f"전체 후보: {result.get('total_count')}건 / 표시: {len(result.get('results') or [])}건",
    ]
    for idx, item in enumerate(result.get("results") or [], start=1):
        lines.extend(
            [
                "",
                f"{idx}. {item.get('bill_name')}",
                f"- 의안번호: {item.get('bill_no') or '-'}",
                f"- 제안일: {item.get('proposed_at') or '-'} / 소관위: {item.get('committee') or '-'}",
                f"- 처리결과: {item.get('process_result') or '-'}",
                f"- 대표발의: {item.get('lead_proposer') or item.get('proposer') or '-'}",
                f"- 공동발의: {item.get('co_proposers') or '-'}",
                f"- 영향 확인: {impact_hint(item)}",
                f"- 상세: {item.get('detail_link') or '-'}",
            ]
        )
    links_data = result["links"]
    lines.extend(
        [
            "",
            "공식 추가 확인:",
            f"- 회의록시스템: {links_data['meeting_record']}",
            f"- 국회입법예고: {links_data['legislative_notice']}",
        ]
    )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Track Korean National Assembly bills by keyword")
    parser.add_argument("--timeout", type=int, default=30)
    sub = parser.add_subparsers(dest="command", required=True)

    bills_parser = sub.add_parser("bills", help="search bill list")
    bills_parser.add_argument("--query", required=True, help="bill name keyword")
    bills_parser.add_argument("--age", default="22", help="National Assembly term, default 22")
    bills_parser.add_argument("--page", type=int, default=1)
    bills_parser.add_argument("--page-size", type=int, default=20)
    bills_parser.add_argument("--limit", type=int, default=10)
    bills_parser.add_argument("--key", help="override key; prefer OPEN_ASSEMBLY_API_KEY env")
    bills_parser.add_argument("--dry-run", action="store_true")
    bills_parser.add_argument("--text", action="store_true")
    bills_parser.add_argument("--json", action="store_true")

    links_parser = sub.add_parser("links", help="show official follow-up links")
    links_parser.add_argument("--query", default="")
    links_parser.add_argument("--text", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = bills(args) if args.command == "bills" else links(args)
    except AssemblyError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if getattr(args, "text", False):
        print(as_text(result))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
