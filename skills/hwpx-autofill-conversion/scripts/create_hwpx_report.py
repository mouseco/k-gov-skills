from __future__ import annotations

import argparse
import html
import json
import re
import zipfile
from pathlib import Path
from typing import Any

from lxml import etree


SKILL_DIR = Path(__file__).resolve().parents[1]


def extract_paragraph_blocks(xml: str) -> list[str]:
    return re.findall(r"<hp:p\b.*?</hp:p>", xml, flags=re.DOTALL)


def block_text(block: str) -> str:
    texts = re.findall(r"<hp:t>(.*?)</hp:t>", block, flags=re.DOTALL)
    return "".join(re.sub(r"<[^>]+>", "", t) for t in texts)


def replace_text_in_block(block: str, text: str) -> str:
    escaped = html.escape(text, quote=False)
    done = False

    def repl(_: re.Match[str]) -> str:
        nonlocal done
        if done:
            return "<hp:t></hp:t>"
        done = True
        return f"<hp:t>{escaped}</hp:t>"

    return re.sub(r"<hp:t>.*?</hp:t>", repl, block, flags=re.DOTALL)


def split_bold_segments(text: str) -> list[tuple[str, bool]]:
    segments: list[tuple[str, bool]] = []
    pos = 0
    for match in re.finditer(r"\*\*(.+?)\*\*", text):
        if match.start() > pos:
            segments.append((text[pos : match.start()], False))
        segments.append((match.group(1), True))
        pos = match.end()
    if pos < len(text):
        segments.append((text[pos:], False))
    return [(value, bold) for value, bold in segments if value]


def remove_bold_markers(text: str) -> str:
    return re.sub(r"\*\*(.+?)\*\*", r"\1", text)


def normalize_text(text: str) -> str:
    text = remove_bold_markers(text) if "**" in text else text
    # Korean bullet-style report endings usually omit a final full stop.
    return re.sub(r"(?<=[가-힣])\.$", "", text)


def replace_text_in_block_with_runs(block: str, text: str, header: str, bold_charpr_id_for: dict[str, str]) -> tuple[str, str]:
    text = re.sub(r"(?<=[가-힣])\.$", "", text)
    segments = split_bold_segments(text)
    if not any(bold for _, bold in segments):
        return replace_text_in_block(block, text), header

    run_matches = list(re.finditer(r"<hp:run\b[^>]*>.*?</hp:run>", block, flags=re.DOTALL))
    if not run_matches:
        return replace_text_in_block(block, text.replace("**", "")), header

    run_template = run_matches[0].group(0)
    base_charpr_id = first_run_charpr_id(run_template)
    if not base_charpr_id:
        return replace_text_in_block(block, text.replace("**", "")), header

    header, bold_charpr_id = ensure_bold_charpr(header, base_charpr_id, bold_charpr_id_for)
    new_runs = []
    for value, is_bold in segments:
        run = re.sub(r"<hp:t>.*?</hp:t>", f"<hp:t>{html.escape(value, quote=False)}</hp:t>", run_template, flags=re.DOTALL)
        if is_bold:
            run = re.sub(r'charPrIDRef="\d+"', f'charPrIDRef="{bold_charpr_id}"', run, count=1)
        new_runs.append(run)

    runs_start = run_matches[0].start()
    runs_end = run_matches[-1].end()
    return block[:runs_start] + "".join(new_runs) + block[runs_end:], header


def renumber_block(block: str, next_id: int) -> tuple[str, int]:
    def repl(match: re.Match[str]) -> str:
        nonlocal next_id
        value = str(next_id)
        next_id += 1
        return f'{match.group(1)}="{value}"'

    return re.sub(r'\b(id|instid|textFlowId)="\d+"', repl, block), next_id


def _para_pr_with_hanging(base: str, new_id: int, hanging_pt: float) -> str:
    text = re.sub(r'(\s)id="\d+"', rf'\1id="{new_id}"', base, count=1)
    margin_index = 0

    def replace_margin(match: re.Match[str]) -> str:
        nonlocal margin_index
        unit = 100 if margin_index == 0 else 200
        intent = -round(hanging_pt * unit)
        margin_index += 1
        margin = match.group(0)
        return re.sub(r'<hc:intent value="[^"]+"', f'<hc:intent value="{intent}"', margin)

    return re.sub(r"<hh:margin>.*?</hh:margin>", replace_margin, text, flags=re.DOTALL)


def ensure_bold_charpr(header: str, base_id: str, cache: dict[str, str]) -> tuple[str, str]:
    if base_id in cache:
        return header, cache[base_id]

    base_match = re.search(r'<hh:charPr\b(?=[^>]*\sid="' + re.escape(base_id) + r'")[^>]*>.*?</hh:charPr>', header, re.DOTALL)
    if not base_match:
        cache[base_id] = base_id
        return header, base_id
    base = base_match.group(0)
    if "<hh:bold" in base:
        cache[base_id] = base_id
        return header, base_id

    max_char_id = max(int(x) for x in re.findall(r'<hh:charPr\b(?=[^>]*\sid="(\d+)")', header))
    new_id = str(max_char_id + 1)
    bold = re.sub(r'(\s)id="\d+"', rf'\1id="{new_id}"', base, count=1)
    if "<hh:underline" in bold:
        bold = bold.replace("<hh:underline", "<hh:bold/><hh:underline", 1)
    else:
        bold = bold.replace("</hh:charPr>", "<hh:bold/></hh:charPr>", 1)
    header = re.sub(
        r'<hh:charProperties itemCnt="(\d+)">',
        lambda m: f'<hh:charProperties itemCnt="{int(m.group(1)) + 1}">',
        header,
        count=1,
    )
    header = header.replace("</hh:charProperties>", bold + "</hh:charProperties>", 1)
    cache[base_id] = new_id
    return header, new_id


def bullet_prefix(text: str) -> str | None:
    for pattern in [
        r"^(\s*□\s+)",
        r"^(\s*ㅇ\s+)",
        r"^(\s*-\s+)",
        r"^(\s*[ㆍ․]\s+)",
        r"^(\s*※\s+)",
    ]:
        match = re.match(pattern, text)
        if match:
            return match.group(1)
    return None


def first_run_charpr_id(block: str) -> str | None:
    match = re.search(r'<hp:run\b[^>]*charPrIDRef="(\d+)"', block)
    return match.group(1) if match else None


def charpr_height_pt(header: str, charpr_id: str | None) -> float:
    if not charpr_id:
        return 15.0
    match = re.search(
        r'<hh:charPr\b(?=[^>]*\sid="' + re.escape(charpr_id) + r'")[^>]*\bheight="(\d+)"',
        header,
    )
    return int(match.group(1)) / 100.0 if match else 15.0


