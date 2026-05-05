from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from inspect_hwpx import inspect_hwpx


def slug(value: str, fallback: str) -> str:
    text = re.sub(r"[^0-9a-zA-Z가-힣]+", "_", value).strip("_").lower()
    # Keep IDs schema-safe and stable even when the source text is Korean.
    ascii_text = re.sub(r"[^0-9a-z_]+", "", text)
    return ascii_text or fallback


def clean(value: str) -> str:
    return " ".join(str(value).split())


def is_metadata_or_toc_text(text: str) -> bool:
    normalized = re.sub(r"\s+", "", text)
    if not normalized:
        return True
    if normalized in {"보도자료", "참고자료", "설명자료", "목차", "부서(부)", "담당", "연락처"}:
        return True
    if normalized in {"전략실", "전략부"}:
        return True
    if normalized in {"(전략부)", "(전략실)"}:
        return True
    if any(label in normalized for label in ["담당자A", "담당자B", "작성자A", "작성자B"]):
        return True
    if len(normalized) <= 12 and any(title in normalized for title in ["팀장", "과장", "차장", "부장", "담당자"]):
        return True
    if re.fullmatch(r"\(?\d{2,4}\)?[-)]?\d{3,4}-\d{4}", normalized):
        return True
    if "목차" in normalized:
        return True
    if "부서" in normalized and "담당" in normalized and "연락처" in normalized:
        return True
    return False


def load_structure(path: Path) -> dict[str, Any]:
    if path.suffix.lower() == ".hwpx":
        return inspect_hwpx(path, paragraph_limit=None)
    return json.loads(path.read_text(encoding="utf-8"))


