# 공공데이터포털 데이터셋 검색 가이드

public-data-finder는 공공데이터포털에 개방된 파일데이터·오픈API·표준데이터 목록을 검색해, 공공기관 실무자가 사업·보고서·서비스 기획에 쓸 수 있는 데이터 후보를 찾는 스킬입니다.

## 해주는 일

- 키워드로 공공데이터포털 목록 검색
- 제공기관, 분류체계, 목록유형 기준 필터링
- 파일데이터/API/표준데이터 여부 확인
- API 유형, 갱신주기, 신청가능 트래픽, 조회수 확인
- 공공데이터포털 상세 URL 정리

## 적합한 사용 장면

- "이 정책 사업에 쓸 만한 공공데이터가 있나?"
- "청년, 고용, 인구, 장학금 관련 API 찾아줘"
- "한국장학재단이나 교육부가 개방한 데이터 목록 정리해줘"
- "파일데이터 말고 오픈API 위주로 찾아줘"

## 기본 실행

    python -X utf8 skills\\public-data-finder\\scripts\\run_public_data_finder.py search --query "인구" --text

기관 필터:

    python -X utf8 skills\\public-data-finder\\scripts\\run_public_data_finder.py search --query "장학금" --org "한국장학재단" --text

API만 검색:

    python -X utf8 skills\\public-data-finder\\scripts\\run_public_data_finder.py search --query "청년" --list-type API --limit 10 --text

최신 월간 endpoint 확인:

    python -X utf8 skills\\public-data-finder\\scripts\\run_public_data_finder.py latest --text

## 인증

공공데이터포털에서 공공데이터활용지원센터_공공데이터포털 목록개방현황 Open API 활용신청 후 받은 인증키를 환경변수 DATA_GO_KR_API_KEY에 넣습니다.

이 스킬은 인증키를 출력하지 않습니다. --dry-run에서도 <REDACTED>로 가립니다.

## 출처

- 공공데이터포털 데이터 상세: https://www.data.go.kr/data/15062804/fileData.do
- OAS 문서: https://infuser.odcloud.kr/oas/docs?namespace=15062804/v1

## 주의사항

- 검색 대상은 공공데이터포털의 목록 메타데이터입니다. 실제 데이터 본문 분석은 상세 URL 또는 개별 API를 다시 확인해야 합니다.
- 목록명 검색이 기본이므로, 결과가 적으면 더 넓은 키워드로 다시 검색합니다.
- 여러 조건을 동시에 넣으면 결과가 급격히 줄 수 있습니다.
