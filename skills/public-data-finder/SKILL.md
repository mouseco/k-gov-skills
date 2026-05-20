---
name: public-data-finder
description: 공공데이터포털(data.go.kr) 목록개방현황 API로 공공기관이 개방한 파일데이터·오픈API·표준데이터를 키워드, 제공기관, 분류체계 기준으로 검색하고 목록유형, API 유형, 갱신주기, 조회수, 목록 URL, 설명을 출처와 함께 정리한다. Use when the user asks to find public datasets or APIs for a Korean public-sector project, policy report, data-based service idea, or administrative evidence search.
license: See docs/attribution.md
metadata:
  category: data
  locale: ko-KR
  phase: v1
---

# Public Data Finder

## What this skill does

공공데이터포털의 공공데이터활용지원센터_공공데이터포털 목록개방현황 Open API를 조회해, 공공기관이 개방한 데이터셋 후보를 빠르게 찾는다.

기준 데이터:

- data.go.kr 데이터셋: 15062804
- API namespace: 15062804/v1
- 최신 월간 UDDI endpoint는 스크립트가 OAS 문서에서 자동 탐색한다.

## When to use

- "이 사업에 쓸 수 있는 공공데이터 찾아줘"
- "청년 정책 관련 공공데이터 API가 있나?"
- "기관별로 어떤 파일데이터/오픈API를 열고 있는지 찾아줘"
- "데이터셋 이름, 제공기관, 갱신주기, API 여부, 목록 URL을 정리해줘"

## When not to use

- 실제 데이터 본문을 분석해야 하는 경우. 이 스킬은 먼저 목록과 상세 URL을 찾는 용도다.
- 민간 데이터, 뉴스, 통계표 본문, 법령 조문 검색. 각각 다른 전용 스킬을 쓴다.
- 공공데이터포털 활용신청, 로그인, 트래픽 증설 신청 자동화.

## Prerequisites

- Python 3.9+ (stdlib only)
- 공공데이터포털에서 공공데이터활용지원센터_공공데이터포털 목록개방현황 Open API 활용신청
- 환경변수 DATA_GO_KR_API_KEY

## Workflow

1. 사용자 질문에서 핵심 키워드와 기관명을 분리한다.
2. search로 목록명을 우선 검색한다.
3. 필요하면 --org, --category, --list-type API|FILE|STANDARD를 추가한다.
4. 결과에는 목록명, 제공기관, 목록유형, API 유형, 갱신주기, 조회수, 목록 URL, 설명을 포함한다.
5. 후보가 넓으면 조회수와 설명 적합도를 기준으로 5~10개만 추린다.

## Examples

    python -X utf8 skills\\public-data-finder\\scripts\\run_public_data_finder.py search --query "인구" --text
    python -X utf8 skills\\public-data-finder\\scripts\\run_public_data_finder.py search --query "청년" --list-type API --limit 10 --text
    python -X utf8 skills\\public-data-finder\\scripts\\run_public_data_finder.py search --query "장학금" --org "한국장학재단" --json
    python -X utf8 skills\\public-data-finder\\scripts\\run_public_data_finder.py latest --text

상세 API 동작과 주요 컬럼은 references/data-go-kr-list-api.md를 참고한다.

## Done when

- 검색 결과에 공공데이터포털 목록 URL이 포함된다.
- 제공기관, 목록유형, API 유형, 갱신주기, 조회수가 함께 정리된다.
- API가 없거나 결과가 없으면 검색어를 좁히거나 넓히는 다음 검색안을 제시한다.
- 인증키 값은 로그나 답변에 노출하지 않는다.

## Safety notes

- 조회 전용 스킬이다.
- 활용신청, 데이터 수정, 포털 계정 조작은 하지 않는다.
- --dry-run 출력에서도 인증키는 <REDACTED>로 가린다.
