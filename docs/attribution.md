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

## mouseco 작성 스킬

아래 스킬은 이 저장소의 공공문서 자동화 목적에 맞춰 작성·정리한 스킬이다.

- `official-report-skillset`
- `hwpx-mouseco`
- `gov-meeting-brief`

단, 각 스킬이 참조하는 공개 프로젝트, 표준, 문서 포맷, 오픈소스 도구의 권리는 각 원 출처에 있다.