def prefix_width_pt(prefix: str, font_pt: float) -> float:
    total = 0.0
    for ch in prefix:
        if ch == " ":
            total += font_pt * 0.53
        elif ord(ch) < 128:
            total += font_pt * 0.45
        else:
            total += font_pt
    return total


def strip_layout_cache(xml: str) -> str:
    return re.sub(r"<[^<>\s/]*:?lineSegArray\b.*?</[^<>\s/]*:?lineSegArray>", "", xml, flags=re.DOTALL | re.IGNORECASE)


def _xml_root(zf: zipfile.ZipFile, name: str, errors: list[str]) -> etree._Element | None:
    try:
        return etree.fromstring(zf.read(name))
    except KeyError:
        errors.append(f"missing {name}")
    except etree.XMLSyntaxError as exc:
        errors.append(f"malformed {name}: {exc}")
    return None


def _local_name(element: etree._Element) -> str:
    return etree.QName(element).localname


def _declared_ids(root: etree._Element | None, local_name: str) -> set[str]:
    if root is None:
        return set()
    return {
        str(element.get("id"))
        for element in root.iter()
        if _local_name(element) == local_name and element.get("id") not in {None, ""}
    }


def _referenced_values(root: etree._Element | None, attr: str) -> set[str]:
    if root is None:
        return set()
    return {
        str(element.get(attr))
        for element in root.iter()
        if element.get(attr) not in {None, ""}
    }


def _paragraph_text(element: etree._Element) -> str:
    return "".join(element.xpath('.//*[local-name()="t"]/text()'))


def _bold_charpr_ids(root: etree._Element | None) -> set[str]:
    if root is None:
        return set()
    return {
        str(element.get("id"))
        for element in root.iter()
        if _local_name(element) == "charPr"
        and element.get("id") not in {None, ""}
        and any(_local_name(child) == "bold" for child in element.iter())
    }


def _paragraph_runs(element: etree._Element) -> list[tuple[str, str | None]]:
    runs: list[tuple[str, str | None]] = []
    for run in element.xpath('.//*[local-name()="run"]'):
        text = "".join(run.xpath('.//*[local-name()="t"]/text()'))
        runs.append((text, run.get("charPrIDRef")))
    return runs


def _text_range_is_bold(runs: list[tuple[str, str | None]], start: int, end: int, bold_ids: set[str]) -> bool:
    if not runs or not bold_ids:
        return False
    cursor = 0
    touched = False
    for value, charpr_id in runs:
        next_cursor = cursor + len(value)
        overlap_start = max(start, cursor)
        overlap_end = min(end, next_cursor)
        if overlap_start < overlap_end:
            fragment = value[overlap_start - cursor : overlap_end - cursor]
            if fragment.strip():
                touched = True
                if charpr_id not in bold_ids:
                    return False
        cursor = next_cursor
    return touched


def validate_hwpx(path: Path, template: Path | None = None) -> list[str]:
    errors: list[str] = []
    with zipfile.ZipFile(path, "r") as zf:
        names = zf.namelist()
        for required in ["mimetype", "Contents/content.hpf", "Contents/header.xml", "Contents/section0.xml"]:
            if required not in names:
                errors.append(f"missing {required}")
        if names and names[0] != "mimetype":
            errors.append("mimetype is not first ZIP entry")
        if "mimetype" in names and zf.read("mimetype").decode("utf-8").strip() != "application/hwp+zip":
            errors.append("invalid mimetype")
        if "mimetype" in names and zf.getinfo("mimetype").compress_type != zipfile.ZIP_STORED:
            errors.append("mimetype is not stored")
        xml_roots: dict[str, etree._Element] = {}
        for name in names:
            if name.endswith(".xml") or name.endswith(".hpf"):
                root = _xml_root(zf, name, errors)
                if root is not None:
                    xml_roots[name] = root

        content = xml_roots.get("Contents/content.hpf")
        if content is not None:
            manifest_ids: dict[str, str] = {}
            for item in content.xpath('.//*[local-name()="manifest"]/*[local-name()="item"]'):
                item_id = item.get("id")
                href = item.get("href")
                if item_id:
                    manifest_ids[item_id] = href or ""
                if href and not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", href) and href not in names:
                    errors.append(f"manifest href missing from ZIP: {href}")
            for itemref in content.xpath('.//*[local-name()="spine"]/*[local-name()="itemref"]'):
                idref = itemref.get("idref")
                if idref and idref not in manifest_ids:
                    errors.append(f"spine idref not in manifest: {idref}")

        header = xml_roots.get("Contents/header.xml")
        section_names = sorted(name for name in names if re.fullmatch(r"Contents/section\d+\.xml", name))
        bold_charpr_ids = _bold_charpr_ids(header)
        if header is not None:
            sec_cnt = header.get("secCnt")
            if sec_cnt and sec_cnt.isdigit() and int(sec_cnt) != len(section_names):
                errors.append(f"header secCnt={sec_cnt} but found {len(section_names)} section files")
            declared_char = _declared_ids(header, "charPr")
            declared_para = _declared_ids(header, "paraPr")
            declared_style = _declared_ids(header, "style")
            for section_name in section_names:
                section = xml_roots.get(section_name)
                for value in sorted(_referenced_values(section, "charPrIDRef") - declared_char):
                    errors.append(f"{section_name} references missing charPrIDRef={value}")
                for value in sorted(_referenced_values(section, "paraPrIDRef") - declared_para):
                    errors.append(f"{section_name} references missing paraPrIDRef={value}")
                for value in sorted(_referenced_values(section, "styleIDRef") - declared_style):
                    errors.append(f"{section_name} references missing styleIDRef={value}")

        for section_name in section_names:
            section = xml_roots.get(section_name)
            if section is None:
                continue
            if section.xpath('.//*[local-name()="lineSegArray"]'):
                errors.append(f"stale lineSegArray remains in {section_name}")
            for para in section.xpath('.//*[local-name()="p"]'):
                text = html.unescape(_paragraph_text(para))
                if "**" in text:
                    errors.append(f"bold markdown marker remains in {section_name}: {text[:60]}")
                if text.strip() in {"□", "ㅇ", "○", "-", "※"}:
                    errors.append(f"empty bullet paragraph in {section_name}: {text!r}")

    if template is not None:
        with zipfile.ZipFile(template, "r") as template_zf, zipfile.ZipFile(path, "r") as output_zf:
            output_names = set(output_zf.namelist())
            for item in template_zf.infolist():
                name = item.filename
                if (name.startswith("BinData/") or name.startswith("Scripts/") or name.startswith("Preview/")) and name not in output_names:
                    errors.append(f"template asset missing from output: {name}")
    return errors


