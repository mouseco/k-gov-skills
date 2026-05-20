# 열린국회정보 의안 API 참고

## Source

- 열린국회정보: https://open.assembly.go.kr
- 국회의원 발의법률안 데이터 상세: https://open.assembly.go.kr/portal/data/service/selectServicePage.do?infId=OK7XM1000938DS17215
- API URL: https://open.assembly.go.kr/portal/openapi/nzmimeepazxkubdpn
- 원본시스템: 의안정보시스템

## Common parameters

- KEY: 열린국회정보 인증키
- Type: json
- pIndex: 페이지 번호
- pSize: 페이지 크기
- AGE: 국회 대수. 22대 기본
- BILL_NAME: 법안명 검색어

## Useful fields

- BILL_ID: 의안 ID
- BILL_NO: 의안 번호
- BILL_NAME: 법안명
- COMMITTEE: 소관위원회
- PROPOSE_DT: 제안일
- PROC_RESULT: 처리결과
- DETAIL_LINK: 의안정보 상세 링크
- PROPOSER: 제안자 표시
- RST_PROPOSER: 대표발의자
- PUBL_PROPOSER: 공동발의자
- LAW_PROC_DT: 법사위 처리일
- CMT_PROC_DT: 소관위 처리일
- PROC_DT: 본회의 처리일

## Official follow-up systems

API 응답만으로 회의록 본문과 입법예고 의견 상태가 항상 충분히 내려오지는 않는다. 법안 후보를 좁힌 뒤 아래 공식 시스템을 확인한다.

- 의안정보시스템: API의 DETAIL_LINK
- 회의록시스템: https://likms.assembly.go.kr/record/
- 국회입법예고: https://pal.assembly.go.kr
- 열린국회정보: https://open.assembly.go.kr

## Public-sector summary shape

1. 법안명
2. 제안일
3. 소관위원회
4. 진행상태와 처리결과
5. 대표발의자와 공동발의자
6. 공공기관 업무 영향 가능성 한 줄
7. 의안 상세 링크
8. 회의록·입법예고 확인 링크
