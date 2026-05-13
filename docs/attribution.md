# Attribution and Origin Notes

이 문서는 `k-gov-skills` 안에 포함된 외부·파생 스킬의 출처와 수정 범위를 기록한다.

## deep-research-pro

- 성격: 외부 스킬을 Windows/OpenClaw 공공문서 리서치 환경에 맞게 조정한 파생·적응본
- 확인된 설치 출처: ClawHub `deep-research-pro`
- 확인된 설치 버전: `1.0.2`
- 로컬 기준 원본 위치: `C:\Users\mouse\.openclaw\workspace\skills\deep-research-pro`
- k-gov 저장소 반영 성격: 공공기관 보고서 근거조사용 OpenClaw Edition

### 주요 수정 방향

- `/home/clawdbot` 계열 Linux/DDG 경로 제거
- Windows/OpenClaw 작업 경로 기준으로 재작성
- `web_search`, `web_fetch`, browser/PDF/korean-law 도구 사용 기준 명시
- 공공기관 정책·법령·지침·통계·공식자료 우선순위 보강
- 보고서 산출물 형식과 검증 스크립트 기준 보강

### 라이선스 주의

`deep-research-pro`는 mouseco의 순수 창작 스킬로 표시하지 않는다. 원저작권과 upstream 라이선스 조건은 원 출처에 남아 있으며, 이 저장소의 문서는 OpenClaw 공공문서 업무에 맞춘 적응본임을 명시한다.

## transport-receipt-collector

- 성격: `NomaDamas/k-skill`의 `hipass-receipt` 설계와 구현 흐름을 참고해 공공기관 출장·여비 정산 증빙 수집 목적에 맞게 재구성한 파생·적응본
- 확인된 원본 위치: `NomaDamas/k-skill` 저장소의 `hipass-receipt/`
- 참고 구현 위치: `NomaDamas/k-skill` 저장소의 `packages/hipass-receipt/`
- k-gov 저장소 반영 성격: 하이패스 영수증을 PDF와 PNG 증빙 파일로 정리하는 provider 중심 스킬

### 주요 수정 방향

- 범용 하이패스 영수증 보조에서 출장·여비 정산 증빙 수집으로 목적을 좁힘
- 하이패스 외 코레일·SRT 확장을 위한 provider 구조 추가
- PDF와 PNG 동시 산출 규칙 추가
- ID/PW 자동 로그인은 선택 provider 후보로만 두고, 추가 본인확인 자동 통과는 공개 스킬 범위 밖으로 명시

### 라이선스 주의

원 `hipass-receipt`의 MIT 라이선스와 출처를 존중한다. 이 저장소의 문서는 공공기관 정산 업무에 맞춘 적응본이며, 원 구현의 권리는 원 출처에 있다.

## read-hwp

- 성격: `NomaDamas/k-skill` 원본을 공공기관 문서 검토 흐름에 필요해 가져와 일부만 가공한 파생·적응본
- 확인된 로컬 원본 위치: `C:\Users\mouse\.agents\skills\hwp`
- k-gov 저장소 반영 이름: `read-hwp`
- k-gov 저장소 반영 성격: ALIO 내부규정, 공공기관 첨부 HWP/HWPX 문서를 Markdown/JSON으로 읽기 위한 보조 스킬

### 주요 수정 방향

- 공개 저장소용 feature 문서 추가
- ALIO 내부규정 ZIP/HWP/HWPX 첨부 확인 흐름과 연결
- `hwpx-mouseco`/로컬 `hwpxskill`의 HWPX 생성 역할과 구분

### 라이선스 주의

원 스킬과 `kordoc` 등 사용 도구의 라이선스와 출처를 존중한다. 이 저장소의 문서는 공공기관 공개문서 읽기·검토 업무에 맞춘 배포용 정리본이다.

## korean-law-search

- 성격: `NomaDamas/k-skill` 원본을 공공기관 법령 근거조사에 필요해 가져와 일부만 가공한 파생·적응본
- 확인된 로컬 원본 위치: `C:\Users\mouse\.agents\skills\korean-law-search`
- k-gov 저장소 반영 이름: `korean-law-search`
- k-gov 저장소 반영 성격: 국가법령정보센터/법제처 API 계열, `korean-law-mcp`, 법망 fallback을 활용해 법령·조문·판례·해석례·자치법규를 확인하는 보조 스킬

### 주요 수정 방향

- 공개 저장소용 feature 문서 추가
- 공공기관 보고서 법령 근거조사 흐름에 맞춘 설명 추가
- ALIO 내부규정과 국가법령정보센터 공공기관 규정의 범위 차이 주의사항 명시

### 라이선스 주의

원 스킬, `korean-law-mcp`, 법제처 Open API, 법망 등 사용 도구·서비스의 라이선스와 이용 조건을 존중한다. 이 저장소의 문서는 공공기관 공개 법령 근거조사 업무에 맞춘 배포용 정리본이다.

## mouseco 작성 스킬

아래 스킬은 이 저장소의 공공문서 자동화 목적에 맞춰 작성·정리한 스킬이다.

- `official-report-skillset`
- `hwpx-mouseco`
- `gov-meeting-brief`

단, 각 스킬이 참조하는 공개 프로젝트, 표준, 문서 포맷, 오픈소스 도구의 권리는 각 원 출처에 있다.