def iter_paragraphs(structure: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    rows: list[tuple[str, dict[str, Any]]] = []
    for section in structure.get("sections", []):
        section_name = str(section.get("name", ""))
        for row in section.get("sample_paragraphs", []):
            rows.append((section_name, row))
    return rows


def iter_tables(structure: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    rows: list[tuple[str, dict[str, Any]]] = []
    for section in structure.get("sections", []):
        section_name = str(section.get("name", ""))
        for table in section.get("sample_tables", []):
            rows.append((section_name, table))
    return rows


def add_slot(slots: list[dict[str, Any]], slot: dict[str, Any]) -> None:
    existing = {item["slot_id"] for item in slots}
    base = slot["slot_id"]
    candidate = base
    index = 2
    while candidate in existing:
        candidate = f"{base}_{index}"
        index += 1
    slot["slot_id"] = candidate
    slots.append(slot)


def paragraph_slot(slot_id: str, slot_type: str, section: str, row: dict[str, Any], role: str, confidence: float, notes: str) -> dict[str, Any]:
    text = clean(row.get("text") or row.get("text_preview") or "")
    return {
        "slot_id": slot_id,
        "slot_type": slot_type,
        "role": role,
        "section": section,
        "anchor": {"kind": "paragraph", "paragraph_index": int(row.get("index", 0)), "text": text[:160]},
        "prototype": {"paraPrIDRef": row.get("paraPrIDRef"), "styleIDRef": row.get("styleIDRef")},
        "content_key": slot_id,
        "placement": {"mode": "replace"},
        "confidence": confidence,
        "requires_review": True,
        "notes": notes,
    }


def table_slot(section: str, table: dict[str, Any]) -> dict[str, Any]:
    headers = [clean(value) for value in table.get("header_like", []) if clean(value)]
    table_index = int(table.get("index", 0))
    slot_id = f"table_{table_index:02d}"
    text_preview = clean(table.get("text_preview", ""))
    compact_headers = {re.sub(r"\s+", "", value) for value in headers}
    compact_text = re.sub(r"\s+", "", text_preview)
    role = "표 prototype 후보"
    confidence = 0.72 if headers else 0.45
    notes = "headers가 실제 데이터 헤더인지, 장식/메타 표인지 사람 검수 필요"
    if {"구분", "일정", "내용"} <= compact_headers:
        role = "데이터 표 prototype 후보"
        confidence = 0.88
        notes = "행 복제·셀 치환 대상 가능성이 높음. placement.after_heading 지정 권장"
    elif {"담당", "연락처"} & compact_headers or ("담당" in compact_text and "연락처" in compact_text):
        role = "작성자/연락처 메타 표 후보"
        confidence = 0.76
        notes = "본문 데이터 표가 아니라 authoring/contact 치환 슬롯인지 검수 필요"
    elif "목차" in compact_text:
        role = "목차 표 후보"
        confidence = 0.7
        notes = "본문 생성 시 보존/삭제/재생성 정책 검수 필요"
    elif re.match(r"^[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]", compact_text):
        role = "장 제목 컨테이너 후보"
        confidence = 0.82
        notes = "장 번호와 제목이 분리된 컨테이너일 수 있으므로 일반 문단으로 풀지 말 것"
    return {
        "slot_id": slot_id,
        "slot_type": "table",
        "role": role,
        "section": section,
        "anchor": {"kind": "table", "table_index": table_index, "headers": headers, "text": text_preview[:180]},
        "prototype": {"row_count": int(table.get("row_count", 0)), "col_count": int(table.get("col_count", 0))},
        "content_key": slot_id,
        "placement": {"mode": "clone_and_fill"},
        "confidence": confidence,
        "requires_review": True,
        "notes": notes,
    }


def build_slot_map(structure: dict[str, Any], source: Path) -> dict[str, Any]:
    slots: list[dict[str, Any]] = []
    paragraphs = iter_paragraphs(structure)
    non_empty = [(section, row) for section, row in paragraphs if clean(row.get("text") or row.get("text_preview") or "")]

    # Title candidates: skip boilerplate labels such as 보도자료 and prefer early concise text.
    for section, row in non_empty[:40]:
        text = clean(row.get("text") or row.get("text_preview") or "")
        if is_metadata_or_toc_text(text):
            continue
        if 6 <= len(text) <= 80 and row.get("kind") in {"short_title_candidate", "body"}:
            add_slot(slots, paragraph_slot("title_main", "title", section, row, "대표 제목 후보", 0.78, "초기 영역의 짧은 핵심 문구를 제목 후보로 추정"))
            break

    # Subtitle/summary bullets immediately after title area.
    for section, row in non_empty[:80]:
        text = clean(row.get("text") or row.get("text_preview") or "")
        if row.get("kind") == "bullet" and 8 <= len(text) <= 140:
            add_slot(slots, paragraph_slot(f"subtitle_bullet_{row.get('index')}", "subtitle", section, row, "제목 하단 요약 bullet 후보", 0.68, "제목 하단 핵심 문장 또는 보도자료 부제 가능성"))

    # Body start: first substantial body paragraph after the title block.
    for section, row in non_empty:
        text = clean(row.get("text") or row.get("text_preview") or "")
        if row.get("kind") == "body" and len(text) >= 90 and not is_metadata_or_toc_text(text):
            add_slot(slots, paragraph_slot("body_start", "body_start", section, row, "본문 시작 후보", 0.74, "장문 본문이 시작되는 위치로 추정"))
            break

    # Heading candidates deeper in the body.
    heading_count = 0
    for section, row in non_empty:
        idx = int(row.get("index", 0))
        text = clean(row.get("text") or row.get("text_preview") or "")
        if is_metadata_or_toc_text(text):
            continue
        if idx < 15:
            continue
        if row.get("kind") in {"short_title_candidate", "number_heading", "korean_letter_heading", "roman_heading"} and 3 <= len(text) <= 70:
            heading_count += 1
            add_slot(slots, paragraph_slot(f"heading_{heading_count:02d}", "heading", section, row, "본문 소제목 후보", 0.56, "반복 구조인지, 표 안 셀 텍스트인지 검수 필요"))
            if heading_count >= 20:
                break

    for section, table in iter_tables(structure):
        add_slot(slots, table_slot(section, table))

    table_total = sum(int(section.get("table_count", 0)) for section in structure.get("sections", []))
    return {
        "version": "0.1",
        "status": "draft",
        "template": {
            "file": str(structure.get("file") or source),
            "source_structure": str(source),
            "sections": len(structure.get("sections", [])),
            "tables": table_total,
        },
        "slots": slots,
        "warnings": [
            "자동 생성 slot map은 초안이다. compile 전에 title/body/table/replacement 슬롯을 사람 검수해야 한다.",
            "표는 장식/메타 표와 데이터 표를 구분해야 하며, 필요한 경우 placement.after_heading을 직접 지정한다.",
        ],
        "notes": "inspect_hwpx.py 결과를 기반으로 한 슬롯 후보. reviewed 상태로 바꾸기 전에는 공식 템플릿으로 간주하지 않는다.",
    }


def write_markdown(slot_map: dict[str, Any], path: Path) -> None:
    lines = [
        "# HWPX Slot Map Draft",
        "",
        f"- Template: `{slot_map['template']['file']}`",
        f"- Status: `{slot_map['status']}`",
        f"- Slots: {len(slot_map['slots'])}",
        "",
        "## Slots",
        "",
        "| slot_id | type | role | anchor | confidence |",
        "|---|---|---|---|---:|",
    ]
    for slot in slot_map["slots"]:
        anchor = slot.get("anchor", {})
        anchor_text = anchor.get("text") or " / ".join(anchor.get("headers", []) or [])
        lines.append(
            f"| `{slot['slot_id']}` | {slot['slot_type']} | {slot.get('role', '')} | {clean(anchor_text)[:80]} | {slot['confidence']:.2f} |"
        )
    lines += ["", "## Warnings", ""]
    lines.extend(f"- {warning}" for warning in slot_map.get("warnings", []))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a human-review slot map draft from an HWPX or inspect_hwpx structure JSON.")
    parser.add_argument("input", type=Path, help="input .hwpx or template_structure.json")
    parser.add_argument("--out-dir", type=Path, required=True, help="output directory")
    args = parser.parse_args()

    structure = load_structure(args.input)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    slot_map = build_slot_map(structure, args.input)
    json_path = args.out_dir / "slot_map_draft.json"
    md_path = args.out_dir / "slot_map_draft.md"
    json_path.write_text(json.dumps(slot_map, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(slot_map, md_path)
    print(json.dumps({"slot_map": str(json_path), "summary": str(md_path), "slots": len(slot_map["slots"])}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
