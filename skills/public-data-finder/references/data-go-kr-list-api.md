# 공공데이터포털 목록개방현황 API 참고

## Source

- 데이터 상세: https://www.data.go.kr/data/15062804/fileData.do
- OAS 문서: https://infuser.odcloud.kr/oas/docs?namespace=15062804/v1
- Base URL: https://api.odcloud.kr/api
- Namespace: 15062804/v1

## Endpoint selection

이 데이터셋은 월별 UDDI endpoint가 누적된다. 예를 들어 공공데이터활용지원센터_공공데이터포털 목록개방현황_20260430처럼 날짜가 붙는다.

스크립트는 OAS 문서의 paths에서 목록개방현황_YYYYMMDD 패턴을 찾고 가장 최신 날짜의 path를 선택한다. 2026-05-20 확인 기준 최신 path는 다음과 같았다.

    /15062804/v1/uddi:27a52f84-d64f-438d-bc59-e4f705ebd386

하드코딩하지 말고 OAS에서 최신 endpoint를 고른다. 단, OAS 장애 시를 대비해 위 path를 fallback으로 둔다.

## Authentication

공공데이터포털 활용신청 후 받은 인증키를 serviceKey query parameter로 전달한다.

    serviceKey=<DATA_GO_KR_API_KEY>

ODCLOUD의 일부 문서는 Authorization: Infuser 방식을 언급하지만, 이 목록개방현황 API는 serviceKey 방식으로 검증했다.

## Common parameters

- page: 1부터 시작
- perPage: 페이지당 결과 수
- serviceKey: 공공데이터포털 인증키
- cond[목록명::LIKE]: 목록명 부분검색
- cond[제공기관::LIKE]: 제공기관 부분검색
- cond[분류체계::LIKE]: 분류체계 부분검색
- cond[목록유형::EQ]: FILE, API, STANDARD

조건을 여러 개 넣으면 AND 조건으로 해석될 수 있으므로, 처음에는 목록명만 검색하고 필요할 때 기관·분류·유형을 붙인다.

## Useful columns

- 목록명
- 파일데이터명
- 목록유형
- 분류체계
- 제공기관
- 업데이트 주기
- 차기 등록 예정일
- 매체유형
- 제공형태
- 설명
- 기타 유의사항
- API 유형
- 신청가능 트래픽
- 심의 유형
- 조회수
- 목록 URL
- 국가중점여부

## Public-sector summary shape

사용자에게는 보통 다음 순서로 정리한다.

1. 목록명
2. 제공기관
3. 목록유형과 API 유형
4. 갱신주기
5. 조회수
6. 왜 쓸 만한지 한 줄
7. 목록 URL
