#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import textwrap
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


BASE_URL = "http://apis.data.go.kr/1230000/ad/BidPublicInfoService"
ENV_NAME = "NARAJANGTEO_SERVICE_KEY"
OPS = {
    "service": ("getBidPblancListInfoServc", "용역"),
    "goods": ("getBidPblancListInfoThng", "물품"),
    "construction": ("getBidPblancListInfoCnstwk", "공사"),
}


class G2BError(RuntimeError):
    pass


def request_json(url: str, timeout: int = 30) -> Any:
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "k-gov-skills-g2b-bid-search/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            body = resp.read().decode(charset, errors="replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise G2BError(f"HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise G2BError(f"request failed: {exc.reason}") from exc
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise G2BError(f"JSON parse failed: {exc}") from exc


def get_service_key(args: argparse.Namespace) -> str:
    if args.service_key:
        return args.service_key.strip()
    value = os.environ.get(ENV_NAME)
    if value:
        return value.strip()
    raise G2BError(f"{ENV_NAME} environment variable is missing")


def ymdhm(value: dt.datetime) -> str:
    return value.strftime("%Y%m%d%H%M")


def resolve_period(args: argparse.Namespace) -> tuple[str, str]:
    if args.from_date or args.to_date:
        if not (args.from_date and args.to_date):
            raise G2BError("--from-date and --to-date must be used together")
        return args.from_date.replace("-", "") + "0000", args.to_date.replace("-", "") + "2359"
    now = dt.datetime.now()
    start = now - dt.timedelta(days=args.days)
    return ymdhm(start.replace(hour=0, minute=0)), ymdhm(now.replace(hour=23, minute=59))


def build_url(op: str, key: str, page: int, rows: int, start: str, end: str) -> str:
    params = {
        "serviceKey": key,
        "pageNo": page,
        "numOfRows": rows,
        "type": "json",
        "inqryDiv": "1",
        "inqryBgnDt": start,
        "inqryEndDt": end,
    }
    return f"{BASE_URL}/{op}?{urllib.parse.urlencode(params)}"


def redact_url(url: str, key: str) -> str:
    return url.replace(urllib.parse.quote_plus(key), "<REDACTED>").replace(key, "<REDACTED>")


def money(value: Any) -> str:
    if value in (None, ""):
        return ""
    try:
        return f"{int(float(str(value))):,}원"
    except ValueError:
        return str(value)


def first_nonempty(*values: Any) -> str:
    for value in values:
        if value not in (None, ""):
            return str(value)
    return ""


def attachments(row: dict[str, Any]) -> list[dict[str, str]]:
    docs: list[dict[str, str]] = []
    for idx in range(1, 11):
        url = row.get(f"ntceSpecDocUrl{idx}")
        name = row.get(f"ntceSpecFileNm{idx}")
        if url:
            docs.append({"name": str(name or f"attachment-{idx}"), "url": str(url)})
    return docs


def normalize_row(row: dict[str, Any], kind_key: str, kind_label: str) -> dict[str, Any]:
    budget = first_nonempty(row.get("asignBdgtAmt"), row.get("bdgtAmt"), row.get("presmptPrce"))
    task_hint = " / ".join(
        part
        for part in [
            row.get("pubPrcrmntLrgClsfcNm"),
            row.get("pubPrcrmntMidClsfcNm"),
            row.get("pubPrcrmntClsfcNm"),
            row.get("srvceDivNm"),
            row.get("dtilPrdctClsfcNoNm"),
        ]
        if part
    )
    return {
        "kind": kind_key,
        "kind_label": kind_label,
        "notice_no": row.get("bidNtceNo") or "",
        "notice_order": row.get("bidNtceOrd") or "",
        "title": row.get("bidNtceNm") or "",
        "notice_org": row.get("ntceInsttNm") or "",
        "demand_org": row.get("dminsttNm") or "",
        "posted_at": row.get("bidNtceDt") or "",
        "bid_start": row.get("bidBeginDt") or "",
        "bid_close": row.get("bidClseDt") or "",
        "open_at": row.get("opengDt") or "",
        "budget": budget,
        "budget_text": money(budget),
        "estimated_price": money(row.get("presmptPrce")),
        "bid_method": row.get("bidMethdNm") or "",
        "contract_method": row.get("cntrctCnclsMthdNm") or "",
        "award_method": row.get("sucsfbidMthdNm") or "",
        "task_hint": task_hint,
        "detail_url": row.get("bidNtceDtlUrl") or row.get("bidNtceUrl") or "",
        "attachments": attachments(row),
        "raw": row,
    }


def match_query(item: dict[str, Any], query: str) -> bool:
    if not query:
        return True
    q = query.lower()
    haystack = " ".join(
        str(item.get(key) or "")
        for key in ["title", "notice_org", "demand_org", "task_hint", "bid_method", "contract_method"]
    ).lower()
    haystack += " " + " ".join(att["name"].lower() for att in item.get("attachments", []))
    return q in haystack


def search(args: argparse.Namespace) -> dict[str, Any]:
    key = get_service_key(args)
    start, end = resolve_period(args)
    kind_keys = list(OPS) if args.kind == "all" else [args.kind]
    all_results: list[dict[str, Any]] = []
    calls: list[str] = []
    totals: dict[str, Any] = {}

    for kind_key in kind_keys:
        op, label = OPS[kind_key]
        url = build_url(op, key, args.page, args.per_page, start, end)
        calls.append(redact_url(url, key))
        if args.dry_run:
            continue
        payload = request_json(url, timeout=args.timeout)
        response = payload.get("response") or {}
        header = response.get("header") or {}
        if str(header.get("resultCode")) != "00":
            raise G2BError(f"{kind_key} API error: {header}")
        body = response.get("body") or {}
        totals[kind_key] = body.get("totalCount")
        items = body.get("items") or []
        if isinstance(items, dict):
            items = [items]
        for row in items:
            normalized = normalize_row(row, kind_key, label)
            if match_query(normalized, args.query):
                all_results.append(normalized)

    all_results.sort(key=lambda item: item.get("bid_close") or item.get("posted_at") or "")
    if args.limit:
        all_results = all_results[: args.limit]
    return {
        "period": {"from": start, "to": end},
        "kind": args.kind,
        "query": args.query,
        "total_counts": totals,
        "results": all_results,
        "request_urls": calls,
        "dry_run": bool(args.dry_run),
    }


def as_text(result: dict[str, Any]) -> str:
    if result.get("dry_run"):
        return "요청 URL:\\n" + "\\n".join(result["request_urls"])
    lines = [
        f"조회기간: {result['period']['from']} ~ {result['period']['to']}",
        f"검색어: {result['query'] or '-'} / 유형: {result['kind']}",
        f"결과: {len(result['results'])}건",
    ]
    for idx, item in enumerate(result["results"], start=1):
        att = item.get("attachments") or []
        first_att = f"{att[0]['name']} {att[0]['url']}" if att else "-"
        hint = textwrap.shorten(item.get("task_hint") or "-", width=120, placeholder="...")
        lines.extend(
            [
                "",
                f"{idx}. {item.get('title')}",
                f"- 유형: {item.get('kind_label')}",
                f"- 수요기관: {item.get('demand_org') or '-'} / 공고기관: {item.get('notice_org') or '-'}",
                f"- 예산/추정가격: {item.get('budget_text') or item.get('estimated_price') or '-'}",
                f"- 입찰마감: {item.get('bid_close') or '-'} / 개찰: {item.get('open_at') or '-'}",
                f"- 계약/낙찰: {item.get('contract_method') or '-'} / {item.get('award_method') or '-'}",
                f"- 과업 힌트: {hint}",
                f"- 상세: {item.get('detail_url') or '-'}",
                f"- 첨부: {first_att}",
            ]
        )
    return "\\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search Korean G2B bid notices")
    parser.add_argument("--timeout", type=int, default=30)
    sub = parser.add_subparsers(dest="command", required=True)

    search_parser = sub.add_parser("search", help="search bid notices")
    search_parser.add_argument("--query", default="", help="keyword filter applied to returned notice fields")
    search_parser.add_argument("--kind", choices=["service", "goods", "construction", "all"], default="service")
    search_parser.add_argument("--days", type=int, default=7)
    search_parser.add_argument("--from-date", help="YYYY-MM-DD")
    search_parser.add_argument("--to-date", help="YYYY-MM-DD")
    search_parser.add_argument("--page", type=int, default=1)
    search_parser.add_argument("--per-page", type=int, default=100)
    search_parser.add_argument("--limit", type=int, default=10)
    search_parser.add_argument("--service-key", help="override service key; prefer NARAJANGTEO_SERVICE_KEY env")
    search_parser.add_argument("--dry-run", action="store_true")
    search_parser.add_argument("--text", action="store_true")
    search_parser.add_argument("--json", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = search(args)
    except G2BError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if args.text:
        print(as_text(result))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