def load_report(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    validate_report_data(data)
    return data


def _validate_authoring_semantics(data: dict[str, Any], authoring: dict[str, Any]) -> None:
    """Keep the upper-right author/date area reserved for real author metadata.

    This area is not a document-topic slot. Reject obvious subject/title values early
    so generated reports do not place travel/project/report labels in the author line.
    """
    title = str(data.get("title", ""))
    title_tokens = {
        token
        for token in re.split(r"[\s()\[\]{}·,./\\_-]+", title)
        if len(token) >= 3 and not re.fullmatch(r"\d+", token)
    }
    blocked_terms = {
        "보고서",
        "출장보고",
        "출장보고서",
        "여행",
        "여행일지",
        "일지",
        "현장조사",
        "프로젝트",
        "문서",
        "자료",
        "계획안",
    }
    for key in ["department", "team", "name"]:
        value = str(authoring.get(key, "")).strip()
        if not value:
            continue
        if any(term in value for term in blocked_terms):
            raise ValueError(
                f"authoring.{key} must be author metadata only, not document/topic data: {value!r}"
            )
        if any(token and token in value for token in title_tokens):
            raise ValueError(
                f"authoring.{key} appears to contain title/topic text. Use a real department/team/name: {value!r}"
            )


def validate_report_data(data: Any) -> None:
    if not isinstance(data, dict):
        raise ValueError("report JSON root must be an object")
    for key in ["title", "summary_title", "summary", "items"]:
        if key not in data:
            raise ValueError(f"missing required key: {key}")
    if "meta" not in data and "authoring" not in data:
        raise ValueError("missing required key: authoring. Use meta only when preserving a template-specific literal string.")
    if "authoring" in data:
        authoring = data["authoring"]
        if not isinstance(authoring, dict):
            raise ValueError("authoring must be an object")
        for key in ["date", "department", "team"]:
            if not isinstance(authoring.get(key), str) or not authoring[key].strip():
                raise ValueError(f"authoring.{key} must be a non-empty string")
        _validate_authoring_semantics(data, authoring)
    if not isinstance(data["items"], list) or not data["items"]:
        raise ValueError("items must be a non-empty list")
    for index, item in enumerate(data["items"], start=1):
        if not isinstance(item, dict):
            raise ValueError(f"items[{index}] must be an object")
        if not isinstance(item.get("heading"), str) or not item["heading"].strip():
            raise ValueError(f"items[{index}].heading must be a non-empty string")
        children = item.get("children")
        if not isinstance(children, list) or not children:
            raise ValueError(f"items[{index}].children must be a non-empty list")
        for child_index, child in enumerate(children, start=1):
            if not isinstance(child, dict):
                raise ValueError(f"items[{index}].children[{child_index}] must be an object")
            marker = child.get("marker")
            if marker not in {"□", "ㅇ", "-", "※"}:
                raise ValueError(f"unsupported marker at items[{index}].children[{child_index}]: {marker!r}")
            if not isinstance(child.get("text"), str) or not child["text"].strip():
                raise ValueError(f"items[{index}].children[{child_index}].text must be a non-empty string")
    if "tables" in data:
        tables = data["tables"]
        if not isinstance(tables, list):
            raise ValueError("tables must be a list")
        for table_index, table in enumerate(tables, start=1):
            if not isinstance(table, dict):
                raise ValueError(f"tables[{table_index}] must be an object")
            headers = table.get("headers")
            rows = table.get("rows")
            after_heading = table.get("after_heading")
            if not isinstance(headers, list) or not headers or not all(isinstance(value, str) and value.strip() for value in headers):
                raise ValueError(f"tables[{table_index}].headers must be a non-empty string list")
            if after_heading is not None and (not isinstance(after_heading, str) or not after_heading.strip()):
                raise ValueError(f"tables[{table_index}].after_heading must be a non-empty string when provided")
            if not isinstance(rows, list) or not rows:
                raise ValueError(f"tables[{table_index}].rows must be a non-empty list")
            for row_index, row in enumerate(rows, start=1):
                if not isinstance(row, list) or len(row) != len(headers):
                    raise ValueError(
                        f"tables[{table_index}].rows[{row_index}] must be a list with {len(headers)} cells"
                    )
                if not all(isinstance(value, (str, int, float)) for value in row):
                    raise ValueError(f"tables[{table_index}].rows[{row_index}] cells must be scalar values")
            if "note" in table and not isinstance(table["note"], str):
                raise ValueError(f"tables[{table_index}].note must be a string")
    if "asset_replacements" in data:
        replacements = data["asset_replacements"]
        if not isinstance(replacements, dict):
            raise ValueError("asset_replacements must be an object mapping package path or manifest id to local file path")
        for key, value in replacements.items():
            if not isinstance(key, str) or not key.strip():
                raise ValueError("asset_replacements keys must be non-empty strings")
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"asset_replacements[{key!r}] must be a non-empty file path string")


def report_meta(data: dict[str, Any]) -> str:
    if "authoring" not in data:
        return remove_bold_markers(str(data["meta"]))
    authoring = data["authoring"]
    name = str(authoring.get("name", "")).strip()
    affiliation = f"{authoring['department']} {authoring['team']}"
    if name:
        affiliation = f"{affiliation} {name}"
    return f"< {authoring['date']}, {affiliation} >"


def strip_heading_numbering(value: str) -> str:
    text = remove_bold_markers(str(value)).strip()
    text = re.sub(r"^\s*[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+[.．]?\s*", "", text)
    text = re.sub(r"^\s*\d+[.．]\s*", "", text)
    return text.strip()


def heading_key(value: str) -> str:
    """Normalize item/table anchor headings for slot placement."""
    return re.sub(r"\s+", "", strip_heading_numbering(value))


def heading_number_style(block: str) -> str | None:
    text = block_text(block).strip()
    if re.match(r"^\s*\d+[.．]\s*", text):
        return "decimal"
    if re.match(r"^\s*[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+[.．]?\s*", text):
        return "roman"
    return None


def extract_style_levels(header: str) -> dict[str, int]:
    """Map paragraph style IDs that explicitly encode hierarchy levels.

    HWPX body paragraphs reference style IDs, and the style definitions live in
    header.xml/refList/styles. Some templates render bullets/outline markers via
    style/paraPr instead of literal marker text, so the compiler must preserve
    styleIDRef/paraPrIDRef and inject plain content text only.
    """
    levels: dict[str, int] = {}
    try:
        root = etree.fromstring(header.encode("utf-8"))
    except Exception:
        return levels
    for style in root.xpath('.//*[local-name()="style"]'):
        if style.get("type") != "PARA":
            continue
        style_id = style.get("id")
        raw_name = " ".join(filter(None, [style.get("name"), style.get("engName")]))
        if not style_id:
            continue
        match = re.search(r"(?:레벨|level|outline)\s*(\d+)", raw_name, re.IGNORECASE)
        if match:
            levels[style_id] = int(match.group(1))
    return levels


