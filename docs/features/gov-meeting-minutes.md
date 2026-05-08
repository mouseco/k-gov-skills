# gov-meeting-minutes

`gov-meeting-minutes`는 공공기관 회의 메모와 녹취록을 담백한 공문서형 회의록 PDF로 만드는 스킬이다.

## 해결하는 문제

ClovaNote 등으로 만든 전사본은 발언이 길고, 익명 발언자와 반복어가 섞여 있어 바로 보관하거나 공유하기 어렵다. 이 스킬은 회의 내용을 1쪽 회의록과 2쪽 이후 상세 발언록으로 나누어 정리하고, HTML 기반 PDF로 산출한다.

## 언제 쓰는지

- 회의 녹취록을 공식 회의록 형태로 정리할 때
- 회의 요약본과 상세 발언록을 함께 남겨야 할 때
- `참석자 1`, `참석자 2`처럼 익명 발언자가 있어 이름·직함 확인이 필요한 때
- 보고서가 아니라 담백한 회의 기록물이 필요할 때
- 표와 선 중심의 공문서형 PDF가 필요할 때

## 입력과 출력

입력:

- 회의 메모
- ClovaNote 전사
- 참석자별 발언 기록
- 시간 정보가 있는 녹취 요약

출력:

- A4 PDF 회의록
- 선택적으로 HTML 원본

기본 구성:

1. 회의록 요약본
2. 상세 발언록
3. 발언자 식별 메모

## 기본 workflow

1. 회의명, 일시, 참석자, 안건을 추출한다.
2. 익명 발언자가 있으면 주요 발언 취지를 설명하고 사용자에게 이름·직함을 확인한다.
3. 회의 목적, 주요 논의내용, 결정사항, 후속조치, 확인 필요사항을 정리한다.
4. 시간순 상세 발언록을 만든다.
5. 구조화 JSON을 작성한다.
6. `scripts/render_minutes_pdf.py`로 HTML과 PDF를 생성한다.
7. PDF를 실제 렌더링해 페이지 수, 하단 회색 박스, 불필요한 페이지 분리 여부를 확인한다.

## 사용 예시

```text
이 ClovaNote 녹취록으로 회의록 PDF 만들어줘. 참석자 1, 2가 누군지는 내가 알려줄게.
```

```text
이 회의 메모를 공문서형 회의록으로 정리하고, 뒤에 상세 발언록도 붙여줘.
```

## 렌더링 예시

```powershell
python -X utf8 skills\gov-meeting-minutes\scripts\render_minutes_pdf.py `
  --input skills\gov-meeting-minutes\examples\ai-demand-meeting-minutes.sample.json `
  --output tmp\gov-meeting-minutes-sample.pdf `
  --html tmp\gov-meeting-minutes-sample.html
```

## 실패 모드와 보완 방법

- 발언자를 알 수 없으면 사용자에게 확인하고, 모르면 익명 표기를 유지한다.
- 회의록이 보고서처럼 화려해지면 표와 선 중심으로 되돌린다.
- 상세 발언록이 불필요하게 여러 페이지로 갈라지면 글자 크기와 행 간격을 조정한다.
- PDF 하단에 빈 회색 박스가 생기면 화면용 배경과 인쇄용 배경을 분리하고, 실제 PDF 렌더링으로 확인한다.
- 원문 의미가 불명확하면 단정하지 않고 `확인 필요`로 표시한다.

## 보안·민감정보 주의사항

실제 회의록, 실명, 내부 문서명, 개인정보, 민감정보가 포함된 원문은 공개 저장소 예시로 넣지 않는다. 공개 예시는 가상 이름과 공개 가능한 업무 맥락만 사용한다.

## 관련 파일 구조

```text
skills/gov-meeting-minutes/
  SKILL.md
  scripts/render_minutes_pdf.py
  references/minutes-writing-guide.md
  examples/ai-demand-meeting-minutes.sample.json
docs/features/gov-meeting-minutes.md
```
