# k-gov-skills

> 한국 공공문서와 HWPX 자동화를 위한 공개 스킬 저장소

`k-gov-skills`는 공공 보고서, 행정 문서, 한글(HWPX) 양식을 AI 작업 흐름 안에서 더 안정적으로 다루기 위한 스킬 모음입니다.

이 저장소는 [`NomaDamas/k-skill`](https://github.com/NomaDamas/k-skill)의 스킬 구조와 문서화 방식을 참고해 만든 **공무원·공공기관 업무 전용 스킬 모음**입니다. 범용 생활·검색 스킬이 아니라, 공공문서 작성, 정책 근거조사, HWPX 보고서 자동화처럼 행정 실무에서 반복되는 작업을 더 안정적으로 처리하는 데 초점을 둡니다.

핵심 목표는 단순 자동화가 아닙니다.  
**문서의 양식은 지키고, 작성 흐름은 줄이고, 결과물은 바로 검토 가능한 HWPX로 만드는 것**입니다.

---

## ✨ 포함된 스킬

| 스킬 | 설명 |
|---|---|
| `official-report-skillset` | 공공기관 공문서·검토보고·계획보고·결과보고·간부보고 초안 작성과 논리 점검을 위한 스킬 |
| `deep-research-pro` | 공문서·정책보고서에 넣을 법령·지침·공식자료·통계·사례 근거를 출처와 함께 조사하는 심층 리서치 스킬 |
| `hwpx-mouseco` | HWPX 보고서 양식을 분석하고, 공개 배포용 프로파일에 맞춰 원페이퍼·다중페이퍼·장문 보고서를 생성하는 스킬 |
| `gov-meeting-brief` | 공공기관 회의 메모·녹취 요약을 회의결과보고, 후속조치 목록, 간부 공유용 브리핑으로 정리하는 스킬 |

---

## 🧩 official-report-skillset

`official-report-skillset`은 공공기관 보고서의 문서 유형, 목차, 개조식 문체, 논리 흐름, 보완 필요사항을 정리하는 작성 스킬입니다.

### 할 수 있는 일

- 검토보고, 계획보고, 결과보고, 간부보고, 회의결과, 동향보고 유형을 판별합니다.
- 문서 유형에 맞는 기본 구조와 작성 기법을 적용합니다.
- 사실, 해석, 권고, 리스크, 후속조치를 구분합니다.
- 필요 시 `deep-research-pro` 방식의 심층 근거조사를 보고서 근거로 연결합니다.

---

## 🔬 deep-research-pro

`deep-research-pro`는 공공기관 보고서에 넣을 공식 근거와 출처 있는 심층조사 메모를 만드는 리서치 스킬입니다.

### 할 수 있는 일

- 주제를 3~5개 연구 질문으로 나눕니다.
- 법령, 지침, 정부·공공기관 공식자료, 통계, 국회·감사·연구기관 보고서, 유사기관 사례를 우선 확인합니다.
- `web_search`, `web_fetch`, `browser`, `pdf`, `korean-law` 도구를 기준으로 조사합니다.
- PDF 도구 실패 시 로컬 다운로드·텍스트 추출 대체 스크립트를 사용합니다.
- Executive Summary, 핵심 쟁점, 한계, 출처 목록을 포함한 `report.md`를 만듭니다.

---

## 🧩 gov-meeting-brief

`gov-meeting-brief`는 회의 메모, 자동 전사, 참석자 발언 요약을 공공기관 회의결과보고와 후속조치 목록으로 정리하는 스킬입니다.

### 할 수 있는 일

- 회의 목적, 안건, 논의 요지, 결정사항을 분리합니다.
- 담당자·기한·후속조치를 실행 단위로 정리합니다.
- 결정사항과 단순 의견을 구분해 감사·보고 리스크를 줄입니다.
- 간부 공유용 5줄 요약과 남은 쟁점을 정리합니다.

---

## 🧩 hwpx-mouseco

`hwpx-mouseco`는 한국 공공기관에서 자주 쓰는 한글 보고서 양식을 안전하게 다루기 위한 HWPX 문서 생성 스킬입니다.

### 할 수 있는 일

- `.hwpx` 파일을 ZIP/XML 구조로 열어 문단, 표, 스타일, 에셋을 확인합니다.
- 기존 양식의 제목, 작성정보, 본문 위계, 표 구조를 최대한 보존합니다.
- 공개 배포용 프로파일을 기준으로 보고서 JSON을 작성하고 HWPX로 변환합니다.
- 생성 후 HWPX 내부 XML, 한글 깨짐, 스타일 참조, 빈 글머리표, 남은 마크다운 표시를 점검합니다.

### 포함된 배포용 양식

- 원페이퍼 보고서
- 다중페이퍼 보고서
- 장문 보고서

---

## 🚀 설치

Codex/OpenClaw 스킬 설치 도구에서 필요한 스킬 경로를 지정합니다.

```text
$skill-installer install https://github.com/mouseco/k-gov-skills/tree/main/skills/official-report-skillset
$skill-installer install https://github.com/mouseco/k-gov-skills/tree/main/skills/deep-research-pro
$skill-installer install https://github.com/mouseco/k-gov-skills/tree/main/skills/hwpx-mouseco
$skill-installer install https://github.com/mouseco/k-gov-skills/tree/main/skills/gov-meeting-brief
```

설치 후에는 새 세션에서 스킬이 인식되도록 Codex/OpenClaw를 다시 시작합니다.

---

## 📁 저장소 구조

```text
docs/
  adding-a-skill.md          새 스킬 추가 표준
  security-and-secrets.md    공개자료·시크릿 취급 기준
  attribution.md             외부·파생 스킬 출처 기록
  features/                  스킬별 사용자·유지보수 문서
scripts/
  validate_skills.py         메타데이터·문서·JSON·Python·HWPX 검증
skills/
  official-report-skillset/
    SKILL.md        공공기관 보고서 작성 규칙
    references/     문서 유형·품질 점검 참고자료
  deep-research-pro/
    SKILL.md        심층 리서치 절차
    scripts/        URL 다운로드, PDF 텍스트 추출, 보고서 검증 도구
  hwpx-mouseco/
    SKILL.md        스킬 사용 규칙
    scripts/        HWPX 분석·생성·검증용 Python 도구
    profiles/       배포용 보고서 프로파일
    templates/      배포용 HWPX 양식
    references/     작성 규칙과 HWPX 구조 참고자료
    examples/       공개 예시 JSON
    schemas/        slot map 검토용 스키마
  gov-meeting-brief/
    SKILL.md        회의결과보고·후속조치 정리 규칙
    references/     결정사항·의견 구분과 민감정보 처리 기준
```

---

## 🧭 스킬 제작 표준

새 스킬을 추가하거나 기존 스킬을 고칠 때는 아래 문서를 기준으로 합니다.

- `docs/adding-a-skill.md` — `SKILL.md` frontmatter, 폴더 구조, feature docs 작성 기준
- `docs/security-and-secrets.md` — 공개 가능한 HWPX·예시·시크릿 기준
- `docs/attribution.md` — 외부·파생 스킬 출처와 수정 범위
- `docs/features/<skill-name>.md` — 스킬별 사용 설명과 실패 모드

---

## 🛡️ 공개 배포 기준

이 저장소에는 공개 가능한 자료만 둡니다.

- 개인·기관 내부용 HWPX 파일은 커밋하지 않습니다.
- 생성 결과물, 임시 압축 해제 폴더, 테스트 산출물은 커밋하지 않습니다.
- 공개 배포용 템플릿과 프로파일만 `skills/hwpx-mouseco/` 아래에 둡니다.
- 리서치 스킬의 테스트 산출물과 다운로드한 원문 PDF는 커밋하지 않습니다.
- 민감한 이름, 이메일, 내부 조직명, 비공개 문서 내용은 포함하지 않습니다.

---

## ✅ 현재 검증 상태

현재 스킬 모음은 아래 명령으로 검증합니다.

```powershell
python -X utf8 scripts\validate_skills.py
```

검증 범위:

- `SKILL.md` frontmatter 표준 확인
- 스킬명과 폴더명 일치 확인
- 스킬별 `docs/features/<skill-name>.md` 존재 확인
- JSON 파싱 확인
- Python 스크립트 컴파일 확인
- HWPX 템플릿 ZIP/XML 구조 확인
- 공개 저장소에 부적절한 민감 문자열 기본 검색

현재 확인된 상태:

- `official-report-skillset` SKILL.md 및 references 포함
- `deep-research-pro` OpenClaw 맞춤 SKILL.md, 출처 기록, 보조 스크립트 포함
- `hwpx-mouseco` 배포용 HWPX 템플릿 3종, 프로파일 3종, 예시 JSON 포함
- `gov-meeting-brief` 회의결과보고 정리 규칙과 feature 문서 포함
- `python -X utf8 scripts\validate_skills.py` 통과
- `hwpx-mouseco` 원페이퍼 생성 및 validate-only smoke test 통과

---

## 📌 사용 방향

이 스킬은 “문서를 대신 써주는 도구”라기보다, **공공문서의 양식과 검증 절차를 AI 작업 흐름 안에 고정하는 도구**입니다.

좋은 자동화는 문서를 많이 찍어내는 것이 아니라, 사람이 검토할 수 있는 구조로 일관되게 만들어 주는 것입니다.