def first_style_id(block: str) -> str | None:
    match = re.search(r'<hp:p\b[^>]*styleIDRef="(\d+)"', block)
    return match.group(1) if match else None


def replace_chapter_title_block(block: str, roman: str, heading: str) -> str:
    """Edit a table-based section heading without losing layout.

    Some templates split the section number and title across separate table cells.
    Replacing all text in the first run would flatten the designed container, so
    update the number-like first text node and the title-like last text node while
    keeping the table/cell geometry intact.
    """
    heading = strip_heading_numbering(heading)
    texts = list(re.finditer(r"<hp:t>.*?</hp:t>", block, flags=re.DOTALL))
    if len(texts) >= 2 and "<hp:tbl" in block:
        replacements = [html.escape(roman, quote=False), html.escape(f" {heading}", quote=False)]
        selected = [texts[0], texts[-1]]
        out = []
        cursor = 0
        for match, value in zip(selected, replacements):
            out.append(block[cursor:match.start()])
            out.append(f"<hp:t>{value}</hp:t>")
            cursor = match.end()
        out.append(block[cursor:])
        return "".join(out)
    return replace_text_in_block(block, f"{roman} {heading}")


def set_first_paragraph_page_break(block: str, value: str) -> str:
    return re.sub(r'(<hp:p\b[^>]*\bpageBreak=")[01](")', rf"\g<1>{value}\2", block, count=1)


def xml_local_name(element: etree._Element) -> str:
    return etree.QName(element).localname


def xml_text(element: etree._Element) -> str:
    return "".join(
        node.text or ""
        for node in element.iter()
        if xml_local_name(node) == "t"
    ).strip()


def xml_descendants(element: etree._Element, local_name: str) -> list[etree._Element]:
    return [node for node in element.iter() if xml_local_name(node) == local_name]


def replace_known_placeholders(section: str, data: dict[str, Any]) -> str:
    """Apply caller-provided text replacements without template-specific code.

    Arbitrary HWPX templates do not expose semantic slots by themselves. Exact
    placeholder text, when needed, must come from a template profile/slot map or
    the current input JSON, not from hardcoded sample phrases in this script.
    """
    replacements: dict[str, str] = {}
    raw_replacements = data.get("text_replacements")
    if isinstance(raw_replacements, dict):
        for old, new in raw_replacements.items():
            if isinstance(old, str):
                replacements[old] = normalize_text(str(new))

    cover = data.get("cover")
    if isinstance(cover, dict):
        cover_replacements = cover.get("text_replacements")
        if isinstance(cover_replacements, dict):
            for old, new in cover_replacements.items():
                if isinstance(old, str):
                    replacements[old] = normalize_text(str(new))

    for old, new in replacements.items():
        escaped_new = html.escape(new, quote=False)
        section = section.replace(old, escaped_new)
        section = section.replace(html.escape(old, quote=False), escaped_new)
    return section


def _short_summary(data: dict[str, Any], max_sentences: int = 2) -> str:
    """Return a compact summary suitable for a cover callout box."""
    summary = normalize_text(str(data.get("summary", "")).strip())
    if not summary:
        return ""
    parts = re.split(r"(?<=[.!?。！？])\s+", summary)
    if len(parts) <= 1:
        # Korean report summaries often omit final punctuation. Split gently on
        # sentence-like endings while preserving compact administrative style.
        parts = re.split(r"(?<=[다함임음])\s+", summary)
    compact = " ".join(part.strip() for part in parts[:max_sentences] if part.strip())
    return compact or summary


def replace_summary_placeholder_blocks(section: str, summary: str) -> str:
    """Replace the green summary callout placeholder as one visual block.

    Some templates split the instructional placeholder across multiple text
    nodes, for example one node for "중고딕, 13p..." and another node for the
    parenthetical note. Replacing those fragments one by one can leave an empty
    visual line. Treat the paragraph containing the placeholder as a single
    summary slot: put the generated summary in the first text node and clear
    the remaining placeholder text nodes.
    """
    if not summary or "중고딕, 13p" not in section:
        return section
    try:
        root = etree.fromstring(section.encode("utf-8"))
    except Exception:
        return section

    changed = False
    for cell in xml_descendants(root, "tc"):
        paragraphs = [node for node in cell.iter() if xml_local_name(node) == "p"]
        target_index = None
        for index, paragraph in enumerate(paragraphs):
            joined = xml_text(paragraph)
            if "중고딕, 13p" in joined and "글상자" in joined:
                target_index = index
                break
        if target_index is None:
            continue

        target = paragraphs[target_index]
        texts = xml_descendants(target, "t")
        if texts:
            texts[0].text = summary
            for node in texts[1:]:
                node.text = ""
            changed = True

        # The template may store the parenthetical instruction as a separate
        # paragraph inside the same green summary box. Clearing its text leaves
        # a visible blank line, so remove the extra paragraph itself.
        for extra in paragraphs[target_index + 1 :]:
            if "본문에 문서 취지가 포함" in xml_text(extra) or not xml_text(extra):
                parent = extra.getparent()
                if parent is not None:
                    parent.remove(extra)
                    changed = True

        for layout_cache in xml_descendants(cell, "lineSegArray"):
            parent = layout_cache.getparent()
            if parent is not None:
                parent.remove(layout_cache)
    return etree.tostring(root, encoding="unicode") if changed else section


def render_toc_block(prototype: str, data: dict[str, Any]) -> str:
    """Render a simple table-of-contents block for long-form templates."""
    block = etree.fromstring(prototype.encode("utf-8"))
    roman_nums = ["Ⅰ", "Ⅱ", "Ⅲ", "Ⅳ", "Ⅴ", "Ⅵ", "Ⅶ", "Ⅷ", "Ⅸ", "Ⅹ"]
    entries = ["목  차"]
    for index, item in enumerate(data.get("items", [])):
        roman = roman_nums[index] if index < len(roman_nums) else str(index + 1)
        heading = strip_heading_numbering(str(item.get("heading", "")).strip())
        if heading:
            entries.append(f"  {roman}. {heading}")

    paragraphs = xml_descendants(block, "p")
    visible_paragraphs = [p for p in paragraphs if not xml_descendants(p, "tbl")]

    def set_plain_paragraph(paragraph: etree._Element, value: str) -> None:
        for tab in xml_descendants(paragraph, "tab"):
            parent = tab.getparent()
            if parent is not None:
                parent.remove(tab)
        text_nodes = xml_descendants(paragraph, "t")
        if text_nodes:
            text_nodes[0].text = value
            for node in text_nodes[1:]:
                node.text = ""
        for layout_cache in xml_descendants(paragraph, "lineSegArray"):
            parent = layout_cache.getparent()
            if parent is not None:
                parent.remove(layout_cache)

    title = next((p for p in visible_paragraphs if xml_text(p).strip() == "목  차"), None)
    if title is not None:
        set_plain_paragraph(title, entries[0])

    entry_start = next(
        (
            index
            for index, paragraph in enumerate(visible_paragraphs)
            if xml_text(paragraph).strip().startswith("Ⅰ")
        ),
        None,
    )
    if entry_start is not None:
        entry_values = entries[1:]
        for offset, value in enumerate(entry_values):
            target_index = entry_start + offset
            if target_index < len(visible_paragraphs):
                set_plain_paragraph(visible_paragraphs[target_index], value)
        for paragraph in visible_paragraphs[entry_start + len(entry_values) :]:
            set_plain_paragraph(paragraph, "")
        return etree.tostring(block, encoding="unicode")

    text_nodes = [node for node in xml_descendants(block, "t") if (node.text or "").strip()]
    if not text_nodes:
        text_nodes = xml_descendants(block, "t")
    for index, node in enumerate(text_nodes):
        node.text = entries[index] if index < len(entries) else ""
    for layout_cache in xml_descendants(block, "lineSegArray"):
        parent = layout_cache.getparent()
        if parent is not None:
            parent.remove(layout_cache)
    return etree.tostring(block, encoding="unicode")


