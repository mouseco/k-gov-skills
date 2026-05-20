---
name: national-assembly-tracker
description: 열린국회정보 Open API와 국회 공식 시스템으로 특정 키워드 관련 법률안·의안 진행상태를 검색하고 제안일, 소관위원회, 처리결과, 대표발의자, 공동발의자, 상세 의안정보 링크, 회의록·입법예고 확인 링크를 정리한다. Use when the user asks to track Korean National Assembly bills, legislation changes, committee discussion clues, or public-sector regulatory impact by keyword.
license: See docs/attribution.md
metadata:
  category: law
  locale: ko-KR
  phase: v1
---

# National Assembly Tracker

## What this skill does

열린국회정보 의안 Open API로 키워드 관련 법률안을 검색하고, 공공기관 실무자가 법령 변화 가능성을 빠르게 볼 수 있게 정리한다.

기본 API:

- 열린국회정보 국회의원 발의법률안
- endpoint id: nzmimeepazxkubdpn
- API URL: https://open.assembly.go.kr/portal/openapi/nzmimeepazxkubdpn

## When to use

- "인공지능 관련 국회 법안 진행상태 찾아줘"
- "학자금, 청년, 고용 관련 법안 변화 감지해줘"
- "상임위, 제안일, 발의자, 처리결과 중심으로 정리해줘"
- "공공기관 업무에 영향 줄 법령 변화가 있나?"

## Prerequisites

- Python 3.9+ (stdlib only)
- 열린국회정보 Open API 인증키
- 환경변수 OPEN_ASSEMBLY_API_KEY

## Workflow

1. bills 명령으로 법률안 목록을 검색한다.
2. 기본 국회 대수는 22대다. 필요하면 --age로 바꾼다.
3. 결과에서 법안명, 제안일, 소관위원회, 처리결과, 대표발의자, 상세 링크를 확인한다.
4. 회의록과 입법예고까지 필요하면 출력된 공식 확인 링크를 열어 같은 키워드로 추가 확인한다.
5. 공공기관 영향 판단은 통과 여부보다 소관위원회, 제안이유, 시행 의무 가능성, 기관 업무 연관성을 기준으로 정리한다.

## Examples

    python -X utf8 skills\\national-assembly-tracker\\scripts\\run_national_assembly_tracker.py bills --query "인공지능" --text
    python -X utf8 skills\\national-assembly-tracker\\scripts\\run_national_assembly_tracker.py bills --query "학자금" --age 22 --limit 10 --json
    python -X utf8 skills\\national-assembly-tracker\\scripts\\run_national_assembly_tracker.py links --query "청년" --text
    python -X utf8 skills\\national-assembly-tracker\\scripts\\run_national_assembly_tracker.py bills --query "고용" --dry-run

상세 필드와 공식 확인 경로는 references/assembly-openapi.md를 참고한다.

## Done when

- 법안명, 제안일, 소관위원회, 처리결과, 대표발의자, 상세 링크가 정리된다.
- 회의록·입법예고 확인이 필요한 경우 공식 시스템 링크를 함께 둔다.
- 결과가 많으면 최신 제안일과 업무 관련도 기준으로 우선순위를 붙인다.
- 인증키 값은 로그나 답변에 노출하지 않는다.

## Safety notes

- 조회 전용 스킬이다.
- 입법 의견 제출, 로그인, 본인인증, 민원 제출 자동화는 하지 않는다.
- --dry-run 출력에서도 인증키는 <REDACTED>로 가린다.
