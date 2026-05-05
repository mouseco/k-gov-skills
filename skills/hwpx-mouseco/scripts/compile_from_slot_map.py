from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any

from create_hwpx_report import build, heading_key, load_report, report_meta, validate_report_data


class SlotMapError(ValueError):
    """Raised when a slot map is not safe enough to drive compilation."""


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SlotMapError(f"{path} must contain a JSON object")
    return data


def _resolve_path(value: str, base_dir: Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    candidate = (base_dir / path).resolve()
    if candidate.exists():
        return candidate
    return path.resolve()


def _content_value_for_slot(slot: dict[str, Any], report: dict[str, Any]) -> str | None:
    slot_type = slot.get("slot_type")
    key = str(slot.get("content_key") or "").strip()

    # Direct dot-path lookup lets a reviewed slot map target precise report fields
    # without adding template-specific code to the compiler.
    if key:
        current: Any = report
        found = True
        for part in key.split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                found = False
                break
        if found and isinstance(current, (str, int, float)):
            return str(current)

    # Conservative semantic defaults for slot maps produced from inspect output.
    if slot_type == "title":
        return str(report.get("title", "")) or None
    if slot_type in {"summary", "subtitle"}:
        return str(report.get("summary", "")) or None
    if slot_type == "authoring" and "authoring" in report:
        return report_meta(report)
    return None


def _build_replacements_from_slots(slot_map: dict[str, Any], report: dict[str, Any]) -> dict[str, str]:
    replacements: dict[str, str] = {}
    for slot in slot_map.get("slots", []):
        if slot.get("slot_type") not in {"title", "subtitle", "summary", "authoring", "replacement"}:
            continue
        placement = slot.get("placement") or {}
        if placement.get("mode") not in {None, "replace"}:
            continue
        anchor = slot.get("anchor") or {}
        old_text = str(anchor.get("text") or "").strip()
        if not old_text:
            continue
        new_text = _content_value_for_slot(slot, report)
        if new_text is None or not str(new_text).strip():
            continue
        replacements[old_text] = str(new_text)
    return replacements


def _norm_headers(headers: list[Any]) -> list[str]:
    return [re.sub(r"\s+", "", str(value)).strip() for value in headers]


def _table_matches_slot(table: dict[str, Any], slot: dict[str, Any]) -> bool:
    table_headers = _norm_headers(table.get("headers") or [])
    anchor = slot.get("anchor") or {}
    slot_headers = _norm_headers(anchor.get("headers") or [])
    if slot_headers and table_headers == slot_headers:
        return True
    content_key = str(slot.get("content_key") or slot.get("slot_id") or "").strip()
    return bool(content_key and str(table.get("slot") or table.get("slot_id") or table.get("content_key") or "") == content_key)


def _apply_table_slots(slot_map: dict[str, Any], report: dict[str, Any]) -> None:
    tables = report.get("tables")
    if not isinstance(tables, list) or not tables:
        return

    item_headings = {heading_key(str(item.get("heading", ""))) for item in report.get("items", []) if isinstance(item, dict)}
    table_slots = [slot for slot in slot_map.get("slots", []) if slot.get("slot_type") == "table"]
    for slot in table_slots:
        placement = slot.get("placement") or {}
        if placement.get("mode") != "clone_and_fill":
            continue
        after_heading = str(placement.get("after_heading") or "").strip()
        if after_heading and heading_key(after_heading) not in item_headings:
            raise SlotMapError(
                f"slot {slot.get('slot_id')} placement.after_heading does not match report items: {after_heading!r}"
            )
        for table in tables:
            if isinstance(table, dict) and _table_matches_slot(table, slot):
                if after_heading and not table.get("after_heading"):
                    table["after_heading"] = after_heading
                if slot.get("slot_id") and not table.get("slot_id"):
                    table["slot_id"] = slot.get("slot_id")
                break


def _validate_slot_map(slot_map: dict[str, Any], allow_draft: bool) -> None:
    if slot_map.get("version") != "0.1":
        raise SlotMapError("slot_map.version must be '0.1'")
    if not isinstance(slot_map.get("template"), dict) or not slot_map["template"].get("file"):
        raise SlotMapError("slot_map.template.file is required")
    if not isinstance(slot_map.get("slots"), list):
        raise SlotMapError("slot_map.slots must be a list")
    if slot_map.get("status") != "reviewed" and not allow_draft:
        raise SlotMapError("slot map must be status='reviewed' unless --allow-draft is used")
    pending = [slot.get("slot_id") for slot in slot_map.get("slots", []) if slot.get("requires_review")]
    if pending and not allow_draft:
        preview = ", ".join(str(value) for value in pending[:8])
        suffix = "..." if len(pending) > 8 else ""
        raise SlotMapError(f"slot map still has requires_review=true slots: {preview}{suffix}")


def adapt_report_with_slot_map(report: dict[str, Any], slot_map: dict[str, Any], allow_draft: bool = False) -> dict[str, Any]:
    """Return report JSON enriched by a reviewed slot map.

    The slot map supplies template-level anchors and placement policy; the report
    supplies actual content. This keeps the compiler generic: no sample filename,
    paragraph ID, or phrase is hardcoded here.
    """
    _validate_slot_map(slot_map, allow_draft=allow_draft)
    adapted = copy.deepcopy(report)

    replacements = _build_replacements_from_slots(slot_map, adapted)
    if replacements:
        existing = adapted.get("text_replacements")
        if existing is None:
            adapted["text_replacements"] = {}
        elif not isinstance(existing, dict):
            raise SlotMapError("report.text_replacements must be an object when present")
        # Explicit report replacements win over slot defaults.
        adapted["text_replacements"] = {**replacements, **adapted["text_replacements"]}

    _apply_table_slots(slot_map, adapted)
    validate_report_data(adapted)
    return adapted


def compile_from_slot_map(input_path: Path, slot_map_path: Path, output_path: Path, template: Path | None = None, allow_draft: bool = False) -> Path:
    report = load_report(input_path)
    slot_map = _load_json(slot_map_path)
    adapted = adapt_report_with_slot_map(report, slot_map, allow_draft=allow_draft)
    template_path = template or _resolve_path(str(slot_map["template"]["file"]), slot_map_path.parent)
    if not template_path.exists():
        raise SlotMapError(f"template not found: {template_path}")
    return build(adapted, output_path, template_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compile an HWPX report using a reviewed slot map and structured report JSON.")
    parser.add_argument("--input", type=Path, required=True, help="UTF-8 report JSON")
    parser.add_argument("--slot-map", type=Path, required=True, help="reviewed slot_map.json")
    parser.add_argument("--output", type=Path, required=True, help="output .hwpx")
    parser.add_argument("--template", type=Path, help="override template .hwpx path")
    parser.add_argument("--allow-draft", action="store_true", help="allow draft slot maps for local experiments only")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        print(compile_from_slot_map(args.input, args.slot_map, args.output, args.template, allow_draft=args.allow_draft))
    except SlotMapError as exc:
        print(f"slot map error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