def replace_template_cover_placeholders(section: str, data: dict[str, Any]) -> str:
    """Replace common public-report cover placeholders without hardcoding a project.

    Public-sector report templates can encode cover/title/date/department slots as
    ordinary HWPX text nodes, not semantic fields. This function maps common
    generic placeholder phrases to report JSON fields before body replacement.
    Exact overrides can still be supplied through text_replacements/cover.
    """
    title = normalize_text(str(data.get("title", "")).strip())
    summary_title = normalize_text(str(data.get("summary_title", "")).strip())
    summary = _short_summary(data)
    meta = report_meta(data)
    authoring = data.get("authoring") if isinstance(data.get("authoring"), dict) else {}
    cover = data.get("cover") if isinstance(data.get("cover"), dict) else {}
    date = normalize_text(str(cover.get("date") or authoring.get("date") or "").strip())
    department = normalize_text(str(cover.get("department") or authoring.get("department") or "").strip())
    team = normalize_text(str(cover.get("team") or authoring.get("team") or "").strip())
    footer_department = normalize_text(str(cover.get("footer_department") or department).strip())

    replacements: dict[str, str] = {}
    if title:
        replacements.update(
            {
                "ㅇㅇㅇㅇ 사업 계획(안)": title,
            }
        )
    if meta:
        replacements["< ’25. 1. 3(화), ㅇㅇㅇ부(실) ㅇㅇㅇ팀 >"] = meta
    if date:
        replacements["2025.  .  ."] = date
    if department:
        replacements["ㅇㅇㅇ부"] = footer_department or department
    # The long-form eyebrow phrase is part of the template identity, like a
    # logo/tagline. Do not replace it with summary_title by default.

    for old, new in replacements.items():
        escaped_new = html.escape(new, quote=False)
        section = section.replace(old, escaped_new)
        section = section.replace(html.escape(old, quote=False), escaped_new)
    section = replace_summary_placeholder_blocks(section, summary)
    section = replace_longform_title_slot(section, title)
    return section


def replace_longform_title_slot(section: str, title: str) -> str:
    """Treat the long-form cover title placeholders as one title slot.

    The template visually suggests two pieces, "◯◯◯◯부" and
    "△△△△△ 기본 계획(안)", but they are one title sample. Replace the
    first text node with the complete one-line title and clear the second text
    node so no extra line or department-like prefix remains.
    """
    if not title or "◯◯◯◯부" not in section or "△△△△△ 기본 계획(안)" not in section:
        return section
    try:
        root = etree.fromstring(section.encode("utf-8"))
    except Exception:
        return section
    paragraphs = [p for p in xml_descendants(root, "p") if not xml_descendants(p, "tbl")]
    first_paragraph = next((p for p in paragraphs if xml_text(p).strip() == "◯◯◯◯부"), None)
    second_paragraph = next((p for p in paragraphs if xml_text(p).strip() == "△△△△△ 기본 계획(안)"), None)
    if first_paragraph is None or second_paragraph is None:
        return section
    text_nodes = xml_descendants(first_paragraph, "t")
    if text_nodes:
        text_nodes[0].text = title
        for node in text_nodes[1:]:
            node.text = ""
    parent = second_paragraph.getparent()
    if parent is not None:
        parent.remove(second_paragraph)
    # The cover title is a single line. The template keeps several blank
    # spacer paragraphs after the sample title; after automatic generation
    # they show up as an unwanted blank line under the title. Remove consecutive
    # empty sibling paragraphs until the next real cover text, such as date.
    title_parent = first_paragraph.getparent() if first_paragraph is not None else None
    if title_parent is not None:
        siblings = list(title_parent)
        try:
            cursor = siblings.index(first_paragraph) + 1
        except ValueError:
            cursor = -1
        while cursor >= 0 and cursor < len(siblings):
            candidate = siblings[cursor]
            if xml_local_name(candidate) != "p" or xml_text(candidate):
                break
            title_parent.remove(candidate)
            siblings.pop(cursor)
    title_row = first_paragraph
    while title_row is not None and xml_local_name(title_row) != "tr":
        title_row = title_row.getparent()
    if title_row is not None:
        for cell_size in xml_descendants(title_row, "cellSz"):
            if cell_size.get("height"):
                cell_size.set("height", "6200")
    # Remove layout cache around the common cover table so the editor recalculates.
    if first_paragraph is not None:
        for cache in xml_descendants(first_paragraph, "lineSegArray"):
            parent = cache.getparent()
            if parent is not None:
                parent.remove(cache)
    return etree.tostring(root, encoding="unicode")


def _element_text(element: etree._Element) -> str:
    return "".join(element.xpath('.//*[local-name()="t"]/text()')).strip()


def _table_header_texts(table_block: etree._Element) -> list[str]:
    rows = table_block.xpath('.//*[local-name()="tbl"]/*[local-name()="tr"]')
    if not rows:
        return []
    return [_element_text(cell) for cell in rows[0].xpath('./*[local-name()="tc"]')]


def _norm_header(value: str) -> str:
    return re.sub(r"\s+", "", value).strip()


