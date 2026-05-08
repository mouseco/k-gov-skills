import argparse
import html
import json
import shutil
import subprocess
from pathlib import Path


def esc(value):
    return html.escape(str(value or ""))


def rows(items, kind):
    out = []
    if kind == "simple":
        for i, item in enumerate(items, 1):
            out.append(f"<tr><td>{i}</td><td>{esc(item.get('category'))}</td><td>{esc(item.get('content'))}</td></tr>")
    elif kind == "actions":
        for i, item in enumerate(items, 1):
            out.append(
                f"<tr><td>{i}</td><td>{esc(item.get('owner'))}</td><td>{esc(item.get('task'))}</td>"
                f"<td>{esc(item.get('due'))}</td><td>{esc(item.get('note'))}</td></tr>"
            )
    elif kind == "transcript":
        for item in items:
            out.append(
                f"<tr><td class='time'>{esc(item.get('time'))}</td><td class='speaker'>{esc(item.get('speaker'))}</td>"
                f"<td>{esc(item.get('summary'))}</td></tr>"
            )
    return "\n".join(out)


def checks(items):
    return "".join(f"<li>{esc(item)}</li>" for item in items)


def render_html(data):
    participants = ", ".join(data.get("participants", []))
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8" />
<title>회의록 - {esc(data.get('title'))}</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/variable/pretendardvariable-dynamic-subset.css" />
<style>
  @page {{ size: A4; margin: 13mm 15mm 12mm 15mm; }}
  * {{ box-sizing: border-box; }}
  html, body {{ margin:0; padding:0; background:#fff; color:#111; }}
  body {{ font-family:"Pretendard Variable", Pretendard, "Noto Sans KR", "Malgun Gothic", sans-serif; font-size:10.6px; line-height:1.38; letter-spacing:-0.01em; }}
  .page {{ page-break-after: always; background:#fff; }}
  .page:last-child {{ page-break-after:auto; }}
  .doc-no {{ text-align:right; font-size:9px; color:#666; margin-bottom:7px; }}
  h1 {{ margin:0 0 10px; text-align:center; font-size:22px; letter-spacing:0.18em; font-weight:800; color:#000; }}
  h2 {{ margin:0 0 8px; text-align:center; font-size:18px; letter-spacing:0.08em; font-weight:800; }}
  .top-rule {{ border-top:2px solid #111; margin-bottom:8px; }}
  table {{ width:100%; border-collapse:collapse; table-layout:fixed; page-break-inside:auto; }}
  tr {{ page-break-inside:avoid; page-break-after:auto; }}
  th, td {{ border:1px solid #333; padding:3.8px 5.5px; vertical-align:top; }}
  th {{ background:#f0f0f0; text-align:center; font-weight:760; color:#111; }}
  .meta th {{ width:16%; }} .meta td {{ width:34%; }}
  .section-title {{ margin:9px 0 4.5px; padding:3.8px 7px; border-left:4px solid #111; border-top:1px solid #111; border-right:1px solid #111; border-bottom:1px solid #111; background:#f6f6f6; font-size:12px; font-weight:800; }}
  .agenda td:first-child, .actions td:first-child {{ text-align:center; font-weight:700; }}
  .plain-list {{ margin:0; padding-left:16px; }} .plain-list li {{ margin:1.2px 0; }}
  .small {{ font-size:10px; color:#333; }}
  .page-footer {{ margin-top:6px; text-align:right; color:#999; font-size:8.8px; }}
  .speaker {{ font-weight:800; white-space:nowrap; }}
  .time {{ color:#555; font-size:9.1px; white-space:nowrap; text-align:center; }}
  .transcript {{ font-size:9.35px; line-height:1.28; }}
  .transcript th, .transcript td {{ padding:3.1px 4.7px; }}
</style>
</head>
<body>
<section class="page">
  <div class="doc-no">문서상태: {esc(data.get('status', '회의록 초안'))} / 작성기준: {esc(data.get('source_note', '회의 메모'))}</div>
  <h1>회 의 록</h1>
  <div class="top-rule"></div>
  <table class="meta">
    <tr><th>회의명</th><td>{esc(data.get('title'))}</td><th>작성일</th><td>{esc(data.get('date'))}</td></tr>
    <tr><th>일시</th><td>{esc(data.get('time'))}</td><th>장소</th><td>{esc(data.get('place'))}</td></tr>
    <tr><th>참석</th><td colspan="3">{esc(participants)}</td></tr>
    <tr><th>안건</th><td colspan="3">{esc(data.get('agenda'))}</td></tr>
  </table>
  <div class="section-title">1. 회의 목적</div>
  <table><tr><td>{esc(data.get('purpose'))}</td></tr></table>
  <div class="section-title">2. 주요 논의내용</div>
  <table class="agenda"><colgroup><col style="width:8%"><col style="width:23%"><col></colgroup><thead><tr><th>연번</th><th>구분</th><th>논의내용</th></tr></thead><tbody>{rows(data.get('discussions', []), 'simple')}</tbody></table>
  <div class="section-title">3. 결정사항</div>
  <table><colgroup><col style="width:8%"><col style="width:27%"><col></colgroup><thead><tr><th>연번</th><th>항목</th><th>내용</th></tr></thead><tbody>{rows(data.get('decisions', []), 'simple')}</tbody></table>
  <div class="section-title">4. 후속조치</div>
  <table class="actions"><colgroup><col style="width:8%"><col style="width:17%"><col style="width:43%"><col style="width:16%"><col style="width:16%"></colgroup><thead><tr><th>연번</th><th>담당</th><th>조치사항</th><th>기한</th><th>비고</th></tr></thead><tbody>{rows(data.get('actions', []), 'actions')}</tbody></table>
  <div class="section-title">5. 확인 필요사항</div>
  <table><tr><td><ol class="plain-list">{checks(data.get('checks', []))}</ol></td></tr></table>
  <div class="page-footer">1 / 2</div>
</section>
<section class="page">
  <div class="doc-no">{esc(data.get('title'))} / 상세 발언록</div>
  <h2>상 세 발 언 록</h2>
  <div class="top-rule"></div>
  <table class="transcript"><colgroup><col style="width:11%"><col style="width:15%"><col></colgroup><thead><tr><th>시간</th><th>발언자</th><th>발언 요지</th></tr></thead><tbody>{rows(data.get('transcript', []), 'transcript')}</tbody></table>
  <div class="section-title">발언자 식별 메모</div>
  <table><tr><td class="small">{esc(data.get('speaker_note'))}</td></tr></table>
  <div class="page-footer">2 / 2</div>
</section>
</body>
</html>"""


def find_browser():
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    for name in ["msedge", "chrome", "chromium"]:
        found = shutil.which(name)
        if found:
            return found
    raise RuntimeError("Chrome or Edge executable not found")


def print_pdf(html_path, pdf_path):
    browser = find_browser()
    url = html_path.resolve().as_uri()
    subprocess.run([
        browser,
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path}",
        url,
    ], check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="minutes JSON path")
    parser.add_argument("--output", required=True, help="output PDF path")
    parser.add_argument("--html", help="optional output HTML path")
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    pdf_path = Path(args.output).resolve()
    html_path = (Path(args.html) if args.html else Path(args.output).with_suffix(".html")).resolve()
    data = json.loads(input_path.read_text(encoding="utf-8"))
    html_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(render_html(data), encoding="utf-8", newline="\n")
    print_pdf(html_path, pdf_path)
    print(f"HTML: {html_path}")
    print(f"PDF: {pdf_path}")


if __name__ == "__main__":
    main()
