---
name: g2b-bid-search
description: 나라장터(g2b.go.kr) 입찰공고 Open API로 용역·물품·공사 공고를 검색하고 공고명, 수요기관, 공고기관, 추정가격·배정예산, 입찰마감, 개찰일시, 계약방법, 낙찰방법, 첨부 규격서 URL, 상세 URL을 정리한다. Use when the user asks to monitor Korean public procurement bids, AI/software/service tenders, consulting opportunities, or public-sector procurement notices.
license: See docs/attribution.md
metadata:
  category: procurement
  locale: ko-KR
  phase: v1
---

# G2B Bid Search

## What this skill does

나라장터 입찰공고 목록 API로 최근 입찰공고를 조회하고, 공공기관 실무자가 빠르게 판단할 수 있는 필드만 추려 정리한다.

지원 유형:

- 용역: getBidPblancListInfoServc
- 물품: getBidPblancListInfoThng
- 공사: getBidPblancListInfoCnstwk

## When to use

- "AI 사업 입찰공고 찾아줘"
- "정보화사업 용역 공고 모니터링해줘"
- "나라장터에서 최근 컨설팅 용역 찾아줘"
- "수요기관, 예산, 입찰마감, 첨부파일 URL까지 정리해줘"

## Prerequisites

- Python 3.9+ (stdlib only)
- 공공데이터포털 나라장터 입찰공고정보서비스 활용신청
- 환경변수 NARAJANGTEO_SERVICE_KEY

## Workflow

1. 기본은 용역 검색이다. AI, 컨설팅, 정보화사업은 보통 용역에 있다.
2. 물품·공사까지 함께 보려면 --kind all을 쓴다.
3. 조회 기간은 기본 최근 7일이다. 긴 모니터링은 --days 또는 --from-date/--to-date로 조정한다.
4. 키워드는 API 조회 후 공고명, 수요기관, 공고기관, 분류명에서 한 번 더 필터링한다.
5. 결과에는 상세 URL과 첨부 규격서 URL을 함께 둔다.

## Examples

    python -X utf8 skills\\g2b-bid-search\\scripts\\run_g2b_bid_search.py search --query "인공지능" --text
    python -X utf8 skills\\g2b-bid-search\\scripts\\run_g2b_bid_search.py search --query "정보화" --kind service --days 14 --text
    python -X utf8 skills\\g2b-bid-search\\scripts\\run_g2b_bid_search.py search --query "서버" --kind all --limit 10 --json
    python -X utf8 skills\\g2b-bid-search\\scripts\\run_g2b_bid_search.py search --query "AI" --dry-run

상세 API 필드와 출력 기준은 references/g2b-bid-api.md를 참고한다.

## Done when

- 공고명, 수요기관, 예산 또는 추정가격, 입찰마감, 상세 URL이 정리된다.
- 첨부 규격서 URL이 있으면 함께 표시된다.
- 결과가 없으면 기간을 늘리거나 키워드를 바꾸는 다음 검색안을 제시한다.
- 인증키 값은 로그나 답변에 노출하지 않는다.

## Safety notes

- 조회 전용 스킬이다.
- 입찰 참가, 투찰, 로그인, 인증서 사용, 첨부 다운로드 자동화는 하지 않는다.
- --dry-run 출력에서도 인증키는 <REDACTED>로 가린다.