def find_table_prototype(section: str, headers: list[str]) -> str | None:
    """Find a top-level table block whose header row matches requested headers.

    Tables are layout containers in HWPX. Reusing the whole top-level paragraph
    preserves the table geometry, border fills, cell margins, and paragraph
    styles better than building XML from scratch.
    """
    wanted = [_norm_header(value) for value in headers]
    if not wanted:
        return None
    try:
        root = etree.fromstring(section.encode("utf-8"))
    except Exception:
        return None

    fallback: str | None = None
    for child in list(root):
        if not child.xpath('.//*[local-name()="tbl"]'):
            continue
        actual = [_norm_header(value) for value in _table_header_texts(child)]
        if not actual or len(actual) != len(wanted):
            continue
        child_xml = etree.tostring(child, encoding="unicode")
        if actual == wanted:
            return child_xml
        # Public-report sample tables often use instructional placeholder
        # headers such as "푸른 음영 / 문자 가운데 정렬 / 숫자 오른쪽 정렬 / 비 고".
        # Those placeholders identify a reusable body-table prototype, even
        # when the generated report uses real semantic headers. Treat that
        # shape as a safe fallback instead of forcing generated JSON to keep
        # the instructional header text.
        if "푸른음영" in actual:
            fallback = child_xml
        # If the table has the same shape and at least two matching semantic
        # headers, keep it as a fallback. This handles minor spacing variants
        # while avoiding author/date cover tables that merely share a column count.
        if len(set(actual) & set(wanted)) >= min(2, len(wanted)):
            fallback = child_xml
    return fallback


def _set_cell_text(cell: etree._Element, value: str) -> None:
    text_nodes = cell.xpath('.//*[local-name()="t"]')
    if text_nodes:
        text_nodes[0].text = normalize_text(str(value))
        for node in text_nodes[1:]:
            node.text = ""
    for layout_cache in cell.xpath('.//*[local-name()="lineSegArray"]'):
        parent = layout_cache.getparent()
        if parent is not None:
            parent.remove(layout_cache)


def render_table_block(prototype: str, table_data: dict[str, Any], next_id: int) -> tuple[str, int]:
    block = etree.fromstring(prototype.encode("utf-8"))
    tbl_nodes = block.xpath('.//*[local-name()="tbl"]')
    if not tbl_nodes:
        raise RuntimeError("table prototype does not contain hp:tbl")
    tbl = tbl_nodes[0]
    rows = tbl.xpath('./*[local-name()="tr"]')
    if len(rows) < 2:
        raise RuntimeError("table prototype needs at least header and body rows")

    headers = [str(value) for value in table_data.get("headers", [])]
    body_rows = [[str(value) for value in row] for row in table_data.get("rows", [])]
    note = str(table_data.get("note", "")).strip()
    col_count = len(headers)

    header_template = copy_element(rows[0])
    body_template = copy_element(rows[1])
    note_template = copy_element(rows[-1])

    for row in rows:
        tbl.remove(row)

    rendered_rows: list[etree._Element] = []
    for row_index, values in enumerate([headers] + body_rows):
        row = copy_element(header_template if row_index == 0 else body_template)
        cells = row.xpath('./*[local-name()="tc"]')
        for col_index, cell in enumerate(cells):
            value = values[col_index] if col_index < len(values) else ""
            _set_cell_text(cell, value)
            for addr in cell.xpath('./*[local-name()="cellAddr"]'):
                addr.set("rowAddr", str(row_index))
                addr.set("colAddr", str(col_index))
        rendered_rows.append(row)

    if note:
        row_index = len(rendered_rows)
        row = copy_element(note_template)
        cells = row.xpath('./*[local-name()="tc"]')
        for col_index, cell in enumerate(cells):
            _set_cell_text(cell, note if col_index == 0 else "")
            for addr in cell.xpath('./*[local-name()="cellAddr"]'):
                addr.set("rowAddr", str(row_index))
                addr.set("colAddr", str(col_index))
        rendered_rows.append(row)

    for row in rendered_rows:
        tbl.append(row)
    tbl.set("rowCnt", str(len(rendered_rows)))
    if col_count:
        tbl.set("colCnt", str(col_count))

    rendered = etree.tostring(block, encoding="unicode")
    return renumber_block(rendered, next_id)


def copy_element(element: etree._Element) -> etree._Element:
    return etree.fromstring(etree.tostring(element))


def find_body_span(section: str, prototypes: dict[str, str]) -> tuple[int, int]:
    prototype_values = [value for key, value in prototypes.items() if key in {"h1", "box", "circle", "dash", "note", "body"}]
    start = min(section.index(value) for value in prototype_values)
    root_close = section.rfind("</")
    end = root_close if root_close > start else len(section)
    attach_text = section.find(">붙임<", start)
    if attach_text != -1:
        attach_para = section.rfind("<hp:p", 0, attach_text)
        if attach_para > start:
            end = attach_para
    return start, end


def _manifest_id_to_href(content_hpf: str) -> dict[str, str]:
    try:
        root = etree.fromstring(content_hpf.encode("utf-8"))
    except Exception:
        return {}
    return {
        str(item.get("id")): str(item.get("href"))
        for item in root.xpath('.//*[local-name()="manifest"]/*[local-name()="item"]')
        if item.get("id") and item.get("href")
    }


def _load_asset_replacements(data: dict[str, Any], entries: list[tuple[zipfile.ZipInfo, bytes]]) -> dict[str, bytes]:
    raw = data.get("asset_replacements")
    if not isinstance(raw, dict) or not raw:
        return {}
    names = {item.filename for item, _ in entries}
    content_hpf = next((payload.decode("utf-8") for item, payload in entries if item.filename == "Contents/content.hpf"), "")
    id_to_href = _manifest_id_to_href(content_hpf)
    replacements: dict[str, bytes] = {}
    for key, path_value in raw.items():
        package_name = key if key in names else id_to_href.get(key)
        if not package_name or package_name not in names:
            raise RuntimeError(f"asset_replacements key does not match package path or manifest id: {key!r}")
        replacement_path = Path(str(path_value)).expanduser()
        if not replacement_path.exists() or not replacement_path.is_file():
            raise RuntimeError(f"asset replacement file not found: {replacement_path}")
        replacements[package_name] = replacement_path.read_bytes()
    return replacements


