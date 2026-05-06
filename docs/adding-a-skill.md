# k-gov-skills 새 스킬 추가 가이드

이 문서는 `k-gov-skills`에 새 스킬을 추가하거나 기존 스킬을 고칠 때 따르는 표준이다. 기준은 `NomaDamas/k-skill`의 스킬 제작 방식에서 가져오되, 공공문서·HWPX·정책 리서치 저장소 특성에 맞게 좁혀 적용한다.

## 1. 스킬의 기본 구조

모든 스킬은 `skills/<skill-name>/` 아래에 둔다.

```text
skills/<skill-name>/
  SKILL.md          # 필수. 에이전트 실행 지침
  references/       # 선택. 필요할 때 읽는 상세 지식
  scripts/          # 선택. 반복·검증·변환용 코드
  examples/         # 선택. 공개 가능한 예시 입력
  schemas/          # 선택. JSON/slot map 등 검증 기준
  templates/        # 선택. 공개 배포 가능한 양식 파일
```

## 2. SKILL.md frontmatter 표준

모든 `SKILL.md`는 YAML frontmatter로 시작한다.

```yaml
---
name: my-skill
description: 사용 시점과 수행 작업을 한 문장으로 구체적으로 설명한다.
license: MIT
metadata:
  category: documents
  locale: ko-KR
  phase: v1
---
```

필수 기준:

- `name`은 폴더명과 정확히 일치해야 한다.
- `description`에는 **무엇을 하는지**와 **언제 써야 하는지**를 함께 적는다.
- `license`는 원칙적으로 `MIT`를 사용한다.
- 외부 스킬을 수정·파생한 경우 `license`에 `See docs/attribution.md`를 쓰고, 출처와 수정 범위를 별도로 기록한다.
- `metadata.locale`은 한국 공공문서 기본값인 `ko-KR`을 사용한다.
- `metadata.phase`는 안정 배포 가능하면 `v1`, 실험성이 크면 `v0.x` 또는 `v1.5`로 둔다.

권장 category:

- `documents`: 공문서·HWPX·보고서 작성
- `research`: 출처 조사·정책 리서치
- `legal`: 법령·규정 중심 조사
- `utility`: 보조 유틸리티

## 3. SKILL.md 본문 작성 원칙

- 에이전트가 바로 실행할 핵심 절차만 남긴다.
- 긴 설명, 세부 기준, 예시는 `references/`나 `docs/features/`로 분리한다.
- 공공문서 스킬은 사실·해석·권고·리스크·후속조치를 구분하도록 한다.
- 실행형 스킬은 입력, 출력, 완료 기준, 실패 모드를 명확히 적는다.
- Windows/OpenClaw 경로와 UTF-8 실행 조건을 필요한 곳에만 적는다.

## 4. 스킬별 feature docs

새 스킬에는 가능하면 아래 문서를 함께 둔다.

```text
docs/features/<skill-name>.md
```

feature docs에는 사용자와 유지보수자를 위한 내용을 넣는다.

- 해결하는 문제
- 언제 쓰는지
- 입력과 출력
- 기본 workflow
- 사용 예시
- 실패 모드와 보완 방법
- 보안·민감정보 주의사항
- 관련 파일 구조

`SKILL.md`는 실행 지침이고, `docs/features/*.md`는 설명서다. 둘을 혼동하지 않는다.

## 5. 공공문서·HWPX 자료 공개 기준

- 실제 기관 내부문서, 개인명, 이메일, 문서번호, 내부 조직명은 공개 저장소에 넣지 않는다.
- HWPX 템플릿은 공개 배포용으로 정리한 파일만 둔다.
- `test-fixtures/private/`, `tmp/`, 생성 결과물, 압축 해제 폴더는 커밋하지 않는다.
- 예시는 가상 기관·가상 주제·공개 가능한 표현만 사용한다.

자세한 기준은 `docs/security-and-secrets.md`를 따른다.

## 6. 검증 기준

수정 후 최소한 아래를 실행한다.

```powershell
python -X utf8 scriptsalidate_skills.py
```

검증 범위:

- `SKILL.md` 존재 여부
- frontmatter 필수값
- `name`과 폴더명 일치
- `docs/features/<skill>.md` 존재 여부
- JSON 파싱
- Python compile
- HWPX ZIP/XML 구조 점검
- 민감 문자열 기본 검색

## 7. 외부·파생 스킬 주의

외부 스킬을 가져와 수정한 경우에는 다음을 지킨다.

- 원 출처와 설치 버전을 `docs/attribution.md`에 적는다.
- 수정 범위와 이 저장소에서의 배포 의도를 분리해 설명한다.
- 원저작권이나 라이선스를 임의로 덮어쓰지 않는다.
- 외부·파생 스킬을 이 저장소의 순수 창작물처럼 표현하지 않는다.
