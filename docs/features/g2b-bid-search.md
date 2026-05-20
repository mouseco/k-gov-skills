# 나라장터 입찰공고 검색 가이드

g2b-bid-search는 나라장터 입찰공고 Open API로 용역·물품·공사 공고를 조회해, 공공기관 사업·AI 사업·정보화사업 모니터링에 필요한 핵심 정보를 정리하는 스킬입니다.

## 해주는 일

- 최근 나라장터 입찰공고 검색
- 용역·물품·공사 유형별 조회
- 공고명, 수요기관, 공고기관, 예산, 입찰마감 정리
- 계약방법, 낙찰방법, 개찰일시 확인
- 상세 URL과 첨부 규격서 URL 정리

## 적합한 사용 장면

- "AI 관련 나라장터 공고 찾아줘"
- "정보화사업 용역 최근 공고 모니터링해줘"
- "컨설팅 용역 중 예산 큰 것만 정리해줘"
- "수요기관과 입찰마감 중심으로 보고 싶어"

## 기본 실행

    python -X utf8 skills\\g2b-bid-search\\scripts\\run_g2b_bid_search.py search --query "인공지능" --text

최근 14일 용역 검색:

    python -X utf8 skills\\g2b-bid-search\\scripts\\run_g2b_bid_search.py search --query "정보화" --kind service --days 14 --text

용역·물품·공사 전체 검색:

    python -X utf8 skills\\g2b-bid-search\\scripts\\run_g2b_bid_search.py search --query "AI" --kind all --limit 10 --text

## 인증

공공데이터포털에서 나라장터 입찰공고정보서비스 활용신청 후 받은 인증키를 환경변수 NARAJANGTEO_SERVICE_KEY에 넣습니다.

## 출처

- 공공데이터포털: https://www.data.go.kr/data/15129394/openapi.do
- 나라장터 상세 URL은 API 응답의 bidNtceDtlUrl을 사용합니다.

## 주의사항

- 이 스킬은 조회 전용입니다. 입찰 참가, 투찰, 로그인, 인증서 사용은 하지 않습니다.
- API 결과에 과업 내용 전문이 항상 포함되지는 않습니다. 과업요약은 공고명·분류명·첨부파일명 기준의 1차 판단입니다.
- 첨부파일 내용 분석이 필요하면 상세 URL 또는 첨부 URL을 별도로 열어 확인해야 합니다.