def build(data: dict[str, Any], output: Path, template: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(template, "r") as zin:
        entries = [(item, zin.read(item.filename)) for item in zin.infolist()]
        section = zin.read("Contents/section0.xml").decode("utf-8")
        header = zin.read("Contents/header.xml").decode("utf-8")
    asset_replacements = _load_asset_replacements(data, entries)

    style_levels = extract_style_levels(header)
    blocks = extract_paragraph_blocks(section)
    prototypes: dict[str, str] = {}

    # Some HWPX templates place section headings inside a table embedded in a
    # top-level paragraph. Regex paragraph extraction sees only the nested cell
    # paragraphs, which destroys the layout if reused. Capture the top-level
    # table paragraph first and treat it as a reusable section-heading block.
    try:
        section_root_for_prototypes = etree.fromstring(section.encode("utf-8"))
        for child in list(section_root_for_prototypes):
            child_text = "".join(child.xpath('.//*[local-name()="t"]/text()')).strip()
            child_xml = etree.tostring(child, encoding="unicode")
            if re.match(r"^[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]\s+", child_text) and "<hp:tbl" in child_xml:
                prototypes["chapter_title"] = child_xml
                prototypes["h1"] = child_xml
                break
    except Exception:
        pass

    for block in blocks:
        text = block_text(block).strip()
        style_level = style_levels.get(first_style_id(block) or "")
        if style_level == 1 and "h1" not in prototypes:
            prototypes["h1"] = block
        elif style_level == 2 and "style_level2" not in prototypes:
            prototypes["style_level2"] = block
        elif style_level == 3 and "style_level3" not in prototypes:
            prototypes["style_level3"] = block
        elif re.match(r"^[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]\s+", text) and "<hp:tbl" in block and "chapter_title" not in prototypes:
            prototypes["chapter_title"] = block
            prototypes["h1"] = block
        elif re.match(r"^\s*\d+[.．]\s*\S+", text) and "h1" not in prototypes:
            prototypes["h1"] = block
        elif " or " in text and "h1" not in prototypes and not bullet_prefix(text):
            # Some templates mark editable section headings with alternatives
            # such as "overview or purpose". Treat that as a structural heading
            # prototype without depending on the exact phrase.
            prototypes["h1"] = block
        elif text.startswith("□ ") and "box" not in prototypes:
            prototypes["box"] = block
        elif (text.startswith("ㅇ ") or text.startswith("○ ")) and "circle" not in prototypes:
            prototypes["circle"] = block
        elif text.startswith("- ") and "dash" not in prototypes:
            prototypes["dash"] = block
        elif text.startswith("※ ") and "note" not in prototypes:
            prototypes["note"] = block
        elif "subbody" not in prototypes and not bullet_prefix(text) and len(text) > 40 and "h1" in prototypes:
            prototypes["subbody"] = block

    has_bullet_template = {"box", "circle", "dash", "note"} <= set(prototypes)
    has_style_level_template = "style_level2" in prototypes
    has_long_report_template = "chapter_title" in prototypes
    onepager_without_h1 = False
    if "h1" not in prototypes and has_bullet_template:
        # One-page public-report forms may have no separate h1 paragraph. In
        # that layout the first □ paragraph is the visual section heading.
        prototypes["h1"] = prototypes["box"]
        onepager_without_h1 = True
    h1_number_style = heading_number_style(prototypes.get("h1", ""))
    if not has_bullet_template and "body" not in prototypes:
        prototypes["body"] = prototypes.get("circle") or prototypes.get("box") or prototypes.get("h1", "")

    missing = {"h1"} - set(prototypes)
    if has_bullet_template:
        missing |= {"box", "circle", "dash", "note"} - set(prototypes)
    elif has_style_level_template:
        missing |= {"style_level2"} - set(prototypes)
    else:
        missing |= {"body"} - set(prototypes)
    if missing:
        raise RuntimeError(f"missing paragraph prototypes: {sorted(missing)}")

    next_id = 30000
    new_blocks: list[str] = []
    tables_by_heading: dict[str, list[tuple[int, dict[str, Any]]]] = {}
    trailing_tables: list[tuple[int, dict[str, Any]]] = []
    placed_table_indexes: set[int] = set()
    for table_index, table_data in enumerate(data.get("tables", []), start=1):
        after_heading = str(table_data.get("after_heading", "")).strip()
        if after_heading:
            tables_by_heading.setdefault(heading_key(after_heading), []).append((table_index, table_data))
        else:
            trailing_tables.append((table_index, table_data))

    style_for = {"□": "box", "ㅇ": "circle", "-": "dash", "※": "note"}
    leading_for = {"□": " ", "ㅇ": "  ", "-": "   ", "※": "       "}
    bold_charpr_id_for: dict[str, str] = {}
    roman_nums = ["Ⅰ", "Ⅱ", "Ⅲ", "Ⅳ", "Ⅴ", "Ⅵ", "Ⅶ", "Ⅷ", "Ⅸ", "Ⅹ"]

    def append_table(table_index: int, table_data: dict[str, Any]) -> None:
        nonlocal next_id
        headers = [str(value) for value in table_data.get("headers", [])]
        table_prototype = find_table_prototype(section, headers)
        if table_prototype is None:
            raise RuntimeError(
                f"could not locate table prototype for tables[{table_index}] headers={headers!r}"
            )
        table_block, next_id = render_table_block(table_prototype, table_data, next_id)
        new_blocks.append(table_block)
        placed_table_indexes.add(table_index)

    for item_index, item in enumerate(data["items"]):
        heading = item["heading"]
        original_heading = heading
        if has_long_report_template and "<hp:tbl" in prototypes.get("chapter_title", ""):
            roman = roman_nums[item_index] if item_index < len(roman_nums) else str(item_index + 1)
            rendered = replace_chapter_title_block(prototypes["chapter_title"], roman, heading)
            rendered = set_first_paragraph_page_break(rendered, "1" if item_index == 0 else "0")
        elif onepager_without_h1:
            heading = f" □ {strip_heading_numbering(heading)}"
            rendered, header = replace_text_in_block_with_runs(prototypes["box"], heading, header, bold_charpr_id_for)
        else:
            if has_long_report_template:
                heading = f" {roman_nums[item_index] if item_index < len(roman_nums) else str(item_index + 1)}. {strip_heading_numbering(heading)}"
            elif h1_number_style == "decimal":
                heading = f"{item_index + 1}. {strip_heading_numbering(heading)}"
            rendered, header = replace_text_in_block_with_runs(prototypes["h1"], heading, header, bold_charpr_id_for)
        block, next_id = renumber_block(rendered, next_id)
        new_blocks.append(block)
        for child in item["children"]:
            marker = child["marker"]
            text = child["text"]
            if has_style_level_template:
                value = text
                prototype = prototypes.get("style_level3") if marker in {"-", "※"} and "style_level3" in prototypes else prototypes["style_level2"]
            elif has_bullet_template:
                effective_marker = "ㅇ" if onepager_without_h1 and marker == "□" else marker
                value = f"{leading_for[effective_marker]}{effective_marker} {text}"
                prototype = prototypes[style_for[effective_marker]]
            else:
                value = text
                prototype = prototypes.get("subbody") if marker in {"ㅇ", "-", "※"} and "subbody" in prototypes else prototypes["body"]
            rendered, header = replace_text_in_block_with_runs(prototype, value, header, bold_charpr_id_for)
            block, next_id = renumber_block(rendered, next_id)
            new_blocks.append(block)
        for table_index, table_data in tables_by_heading.get(heading_key(original_heading), []):
            append_table(table_index, table_data)

    unmatched_tables = sorted(set(index for values in tables_by_heading.values() for index, _ in values) - placed_table_indexes)
    if unmatched_tables:
        known = [heading_key(str(item["heading"])) for item in data["items"]]
        raise RuntimeError(f"tables after_heading did not match any item heading: {unmatched_tables}; known headings={known!r}")

    for table_index, table_data in trailing_tables:
        append_table(table_index, table_data)

    section = replace_known_placeholders(section, data)
    section = replace_template_cover_placeholders(section, data)
    if has_long_report_template:
        root = etree.fromstring(section.encode("utf-8"))

        def child_text(element: etree._Element) -> str:
            return xml_text(element)

        for child in list(root):
            if child_text(child).startswith("목  차"):
                rendered_toc = render_toc_block(etree.tostring(child, encoding="unicode"), data)
                root.replace(child, etree.fromstring(rendered_toc.encode("utf-8")))
                break

        start_index = None
        for index, child in enumerate(root):
            if child_text(child).startswith("Ⅰ"):
                start_index = index
                break
        if start_index is None:
            raise RuntimeError("could not locate roman body start")
        for child in list(root)[start_index:]:
            root.remove(child)
        ns_attrs = " ".join(
            f'xmlns:{prefix}="{uri}"' if prefix else f'xmlns="{uri}"'
            for prefix, uri in root.nsmap.items()
        )
        for block in new_blocks:
            wrapped = etree.fromstring(f"<wrap {ns_attrs}>{block}</wrap>".encode("utf-8"))
            root.append(wrapped[0])
        section = etree.tostring(root, encoding="unicode")
    elif has_bullet_template:
        start, end = find_body_span(section, prototypes)
        section = section[:start] + "\n".join(new_blocks) + section[end:]
    else:
        root = etree.fromstring(section.encode("utf-8"))

        def child_text(element: etree._Element) -> str:
            return "".join(element.xpath('.//*[local-name()="t"]/text()')).strip()

        start_index = None
        prototype_heading_text = strip_heading_numbering(block_text(prototypes["h1"]))
        for index, child in enumerate(root):
            current_text = strip_heading_numbering(child_text(child))
            if current_text == prototype_heading_text or current_text.startswith(prototype_heading_text):
                start_index = index
                break
        if start_index is None:
            raise RuntimeError("could not locate body start from detected heading prototype")
        for child in list(root)[start_index:]:
            root.remove(child)
        ns_attrs = " ".join(
            f'xmlns:{prefix}="{uri}"' if prefix else f'xmlns="{uri}"'
            for prefix, uri in root.nsmap.items()
        )
        for block in new_blocks:
            wrapped = etree.fromstring(f"<wrap {ns_attrs}>{block}</wrap>".encode("utf-8"))
            root.append(wrapped[0])
        section = etree.tostring(root, encoding="unicode")
    section = strip_layout_cache(section)

    def first_para_pr_id(block: str) -> str | None:
        match = re.search(r'<hp:p\b[^>]*paraPrIDRef="(\d+)"', block)
        return match.group(1) if match else None

    base_ids = {
        marker: first_para_pr_id(prototypes[style])
        for marker, style in style_for.items()
        if style in prototypes and first_para_pr_id(prototypes[style])
    }
    max_para_id = max(int(x) for x in re.findall(r'<hh:paraPr\b(?=[^>]*\sid="(\d+)")', header))
    para_cache: dict[tuple[str, int], int] = {}
    additions: list[str] = []

    def update_para(match: re.Match[str]) -> str:
        nonlocal max_para_id
        block = match.group(0)
        text = html.unescape(block_text(block))
        prefix = bullet_prefix(text)
        if not prefix:
            return block
        marker = prefix.strip()[:1]
        base_id = base_ids.get(marker)
        if not base_id:
            return block
        width = prefix_width_pt(prefix, charpr_height_pt(header, first_run_charpr_id(block)))
        width_key = round(width * 100)
        cache_key = (base_id, width_key)
        if cache_key not in para_cache:
            base = re.search(r'<hh:paraPr\b(?=[^>]*\sid="' + base_id + r'")[^>]*>.*?</hh:paraPr>', header, re.DOTALL)
            if not base:
                raise RuntimeError(f"missing base paraPr {base_id}")
            max_para_id += 1
            para_cache[cache_key] = max_para_id
            additions.append(_para_pr_with_hanging(base.group(0), max_para_id, width))
        return re.sub(r'paraPrIDRef="\d+"', f'paraPrIDRef="{para_cache[cache_key]}"', block, count=1)

    # Derive hanging indents from the actual emitted bullet prefix width.
    # This must run for long-form templates as well: chapter/title containers
    # are preserved separately, but generated body bullets still need the same
    # text-start alignment used by one-page and multi-page templates.
    section = re.sub(r"<hp:p\b[^>]*>\s*<hp:run\b[^>]*>\s*<hp:t>.*?</hp:p>", update_para, section, flags=re.DOTALL)

    if additions:
        header = re.sub(
            r'<hh:paraProperties itemCnt="(\d+)">',
            lambda m: f'<hh:paraProperties itemCnt="{int(m.group(1)) + len(additions)}">',
            header,
            count=1,
        )
        header = header.replace("</hh:paraProperties>", "".join(additions) + "</hh:paraProperties>", 1)

    with zipfile.ZipFile(output, "w") as zout:
        for item, raw in entries:
            data_bytes = raw
            if item.filename in asset_replacements:
                data_bytes = asset_replacements[item.filename]
            elif item.filename == "Contents/header.xml":
                data_bytes = header.encode("utf-8")
            elif item.filename == "Contents/section0.xml":
                data_bytes = section.encode("utf-8")
            elif item.filename == "Preview/PrvText.txt":
                data_bytes = (normalize_text(str(data["title"])) + "\n" + normalize_text(str(data["summary"]))).encode("utf-8")

            if item.filename == "mimetype":
                zout.writestr(item, data_bytes, compress_type=zipfile.ZIP_STORED)
            else:
                zout.writestr(item, data_bytes)

    errors = validate_hwpx(output, template=template)
    if errors:
        raise RuntimeError("\n".join(errors))
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a template-based HWPX report from structured JSON.")
    parser.add_argument("--input", type=Path, help="UTF-8 JSON report input path")
    parser.add_argument("--output", type=Path, help="output .hwpx path")
    parser.add_argument(
        "--template",
        type=Path,
        help="template .hwpx path. Required for generation so the caller explicitly selects the target template.",
    )
    parser.add_argument("--validate-only", type=Path, help="validate an existing .hwpx and exit")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.validate_only:
        validation_errors = validate_hwpx(args.validate_only)
        if validation_errors:
            raise RuntimeError("\n".join(validation_errors))
        print(f"OK: {args.validate_only}")
    else:
        if args.input is None or args.output is None or args.template is None:
            raise SystemExit("--input, --output, and --template are required unless --validate-only is used")
        print(build(load_report(args.input), args.output, args.template))
