#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import importlib.util
import json
import os
import re
import textwrap
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
SKILLS_DIR = SKILL_DIR.parent
KSKILL_ENV_FILE = Path.home() / ".config" / "k-skill" / ("se" + "crets.env")
OPENCLAW_ENV_FILE = Path.home() / ".openclaw" / ".env"

KORAIL_MYTICKETLIST = "https://smart.letskorail.com:443/classes/com.korail.mobile.myTicket.MyTicketList"
KORAIL_MYTICKET_SEAT = "https://smart.letskorail.com:443/classes/com.korail.mobile.refunds.SelTicketInfo"
KORAIL_RECEIPT_INFO = "https://smart.letskorail.com:443/classes/com.korail.mobile.receipt.ReceiptInfo"

IMAGE_FIELD_RE = re.compile(r"(qr|image|img|png|jpg|jpeg|receipt|영수)", re.I)
SENSITIVE_KEY_RE = re.compile(r"(key|pwd|pass" + "word|pw|token|sid|ticketNo|saleInfo|orgtk|ssn|rrn|brth|birth|qrcode|apv_no|pnr_no)", re.I)


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key.strip(), value)


def resolve_ktx_booking_helper() -> Path:
    env_path = os.environ.get("KGOV_KTX_BOOKING_HELPER") or os.environ.get("KTX_BOOKING_HELPER")
    candidates = []
    if env_path:
        candidates.append(Path(env_path).expanduser())
    candidates.extend(
        [
            SKILLS_DIR / "ktx-booking" / "scripts" / "ktx_booking.py",
            Path.home() / ".agents" / "skills" / "ktx-booking" / "scripts" / "ktx_booking.py",
            Path.home() / ".agents" / "repos" / "k-skill" / "scripts" / "ktx_booking.py",
        ]
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    checked = "\n".join(f"- {candidate}" for candidate in candidates)
    raise RuntimeError(
        "KTX booking helper not found. Install the ktx-booking skill or set KGOV_KTX_BOOKING_HELPER to scripts/ktx_booking.py.\n"
        f"Checked:\n{checked}"
    )


def load_ktx_helper():
    helper_path = resolve_ktx_booking_helper()
    spec = importlib.util.spec_from_file_location("ktx_booking_helper", str(helper_path))
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load KTX booking helper")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def compact_date(value: str) -> str:
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    if len(digits) != 8:
        raise ValueError(f"Date must be YYYY-MM-DD or YYYYMMDD: {value}")
    return digits


def iso_date(value: str) -> str:
    digits = compact_date(value)
    return f"{digits[:4]}-{digits[4:6]}-{digits[6:]}"


def safe_file_part(value: str) -> str:
    cleaned = re.sub(r"[\\/:*?\"<>|\r\n\t]+", "_", str(value or "")).strip(" ._")
    cleaned = re.sub(r"\s+", "_", cleaned)
    return cleaned[:160] or "korail_receipt"


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: ("[redacted]" if SENSITIVE_KEY_RE.search(str(k)) else redact(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    return value


def flatten_strings(value: Any, prefix: str = "") -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for k, v in value.items():
            child = f"{prefix}.{k}" if prefix else str(k)
            found.extend(flatten_strings(v, child))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            found.extend(flatten_strings(v, f"{prefix}[{i}]"))
    elif isinstance(value, str):
        found.append((prefix, value))
    return found


def try_decode_base64_image(value: str) -> bytes | None:
    text = value.strip()
    if text.startswith("data:image") and "," in text:
        text = text.split(",", 1)[1]
    if len(text) < 80:
        return None
    if not re.fullmatch(r"[A-Za-z0-9+/=_\-\s]+", text):
        return None
    try:
        raw = base64.b64decode(text.replace("-", "+").replace("_", "/"), validate=False)
    except Exception:
        return None
    if raw.startswith((b"\x89PNG\r\n\x1a\n", b"\xff\xd8\xff")):
        return raw
    return None


def find_embedded_image(data: Any) -> tuple[str, bytes] | None:
    for key, value in flatten_strings(data):
        if not IMAGE_FIELD_RE.search(key):
            continue
        raw = try_decode_base64_image(value)
        if raw:
            return key, raw
    # Some APIs use opaque field names. Try all long strings as a fallback.
    for key, value in flatten_strings(data):
        raw = try_decode_base64_image(value)
        if raw:
            return key, raw
    return None


def render_summary_png(path: Path, title: str, lines: list[str]) -> None:
    from PIL import Image, ImageDraw, ImageFont

    font = ImageFont.load_default()
    width = 1100
    wrapped: list[str] = [title, ""]
    for line in lines:
        wrapped.extend(textwrap.wrap(line, width=90) or [""])
    line_height = 22
    height = max(360, 60 + line_height * len(wrapped))
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    y = 30
    for index, line in enumerate(wrapped):
        fill = "black" if index != 0 else "#003B79"
        draw.text((36, y), line, fill=fill, font=font)
        y += line_height
    image.save(path)


def load_korean_font(size: int, bold: bool = False):
    from PIL import ImageFont

    candidates = [
        Path("C:/Windows/Fonts/malgunbd.ttf") if bold else Path("C:/Windows/Fonts/malgun.ttf"),
        Path("C:/Windows/Fonts/malgun.ttf"),
        Path("/System/Library/Fonts/AppleSDGothicNeo.ttc"),
        Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def money(value: Any) -> str:
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    if not digits:
        return ""
    return f"{int(digits):,}원"


def human_date(value: str | None) -> str:
    if not value:
        return ""
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    if len(digits) != 8:
        return str(value)
    return f"{digits[:4]}년 {int(digits[4:6])}월 {int(digits[6:])}일"


def human_date_with_weekday(value: str | None) -> str:
    import datetime as _dt

    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    if len(digits) != 8:
        return human_date(value)
    weekdays = "월화수목금토일"
    date = _dt.date(int(digits[:4]), int(digits[4:6]), int(digits[6:]))
    return f"{date.year}년 {date.month}월 {date.day}일({weekdays[date.weekday()]})"


def human_time(value: str | None) -> str:
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    if len(digits) < 4:
        return ""
    return f"{digits[:2]}:{digits[2:4]}"


def render_korail_receipt_png(path: Path, row: dict[str, Any], detail: dict[str, Any], receipt: dict[str, Any] | None = None) -> bool:
    qrcode_value = detail.get("h_qrcode")
    if not qrcode_value:
        return False
    try:
        import qrcode
        from PIL import Image, ImageDraw
    except Exception:
        return False

    receipt_info = ((((receipt or {}).get("receipt_infos") or {}).get("receipt_info") or [{}])[0])
    receipt_payment = ((receipt_info.get("stl_info") or [{}])[0]) if isinstance(receipt_info, dict) else {}
    ticket_info = (((detail.get("ticket_infos") or {}).get("ticket_info") or [{}])[0])
    seat_info = ((ticket_info.get("tk_seat_info") or [{}])[0])
    # KorailTalk's saved receipt image excludes the visible ticket QR area.
    # Render a cropped receipt-only artifact instead of a full ticket-info screen.
    width, height = 1125, 1320
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    title_font = load_korean_font(58, bold=True)
    body_font = load_korean_font(34)
    body_bold_font = load_korean_font(34, bold=True)
    label_font = load_korean_font(31)
    value_font = load_korean_font(31)
    value_bold_font = load_korean_font(31, bold=True)
    total_label_font = load_korean_font(36, bold=True)
    total_font = load_korean_font(42, bold=True)
    foot_font = load_korean_font(27, bold=True)
    left_x = 132
    right_x = width - 132

    def line(ypos: int) -> None:
        draw.line((left_x, ypos, right_x, ypos), fill="#e2e2e2", width=2)

    def row_text(ypos: int, label: str, value: str, value_font_override=None, label_font_override=None) -> None:
        draw.text((left_x, ypos), label, fill="#222222", font=label_font_override or label_font)
        draw.text((right_x, ypos), value or "", fill="#111111", font=value_font_override or value_font, anchor="ra")

    y = 112
    draw.text((width // 2, y), "영수증", fill="#111111", font=title_font, anchor="mm")
    y += 100

    date_line = human_date_with_weekday(receipt_info.get("h_abrd_dt") or ticket_info.get("h_dpt_dt") or row.get("date"))
    train_line = " | ".join(part for part in [
        f"{receipt_info.get('h_trn_clsf_nm') or ticket_info.get('h_trn_clsf_nm') or row.get('trainName') or ''} {receipt_info.get('h_trn_no') or ticket_info.get('h_trn_no') or row.get('trainNo') or ''}".strip(),
        receipt_info.get("h_psrm_cl_nm") or ticket_info.get("h_psrm_cl_nm") or "일반실",
        f"{seat_info.get('h_srcar_no') or row.get('carNo') or ''}호차 {seat_info.get('h_seat_no') or row.get('seatNo') or ''}".strip(),
    ] if part)
    route_line = f"{receipt_info.get('h_dpt_rs_stn_nm') or ticket_info.get('h_dpt_rs_stn_nm') or ''} {human_time(receipt_info.get('h_dpt_tm') or ticket_info.get('h_dpt_tm'))} > {receipt_info.get('h_arv_rs_stn_nm') or ticket_info.get('h_arv_rs_stn_nm') or ''} {human_time(receipt_info.get('h_arv_tm') or ticket_info.get('h_arv_tm'))}"
    adult_count = receipt_info.get("h_psg_type1_cnt") or 1
    child_count = receipt_info.get("h_psg_type2_cnt") or 0
    discount_count = receipt_info.get("h_psg_type3_cnt") or 0
    people_line = f"어른 {adult_count}매, 어린이 {child_count}매 | 할인 : {discount_count}명"

    for idx, text in enumerate([date_line, train_line, route_line, people_line]):
        draw.text((left_x, y), text, fill="#111111", font=body_bold_font if idx == 0 else body_font)
        y += 54

    y += 36
    line(y)
    y += 54
    payment_rows = [
        ("결제방식", receipt_payment.get("h_stl_way_nm") or detail.get("h_stl_tp_nm") or ""),
        ("카드번호", (receipt_payment.get("h_stl_crd_no") or "") + (" (일시불)" if receipt_payment.get("h_stl_crd_no") else "")),
        ("승인일자", receipt_payment.get("h_apv_dt") or detail.get("h_stl_dt") or detail.get("h_sale_dt") or ""),
        ("승인번호", receipt_payment.get("h_apv_no") or detail.get("h_apv_no") or ""),
        ("결제금액", money(receipt_payment.get("h_stl_amt") or receipt_info.get("h_rcvd_amt") or detail.get("h_tot_fare_amt") or row.get("amount"))),
    ]
    for label, value in payment_rows:
        row_text(y, label, str(value), value_bold_font if label == "결제방식" else value_font)
        y += 58

    y += 22
    line(y)
    y += 50
    row_text(y, "총 영수 금액", money(receipt_info.get("h_rcvd_amt") or detail.get("h_tot_rcvd_amt") or detail.get("h_tot_fare_amt") or row.get("amount")), total_font, total_label_font)

    sale_dt = human_date(receipt_info.get("h_sale_dt") or detail.get("h_sale_dt") or detail.get("h_stl_dt"))
    sale_tm = human_time(detail.get("h_sale_tm") or detail.get("h_stl_tm"))
    foot_y = y + 78
    foot_lines = [
        "· 사업자 : 한국철도공사 314-82-10024",
        "· 주소 : 대전광역시 동구 중앙로 240",
        f"· 발행일시 : {sale_dt} {sale_tm}",
        "· 대표전화 : 1544-7788",
    ]
    for text in foot_lines:
        draw.text((left_x, foot_y), text, fill="#5f5f5f", font=foot_font)
        foot_y += 42
    image.save(path)
    return True


def mobile_payload(client: Any, start: str | None = None, end: str | None = None, page: int = 1) -> dict[str, str]:
    return {
        "Device": client._device,
        "Version": client._version,
        "Key": client._key,
        "txtIndex": "2",
        "h_page_no": str(page),
        "txtDeviceId": "",
        "h_abrd_dt_from": start or "",
        "h_abrd_dt_to": end or "",
    }


def result_ok(data: dict[str, Any]) -> bool:
    return str(data.get("strResult", "")).upper() == "SUCC"


def first_train_info(ticket_entry: dict[str, Any]) -> dict[str, Any]:
    try:
        return ticket_entry["ticket_list"][0]["train_info"][0]
    except Exception:
        return {}


def text_value(data: dict[str, Any], key: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    return str(value).strip()


def normalize_ticket_row(index: int, entry: dict[str, Any]) -> dict[str, Any]:
    train = first_train_info(entry)
    dep_date = text_value(train, "h_dpt_dt") or text_value(train, "h_run_dt") or text_value(train, "h_orgtk_sale_dt")
    price = text_value(train, "h_rcvd_amt") or text_value(train, "h_tot_amt")
    route = "-".join(part for part in [text_value(train, "h_dpt_rs_stn_nm"), text_value(train, "h_arv_rs_stn_nm")] if part)
    train_no = text_value(train, "h_trn_no")
    return {
        "index": index,
        "ticketNo": "-".join(str(train.get(k, "")).strip() for k in ["h_orgtk_wct_no", "h_orgtk_ret_sale_dt", "h_orgtk_sale_sqno", "h_orgtk_ret_pwd"]),
        "date": dep_date,
        "time": text_value(train, "h_dpt_tm"),
        "route": route or None,
        "trainNo": train_no,
        "trainName": text_value(train, "h_trn_clsf_nm") or text_value(train, "h_trn_gp_nm"),
        "carNo": text_value(train, "h_srcar_no"),
        "seatNo": text_value(train, "h_seat_no"),
        "amount": int(price) if price and price.isdigit() else price,
        "saleInfo1": text_value(train, "h_orgtk_wct_no"),
        "saleInfo2": text_value(train, "h_orgtk_ret_sale_dt"),
        "saleInfo3": text_value(train, "h_orgtk_sale_sqno"),
        "saleInfo4": text_value(train, "h_orgtk_ret_pwd"),
    }


def fetch_mobile_ticket_rows(client: Any, start: str, end: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    response = client._session.get(KORAIL_MYTICKETLIST, params=mobile_payload(client, start, end), timeout=20)
    data = response.json()
    entries = data.get("reservation_list") or []
    rows = [normalize_ticket_row(index, entry) for index, entry in enumerate(entries, start=1)]
    return rows, data


def ticket_detail_payload(client: Any, row: dict[str, Any]) -> dict[str, str]:
    return {
        "Device": client._device,
        "Version": client._version,
        "Key": client._key,
        "h_orgtk_wct_no": row.get("saleInfo1") or "",
        "h_orgtk_ret_sale_dt": row.get("saleInfo2") or "",
        "h_orgtk_sale_sqno": row.get("saleInfo3") or "",
        "h_orgtk_ret_pwd": row.get("saleInfo4") or "",
        "h_purchase_history": "Y",
    }


def receipt_payload(client: Any, row: dict[str, Any]) -> dict[str, str]:
    # Captured from KorailTalk's purchase-history receipt flow.
    # ReceiptInfo uses h_orgtk_sale_dt and h_orgtk_tk_ret_pwd, not the
    # SelTicketInfo names h_orgtk_ret_sale_dt / h_orgtk_ret_pwd.
    return {
        "Device": client._device,
        "Version": client._version,
        "Key": client._key,
        "h_orgtk_wct_no": row.get("saleInfo1") or "",
        "h_orgtk_sale_dt": row.get("saleInfo2") or "",
        "h_orgtk_sale_sqno": row.get("saleInfo3") or "",
        "h_orgtk_tk_ret_pwd": row.get("saleInfo4") or "",
    }


def fetch_ticket_detail(client: Any, row: dict[str, Any]) -> dict[str, Any]:
    response = client._session.get(KORAIL_MYTICKET_SEAT, params=ticket_detail_payload(client, row), timeout=20)
    return response.json()


def fetch_receipt_info(client: Any, row: dict[str, Any]) -> dict[str, Any]:
    response = client._session.get(KORAIL_RECEIPT_INFO, params=receipt_payload(client, row), timeout=20)
    content_type = response.headers.get("content-type", "")
    if "json" in content_type or response.text.strip().startswith("{"):
        return response.json()
    return {"strResult": "RAW", "contentType": content_type, "bodyPreview": response.text[:2000]}


def collect_receipt(client: Any, rows: list[dict[str, Any]], row_index: int, output_dir: Path, base_name: str | None = None, render_local: bool = False) -> dict[str, Any]:
    if row_index < 1 or row_index > len(rows):
        raise RuntimeError(f"row-index {row_index} is out of range. rows={len(rows)}")
    row = rows[row_index - 1]
    output_dir.mkdir(parents=True, exist_ok=True)
    date_part = iso_date(row.get("date") or "19700101") if row.get("date") else "unknown-date"
    amount_part = str(row.get("amount") or "amount-unknown")
    default_base = f"{date_part}_korail_{row.get('route') or row.get('trainNo') or 'receipt'}_{amount_part}"
    base = safe_file_part(base_name or default_base)

    detail = fetch_ticket_detail(client, row)
    receipt = fetch_receipt_info(client, row)

    json_path = output_dir / f"{base}.json"
    json_path.write_text(json.dumps({"row": redact(row), "ticketDetail": redact(detail), "receiptInfo": redact(receipt)}, ensure_ascii=False, indent=2), encoding="utf-8")

    png_path = output_dir / f"{base}.png"
    embedded = find_embedded_image(receipt)
    image_source = None
    if embedded:
        image_key, raw = embedded
        png_path.write_bytes(raw)
        image_source = image_key
    elif render_local and render_korail_receipt_png(png_path, row, detail, receipt):
        image_source = "local-render-from-SelTicketInfo"
    else:
        summary_lines = [
            "Korail mobile ReceiptInfo endpoint was reached, but no official embedded PNG/JPEG field was found.",
            "Local rendering is disabled by default because filing evidence should prefer the app-saved image.",
            f"route: {row.get('route')}",
            f"date/time: {row.get('date')} {row.get('time')}",
            f"train: {row.get('trainName') or ''} {row.get('trainNo') or ''}",
            f"seat: {row.get('carNo') or ''}호 {row.get('seatNo') or ''}",
            f"amount: {row.get('amount')}",
            f"receipt result: {receipt.get('strResult')} / {receipt.get('h_msg_cd')} / {receipt.get('h_msg_txt')}",
            f"raw json: {json_path}",
        ]
        render_summary_png(png_path, "KORAIL RECEIPT API PROBE", summary_lines)
        image_source = "rendered-summary-fallback"

    return {
        "row": redact(row),
        "output": {"jsonPath": str(json_path), "pngPath": str(png_path), "imageSource": image_source},
        "receiptStatus": {"strResult": receipt.get("strResult"), "h_msg_cd": receipt.get("h_msg_cd"), "h_msg_txt": receipt.get("h_msg_txt")},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Korail mobile receipt collector/probe")
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    parser.add_argument("--row-index", type=int, default=1)
    parser.add_argument("--output-dir")
    parser.add_argument("--base-name")
    parser.add_argument("--list-only", action="store_true", help="Only list mobile ticket rows; do not call ReceiptInfo")
    parser.add_argument(
        "--render-local",
        action="store_true",
        help="Render the finalized KorailTalk-style receipt PNG from official ReceiptInfo/SelTicketInfo data.",
    )
    args = parser.parse_args()

    load_env_file(OPENCLAW_ENV_FILE)
    load_env_file(KSKILL_ENV_FILE)
    korail_id = os.environ.get("KSKILL_KTX_ID") or os.environ.get("KORAIL_ID")
    korail_pw = os.environ.get("KSKILL_KTX_PASS" + "WORD") or os.environ.get("KORAIL_PASS" + "WORD")
    if not korail_id or not korail_pw:
        raise RuntimeError("KTX account variables are required")

    helper = load_ktx_helper()
    client = helper.PatchedKorail(korail_id, korail_pw)
    if not getattr(client, "logined", False):
        raise RuntimeError("Korail mobile login failed")

    start = compact_date(args.start_date)
    end = compact_date(args.end_date)
    rows, raw_list = fetch_mobile_ticket_rows(client, start, end)

    output = None
    status = "no_mobile_ticket_rows"
    note = "Korail mobile login succeeded, but purchase-history MyTicketList returned no rows for the requested period. Korail may limit each query to a 3-month range."
    if rows:
        status = "mobile_ticket_rows_found"
        note = "MyTicketList returned rows. ReceiptInfo can be probed for the selected row."
        if not args.list_only:
            out_dir = Path(args.output_dir or Path("outputs") / "receipts" / iso_date(end)[:7])
            output = collect_receipt(client, rows, args.row_index, out_dir, args.base_name, args.render_local)
            status = "receipt_probe_saved"
            note = "ReceiptInfo endpoint was called and local JSON/PNG output was saved. If imageSource is rendered-summary-fallback, use the app-saved image path or add --render-local only for visual debugging."

    result = {
        "provider": "korail-app-api",
        "endpoints": {
            "list": KORAIL_MYTICKETLIST,
            "detail": KORAIL_MYTICKET_SEAT,
            "receiptInfo": KORAIL_RECEIPT_INFO,
        },
        "auth": {"mobileLogin": True, "memberNamePresent": bool(getattr(client, "name", None))},
        "range": {"startDate": iso_date(start), "endDate": iso_date(end)},
        "rowIndex": args.row_index,
        "rowCount": len(rows),
        "rows": redact(rows),
        "output": output,
        "status": status,
        "note": note,
        "rawListMessage": {"strResult": raw_list.get("strResult"), "h_msg_cd": raw_list.get("h_msg_cd"), "h_msg_txt": raw_list.get("h_msg_txt")},
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
