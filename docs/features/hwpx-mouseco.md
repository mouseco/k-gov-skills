# HWPX 보고서 생성 가이드

공공기관 한글 보고서 양식을 `.hwpx` 상태로 분석하고, 보고서 JSON을 넣어 **원페이퍼·다중페이퍼·장문 보고서**를 생성·검증할 때 쓰는 스킬입니다.

이 기능의 목표는 새 문서를 예쁘게 만드는 것이 아니라, **기존 HWPX 양식의 구조와 스타일을 보존한 채 내용을 안전하게 채우는 것**입니다.

## 이 기능으로 할 수 있는 일

- `.hwpx` 파일을 ZIP/XML 구조로 열어 문단, 표, 스타일, 에셋 확인
- 공개 배포용 프로파일 선택
- 보고서 JSON을 HWPX로 변환
- 원페이퍼, 다중페이퍼, 장문 보고서 생성
- 템플릿의 제목, 작성정보, 본문 위계, 표 구조 보존
- `validate-only`로 패키지, XML, 스타일 참조, 한글 깨짐 점검
- 빈 글머리, 남은 `**` 마크다운 표시, 오래된 Preview 텍스트 확인

## 먼저 알아둘 점

- 이 스킬은 `.hwp` 바이너리 직접 편집용이 아닙니다. 기본 대상은 `.hwpx`입니다.
- 단순 텍스트 치환만 하면 문서 구조가 깨질 수 있습니다.
- 템플릿의 문단, 표, 셀, 글상자, 스타일 참조를 최대한 보존해야 합니다.
- 실제 기관 내부 양식, 직인, 서명, 개인정보가 들어간 HWPX는 공개 저장소에 넣지 않습니다.

## 입력

- 보고서 JSON
- 사용할 프로파일 또는 템플릿 경로
- 제목, 작성정보, 본문 섹션, 표, 참고 문단
- 필요 시 slot map 검토 결과

## 출력

- 최종 `.hwpx` 파일
- 템플릿 inspection 결과
- validate-only 검증 결과
- 남은 레이아웃 위험 또는 수동 확인 필요사항

## 포함 템플릿

- 원페이퍼 보고서
- 다중페이퍼 보고서
- 장문 보고서

## 기본 흐름

1. HWPX 템플릿의 ZIP/XML 구조를 확인합니다.
2. 프로파일 또는 템플릿을 선택합니다.
3. report JSON을 작성하거나 입력받습니다.
4. HWPX를 생성합니다.
5. `validate-only`로 재검증합니다.
6. 필요 시 내부 XML과 `Preview/PrvText.txt`를 함께 확인합니다.
7. 최종 파일을 실제 HWPX 뷰어에서 열어 확인합니다.

## 사용 예시

```powershell
$env:PYTHONUTF8='1'; $env:PYTHONIOENCODING='utf-8'; chcp 65001 > $null
python skills\hwpx-mouseco\scripts\create_hwpx_report.py `
  --input skills\hwpx-mouseco\examples\public_ai_adoption_report.json `
  --template "skills\hwpx-mouseco\templates\붙임1 보고서 양식_배포용_원페이퍼.hwpx" `
  --output output\report.hwpx

python skills\hwpx-mouseco\scripts\create_hwpx_report.py --validate-only output\report.hwpx
```

## 결과 확인 포인트

- 생성된 `.hwpx`가 다시 열리는가
- `content.hpf` manifest와 spine 참조가 맞는가
- `header.xml`과 section XML 참조가 깨지지 않았는가
- 핵심 본문 텍스트가 실제 XML 안에 들어갔는가
- 템플릿의 표, 글머리, 작성정보 위치가 유지됐는가
- `**` 마크다운 표시나 깨진 한글이 남지 않았는가
- `Preview/PrvText.txt`가 오래된 내용을 보여주지 않는가

## 주의할 점

- `BinData`, manifest, spine, style 참조를 누락하면 문서가 열리더라도 신뢰할 수 없습니다.
- 템플릿의 문단 위계를 무시하고 텍스트만 치환하면 실패입니다.
- inspect 단계에서 `Preview/PrvText.txt may not match section text` 경고가 나오면 최종 배포 전 본문 XML과 Preview 텍스트를 함께 확인합니다.
- 공개 배포용으로 정리된 템플릿만 `skills/hwpx-mouseco/templates/` 아래에 둡니다.

## 관련 파일

- `skills/hwpx-mouseco/SKILL.md`
- `skills/hwpx-mouseco/profiles/*.profile.json`
- `skills/hwpx-mouseco/templates/*.hwpx`
- `skills/hwpx-mouseco/scripts/*.py`
- `skills/hwpx-mouseco/references/*.md`
- `skills/hwpx-mouseco/schemas/slot_map.schema.json`
