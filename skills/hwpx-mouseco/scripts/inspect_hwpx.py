from __future__ import annotations

import argparse
import json
import re
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

from lxml import etree

NS = {
    "hp": "http://www.hancom.co.kr/hwpml/2011/paragraph",
    "hh": "http://www.hancom.co.kr/hwpml/2011/head",
    "opf": "http://www.idpf.org/2007/opf",
}


def local_name(element: etree._Element) -> str:
    return etree.QName(element).localname


def read_xml(zf: zipfile.ZipFile, name: str) -> etree._Element | None:
    try:
        return etree.fromstring(zf.read(name))
    except Exception:
        return None


def text_of(element: etree._Element) -> str:
    values: list[str] = []
    for node in element.iter():
        if local_name(node) == "t" and node.text:
            values.append(node.text)
    return "".join(values)


def classify_paragraph(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        return "empty"
    if re.match(r"^[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+[.．]?\s*", stripped):
        return "roman_heading"
    if re.match(r"^\d+[.．]\s*", stripped):
        return "number_heading"
    if re.match(r"^[가-힣]\.\s*", stripped):
        return "korean_letter_heading"
    if re.match(r"^[□■○ㅇ●◇◆※\-ㆍ․]\s*", stripped):
        return "bullet"
    if len(stripped) <= 45 and not stripped.endswith(("다", "음", "함", "임", "요")):
        return "short_title_candidate"
    return "body"


def paragraph_info(section_root: etree._Element, limit: int | None = None) -> list[dict[str, Any]]:
    paragraphs = [node for node in section_root.iter() if local_name(node) == "p"]
    rows: list[dict[str, Any]] = []
    for index, p in enumerate(paragraphs):
        text = text_of(p)
        run_count = sum(1 for node in p.iter() if local_name(node) == "run")
        row = {
            "index": index,
            "text": text,
            "text_preview": text[:120],
            "chars": len(text),
            "kind": classify_paragraph(text),
            "run_count": run_count,
            "paraPrIDRef": p.get("paraPrIDRef"),
            "styleIDRef": p.get("styleIDRef"),
        }
        rows.append(row)
        if limit is not None and len(rows) >= limit:
            break
    return rows


def table_count(section_root: etree._Element) -> int:
    return sum(1 for node in section_root.iter() if local_name(node) == "tbl")


def table_info(section_root: etree._Element, limit: int | None = None) -> list[dict[str, Any]]:
    tables = [node for node in section_root.iter() if local_name(node) == "tbl"]
    rows: list[dict[str, Any]] = []
    for index, tbl in enumerate(tables):
        tr_nodes = [node for node in tbl if local_name(node) == "tr"]
        row_values: list[list[str]] = []
        for tr in tr_nodes[:5]:
            cells = [" ".join(text_of(tc).split()) for tc in tr if local_name(tc) == "tc"]
            row_values.append(cells)
        non_empty_rows = [row for row in row_values if any(cell.strip() for cell in row)]
        header_like = non_empty_rows[0] if non_empty_rows else []
        rows.append(
            {
                "index": index,
                "row_count": len(tr_nodes),
                "col_count": max((len(row) for row in row_values), default=0),
                "header_like": header_like,
                "sample_rows": row_values,
                "text_preview": " ".join(text_of(tbl).split())[:240],
            }
        )
        if limit is not None and len(rows) >= limit:
            break
    return rows


def detect_placeholders(text: str) -> list[str]:
    candidates = set()
    patterns = [
        r"\{\{[^{}]{1,80}\}\}",
        r"\[[^\[\]]{1,80}\]",
        r"<[^<>]{1,80}>",
        r"○○+|OO+|XX+|□□+",
        r"(입력|작성|기재|수정)\s*(필요|요망|예정|란)",
    ]
    for pattern in patterns:
        for match in re.findall(pattern, text):
            if isinstance(match, tuple):
                match = " ".join(match)
            candidates.add(str(match))
    return sorted(candidates)


def inspect_hwpx(path: Path, paragraph_limit: int | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "file": str(path),
        "exists": path.exists(),
        "package": {},
        "sections": [],
        "text": {},
        "qa": {"errors": [], "warnings": []},
    }
    if not path.exists():
        result["qa"]["errors"].append("file does not exist")
        return result

    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        result["package"] = {
            "entry_count": len(names),
            "first_entry": names[0] if names else None,
            "has_mimetype": "mimetype" in names,
            "mimetype_first": bool(names and names[0] == "mimetype"),
            "has_header": "Contents/header.xml" in names,
            "has_content_hpf": "Contents/content.hpf" in names,
            "has_preview_text": "Preview/PrvText.txt" in names,
            "bindata_count": sum(1 for n in names if n.startswith("BinData/")),
            "preview_count": sum(1 for n in names if n.startswith("Preview/")),
        }
        if names and names[0] != "mimetype":
            result["qa"]["warnings"].append("mimetype is not the first ZIP entry")

        section_names = sorted(
            [n for n in names if re.fullmatch(r"Contents/section\d+\.xml", n)],
            key=lambda n: int(re.search(r"section(\d+)\.xml", n).group(1)),
        )
        full_text_parts: list[str] = []
        kind_counter: Counter[str] = Counter()
        for section_name in section_names:
            root = read_xml(zf, section_name)
            if root is None:
                result["qa"]["errors"].append(f"malformed or unreadable {section_name}")
                continue
            paragraphs = paragraph_info(root, limit=paragraph_limit)
            section_text = "\n".join(row["text"] for row in paragraph_info(root, limit=None) if row["text"].strip())
            for row in paragraph_info(root, limit=None):
                kind_counter[row["kind"]] += 1
            full_text_parts.append(section_text)
            result["sections"].append(
                {
                    "name": section_name,
                    "paragraph_count": sum(1 for node in root.iter() if local_name(node) == "p"),
                    "table_count": table_count(root),
                    "sample_tables": table_info(root, limit=30),
                    "sample_paragraphs": paragraphs,
                }
            )

        full_text = "\n".join(part for part in full_text_parts if part)
        preview_text = ""
        if "Preview/PrvText.txt" in names:
            try:
                preview_text = zf.read("Preview/PrvText.txt").decode("utf-8", errors="replace")
            except Exception as exc:
                result["qa"]["warnings"].append(f"Preview/PrvText.txt unreadable: {exc}")
        result["text"] = {
            "char_count": len(full_text),
            "paragraph_kind_counts": dict(kind_counter),
            "first_1000_chars": full_text[:1000],
            "placeholder_candidates": detect_placeholders(full_text),
            "preview_char_count": len(preview_text),
            "preview_synced_roughly": bool(preview_text.strip() and full_text.strip()[:80] in preview_text),
        }
        if "Preview/PrvText.txt" in names and full_text.strip() and not result["text"]["preview_synced_roughly"]:
            result["qa"]["warnings"].append("Preview/PrvText.txt may not match section text")

        content_root = read_xml(zf, "Contents/content.hpf") if "Contents/content.hpf" in names else None
        if content_root is not None:
            manifest_hrefs = []
            for element in content_root.iter():
                href = element.get("href")
                if href:
                    manifest_hrefs.append(href)
            missing = []
            for href in manifest_hrefs:
                normalized = href.lstrip("/")
                if normalized not in names and f"Contents/{normalized}" not in names:
                    missing.append(href)
            result["package"]["manifest_href_count"] = len(manifest_hrefs)
            result["package"]["manifest_missing_entries"] = missing[:50]
            if missing:
                result["qa"]["warnings"].append(f"manifest href missing entries: {len(missing)}")

    return result


def write_reports(result: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    structure_path = out_dir / "template_structure.json"
    inspection_path = out_dir / "template_inspection.md"
    structure_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# HWPX Template Inspection",
        "",
        f"- File: `{result.get('file')}`",
        f"- Entries: {result.get('package', {}).get('entry_count')}",
        f"- First entry: `{result.get('package', {}).get('first_entry')}`",
        f"- Sections: {len(result.get('sections', []))}",
        f"- Text chars: {result.get('text', {}).get('char_count')}",
        f"- Tables: {sum(s.get('table_count', 0) for s in result.get('sections', []))}",
        "",
        "## QA",
    ]
    errors = result.get("qa", {}).get("errors", [])
    warnings = result.get("qa", {}).get("warnings", [])
    lines.append(f"- Errors: {len(errors)}")
    lines.extend(f"  - {e}" for e in errors)
    lines.append(f"- Warnings: {len(warnings)}")
    lines.extend(f"  - {w}" for w in warnings)
    lines += ["", "## Paragraph kinds", ""]
    for key, value in result.get("text", {}).get("paragraph_kind_counts", {}).items():
        lines.append(f"- {key}: {value}")
    lines += ["", "## Section samples", ""]
    for section in result.get("sections", []):
        lines.append(f"### {section.get('name')}")
        lines.append(f"- Paragraphs: {section.get('paragraph_count')}")
        lines.append(f"- Tables: {section.get('table_count')}")
        for table in section.get("sample_tables", [])[:10]:
            headers = " | ".join(table.get("header_like", []))
            preview = table.get("text_preview", "").replace("`", "'")
            lines.append(f"- Table `{table.get('index')}` rows={table.get('row_count')} cols={table.get('col_count')} headers=`{headers}` preview={preview[:120]}")
        for row in section.get("sample_paragraphs", [])[:30]:
            text = row.get("text_preview", "").replace("`", "'")
            if text.strip():
                lines.append(f"- `{row.get('index')}` [{row.get('kind')}] {text}")
        lines.append("")
    inspection_path.write_text("\n".join(lines), encoding="utf-8")
    return structure_path, inspection_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect an HWPX template and emit structure reports.")
    parser.add_argument("input", help="input .hwpx path")
    parser.add_argument("--out-dir", help="directory for template_structure.json and template_inspection.md")
    parser.add_argument("--paragraph-limit", type=int, default=80, help="sample paragraphs per section")
    args = parser.parse_args()

    input_path = Path(args.input)
    result = inspect_hwpx(input_path, paragraph_limit=args.paragraph_limit)
    out_dir = Path(args.out_dir) if args.out_dir else Path.cwd() / f"{input_path.stem}_inspection"
    structure_path, inspection_path = write_reports(result, out_dir)
    print(json.dumps({"structure": str(structure_path), "inspection": str(inspection_path), "errors": result["qa"]["errors"], "warnings": result["qa"]["warnings"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
