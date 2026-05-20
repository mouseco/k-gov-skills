# 나라장터 입찰공고정보 API 참고

## Source

- 공공데이터포털: https://www.data.go.kr/data/15129394/openapi.do
- Base URL: http://apis.data.go.kr/1230000/ad/BidPublicInfoService

## Operations

- 용역: getBidPblancListInfoServc
- 물품: getBidPblancListInfoThng
- 공사: getBidPblancListInfoCnstwk

## Common parameters

- serviceKey: 공공데이터포털 인증키
- pageNo: 페이지 번호
- numOfRows: 페이지당 건수
- type: json
- inqryDiv: 1
- inqryBgnDt: 조회 시작 일시, yyyyMMddHHmm
- inqryEndDt: 조회 종료 일시, yyyyMMddHHmm

## Useful fields

- bidNtceNo: 입찰공고번호
- bidNtceOrd: 차수
- bidNtceNm: 공고명
- ntceInsttNm: 공고기관
- dminsttNm: 수요기관
- bidNtceDt: 공고일시
- bidBeginDt: 입찰개시일시
- bidClseDt: 입찰마감일시
- opengDt: 개찰일시
- asignBdgtAmt: 배정예산금액
- bdgtAmt: 공사 예산금액
- presmptPrce: 추정가격
- bidMethdNm: 입찰방식
- cntrctCnclsMthdNm: 계약체결방법
- sucsfbidMthdNm: 낙찰방법
- ntceSpecDocUrl1~10: 공고 규격서/첨부 URL
- ntceSpecFileNm1~10: 첨부 파일명
- bidNtceDtlUrl: 상세 URL
- bidNtceUrl: 공고 URL

## Public-sector summary shape

1. 공고명
2. 수요기관 / 공고기관
3. 예산 또는 추정가격
4. 입찰마감 / 개찰일시
5. 계약방법 / 낙찰방법
6. 과업 판단 힌트: 공고명과 분류명, 첨부명
7. 상세 URL과 첨부 URL
