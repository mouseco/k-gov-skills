---
name: hwpx-mouseco
description: 한국 공공문서용 HWPX(.hwpx) 보고서 양식을 분석·작성·검증할 때 사용한다. 공개 배포용 원페이퍼, 다중페이퍼, 장문 보고서 프로파일과 템플릿을 기준으로 report JSON을 만들고, HWPX 내부 XML을 보존하면서 문서를 생성한다. 레거시 .hwp 바이너리 파일은 직접 편집하지 않는다.
license: MIT
metadata:
  category: documents
  locale: ko-KR
  phase: v1
---

# hwpx-mouseco

`hwpx-mouseco`는 한국 공공기관에서 자주 쓰는 한글 보고서 양식을 안전하게 다루기 위한 HWPX 문서 생성 스킬입니다.

목표는 단순 텍스트 치환이 아닙니다. **양식의 문단 위계, 표, 스타일, 첨부 에셋을 보존하면서 보고서다운 구조를 가진 HWPX 파일을 만드는 것**입니다.

---

## 핵심 원칙

- `.hwpx`만 지원합니다. `.hwp` 파일은 먼저 HWPX로 변환한 뒤 작업합니다.
- 사용자가 제공한 양식은 민감자료일 수 있으므로 공개 저장소에 복사하거나 커밋하지 않습니다.
- 기존 문서 구조와 스타일을 우선 보존합니다.
- 표 구조, section 수, style ID, `BinData`, package manifest를 임의로 바꾸지 않습니다.
- XML은 UTF-8 기준으로 읽고 씁니다. 깨진 한글, replacement character, mojibake를 그대로 재사용하지 않습니다.
- 하위 불릿 `ㅇ`, `-`에는 괄호형 키워드를 기계적으로 붙이지 않습니다. 기본은 자연스러운 일반 문장입니다.
- JSON/content에서 `**굵게**` 표시는 꼭 필요한 핵심어에만 짧게 사용합니다.

---

## 기본 작업 흐름

### 1. 템플릿 확인

- 파일 확장자가 `.hwpx`인지 확인합니다.
- HWPX를 ZIP 패키지로 열어 `Contents/header.xml`, `Contents/content.hpf`, `Contents/section*.xml`을 확인합니다.
- 문단, 표, 자리표시자, 반복 블록, 스타일 참조, 이미지·첨부 에셋을 파악합니다.

### 2. 실행 경로 선택

- 단순 치환이면 기존 `<hp:t>` 텍스트 노드를 바꿔 재압축합니다.
- 새로운 양식이면 `inspect → slot map draft → human review → compile → QA` 순서로 갑니다.
- 이 저장소에 포함된 공개 배포용 양식이면 먼저 `profiles/`의 해당 프로파일을 읽고, 프로파일의 `template_file`이 가리키는 `templates/` 파일을 사용합니다.
- 페이지 렌더링, 필드 동작, 편집기 수준 조작이 꼭 필요하면 XML 직접 편집 대신 로컬 HWP 자동화 경로를 검토하되, 위험과 한계를 먼저 설명합니다.

### 3. 내용 작성

보고서는 문서 목적에 맞춰 다음 흐름을 선택합니다.

```text
배경/현황 → 문제/필요성 → 기본방향 → 추진과제 → 관리방안/기대효과 → 향후 조치
```

문체는 공공 보고서식 개조식을 기본으로 합니다.

- `~함`, `~필요`, `~예정`, `~가능`, `~곤란`, `~우려`처럼 간결하게 씁니다.
- 불필요한 마침표와 장황한 설명을 줄입니다.
- 원페이퍼는 실제 한 페이지 분량을 최우선 제약으로 봅니다.
- 장문 보고서는 장 제목, 하위 항목, 표, 참고 문단의 위계를 분명히 둡니다.

### 4. 검증

생성 후 반드시 확인합니다.

- HWPX가 정상 ZIP으로 열리는지
- 주요 XML이 UTF-8로 파싱되는지
- `content.hpf` manifest/spine이 맞는지
- `header.xml`의 스타일 참조가 깨지지 않았는지
- 한글이 깨지지 않았는지
- `**` 마크다운 표시가 남지 않았는지
- 빈 글머리표, stale `lineSegArray`, 누락된 에셋이 없는지

---

## 포함 파일

### 프로파일

- `profiles/distribution_onepager.profile.json`  
  배포용 원페이퍼 보고서 기준
- `profiles/distribution_multipage.profile.json`  
  배포용 다중페이퍼 보고서 기준
- `profiles/distribution_longform.profile.json`  
  배포용 장문 보고서 기준
- `profiles/profile.schema.json`  
  프로파일 작성 기준 문서

### 템플릿

- `templates/붙임1 보고서 양식_배포용_원페이퍼.hwpx`
- `templates/붙임1 보고서 양식_배포용_다중페이퍼.hwpx`
- `templates/붙임2 장문 보고서 양식_(가)_배포용.hwpx`

### 스크립트

- `scripts/inspect_hwpx.py`  
  HWPX 구조를 분석하고 inspection 결과를 만듭니다.
- `scripts/build_slot_map_draft.py`  
  분석 결과를 바탕으로 slot map 초안을 만듭니다.
- `scripts/compile_from_slot_map.py`  
  검토된 slot map과 report JSON을 이용해 HWPX를 생성합니다.
- `scripts/create_hwpx_report.py`  
  프로파일 기반 보고서 생성과 HWPX 검증을 수행합니다.

---

## 사용 예시

PowerShell에서는 한글 경로와 출력 깨짐을 줄이기 위해 UTF-8 환경을 먼저 잡습니다.

```powershell
$env:PYTHONUTF8='1'; $env:PYTHONIOENCODING='utf-8'; chcp 65001 > $null
```

템플릿 분석:

```powershell
python scripts/inspect_hwpx.py "templates\붙임1 보고서 양식_배포용_원페이퍼.hwpx" --out-dir output\onepager_inspection
```

보고서 생성:

```powershell
python scripts/create_hwpx_report.py --input examples\public_ai_adoption_report.json --template "templates\붙임1 보고서 양식_배포용_원페이퍼.hwpx" --output output\report.hwpx
```

생성물 검증:

```powershell
python scripts/create_hwpx_report.py --validate-only output\report.hwpx
```

---

## 완료 기준

작업은 다음 조건을 만족해야 끝난 것으로 봅니다.

- 최종 산출물이 `.hwpx` 파일임
- 요청한 제목, 작성정보, 본문, 표, 참고 문단이 반영됨
- 기존 스타일과 표 구조가 유지됨
- HWPX 내부 XML 검증을 통과함
- 한글 깨짐이 없음
- 남은 `**` 마크다운 표시가 없음
- 건너뛴 검증이나 남은 레이아웃 위험이 있으면 사용자에게 명확히 보고함
