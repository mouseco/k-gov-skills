# HWP/HWPX 문서 읽기·변환 가이드

HWP/HWPX/HWPML 문서를 AI가 읽을 수 있는 Markdown 또는 JSON으로 변환하는 스킬입니다. ALIO 내부규정, 공공기관 공시 첨부문서, 공개 HWP 자료를 검토할 때 사용합니다.

## 이 기능으로 할 수 있는 일

- `.hwp`, `.hwpx`, `.hwpml` 문서를 Markdown으로 변환
- 문서 구조를 JSON으로 추출
- 여러 문서를 일괄 변환
- 조항, 표, 제목 구조를 확인해 보고서 근거로 정리
- HWPX 양식 필드 또는 구조 확인 보조

## 기본 도구

이 스킬의 기본 엔진은 `kordoc`입니다.

일회성 변환 예시:

```powershell
npx --yes --package kordoc --package pdfjs-dist kordoc "문서.hwp" -o "문서.md"
```

JSON 추출 예시:

```powershell
npx --yes --package kordoc --package pdfjs-dist kordoc "문서.hwpx" --format json > "문서.json"
```

## ALIO 내부규정과 함께 쓸 때

ALIO 내부규정은 화면에 전문이 바로 보이지 않고 ZIP/HWP/HWPX/PDF 첨부로 제공되는 경우가 많습니다.

권장 흐름:

1. `alio` 스킬로 기관의 내부규정 목록을 조회합니다.
2. 규정 상세에서 첨부파일 번호와 파일명을 확인합니다.
3. ZIP이면 압축을 풀고 최신 시행일 파일을 고릅니다.
4. HWP/HWPX/HWPML이면 이 `hwp` 스킬로 Markdown 또는 JSON으로 변환합니다.
5. 조항 번호, 시행일, 개정 이력, 본문 내용을 확인합니다.

## `hwpx-mouseco`/`hwpxskill`과의 차이

- `hwp`: 기존 HWP/HWPX 문서를 **읽고 변환**합니다.
- `hwpx-mouseco` 또는 로컬 `hwpxskill`: 템플릿과 profile을 기준으로 공공 보고서 HWPX를 **생성**합니다.
- 바이너리 HWP 직접 편집은 이 스킬의 범위가 아닙니다.

## 입력

- 파일 경로: `.hwp`, `.hwpx`, `.hwpml`
- 출력 형식: Markdown 또는 JSON
- 출력 파일 또는 디렉터리

## 출력 확인

- Markdown 파일이 생성되었는지 확인합니다.
- 제목, 조항 번호, 표가 필요한 수준으로 읽히는지 확인합니다.
- JSON 변환 시 `success`, `markdown`, `blocks`, `metadata` 필드를 확인합니다.
- 공공자료 인용 시 원문 파일명, 시행일, 공시 URL을 함께 남깁니다.

## 주의사항

- OCR이 필요한 이미지 기반 문서는 별도 OCR이 필요할 수 있습니다.
- 변환 결과의 표 구조는 원문 레이아웃에 따라 일부 손실될 수 있습니다.
- 공개 저장소에는 실제 내부자료나 개인정보가 포함된 원문 HWP를 커밋하지 않습니다.
- 공개 공시자료라도 대용량 원문 파일은 필요할 때만 별도 보관하고, 저장소에는 스킬과 예시만 둡니다.
