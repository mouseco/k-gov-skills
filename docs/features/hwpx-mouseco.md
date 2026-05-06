# hwpx-mouseco

## 해결하는 문제

한국 공공기관 HWPX 보고서 양식을 분석하고, 공개 배포용 프로파일과 템플릿을 기준으로 원페이퍼·다중페이퍼·장문 보고서를 생성·검증하는 스킬이다.

## 언제 쓰는가

- HWPX 양식 구조 분석
- 공개 배포용 보고서 템플릿에 내용 채우기
- report JSON을 HWPX로 변환
- HWPX 내부 XML, 스타일, 표, 미리보기, 한글 깨짐 검증
- `.hwp`가 아니라 `.hwpx` 기반 문서 자동화가 필요할 때

## 입력

- 보고서 JSON
- 사용할 프로파일 또는 템플릿 경로
- 제목, 작성정보, 본문 섹션, 표, 참고 문단
- 필요 시 slot map 검토 결과

## 출력

- 최종 `.hwpx` 파일
- 템플릿 inspection 결과
- 검증 결과 또는 남은 레이아웃 위험

## 기본 workflow

1. HWPX 템플릿 ZIP/XML 구조 확인
2. 프로파일 선택
3. report JSON 작성 또는 수신
4. HWPX 생성
5. validate-only 검증
6. 필요 시 내부 XML과 Preview 텍스트 확인

## 포함 템플릿

- 원페이퍼 보고서
- 다중페이퍼 보고서
- 장문 보고서

## 사용 예시

```powershell
$env:PYTHONUTF8='1'; $env:PYTHONIOENCODING='utf-8'; chcp 65001 > $null
python skills\hwpx-mouseco\scripts\create_hwpx_report.py --input skills\hwpx-mouseco\examples\public_ai_adoption_report.json --template "skills\hwpx-mouseco	emplates\붙임1 보고서 양식_배포용_원페이퍼.hwpx" --output outputeport.hwpx
python skills\hwpx-mouseco\scripts\create_hwpx_report.py --validate-only outputeport.hwpx
```

## 관련 파일

- `skills/hwpx-mouseco/SKILL.md`
- `skills/hwpx-mouseco/profiles/*.profile.json`
- `skills/hwpx-mouseco/templates/*.hwpx`
- `skills/hwpx-mouseco/scripts/*.py`
- `skills/hwpx-mouseco/references/*.md`
- `skills/hwpx-mouseco/schemas/slot_map.schema.json`

## 실패 모드

- `.hwp` 바이너리를 직접 편집하려 함
- `BinData`, manifest, spine, style 참조를 누락함
- 템플릿의 문단 위계를 무시하고 텍스트만 치환함
- `Preview/PrvText.txt`가 본문과 달라 미리보기가 오래된 내용을 보임
- `**` 마크다운 표시나 깨진 한글이 남음

## 검증 메모

현재 배포용 HWPX 템플릿은 ZIP/XML 구조 검증을 통과한다. 다만 inspect 단계에서 `Preview/PrvText.txt may not match section text` 경고가 나올 수 있으므로, 최종 배포물에서는 본문 XML과 Preview 텍스트를 함께 확인한다.

## 보안 주의

실제 기관 문서, 내부 서식, 직인·서명·개인정보가 들어간 HWPX를 공개 저장소에 넣지 않는다. 공개 배포용으로 정리된 템플릿만 사용한다.
