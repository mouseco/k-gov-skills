# ALIO 기관별 공시 확인 가이드

## 오늘 범위

포함:
- ALIO 공공기관 경영정보 공개시스템 `https://alio.go.kr`
- 경영공시 > 기관별 공시
- 공공기관별 공시 상세내용 확인
- 기준연도·공시일·공시항목·수치 단위 확인

제외:
- ALIO PLUS API
- ALIO PLUS 행사·시설·사업 안내
- JOB-ALIO 채용공고 중심 조사
- ALIO 오픈데이터 대량 수집 자동화

## 핵심 URL

- ALIO 메인: `https://alio.go.kr/`
- 기관별 공시: `https://alio.go.kr/organ/organDisclosureList.do`
- 항목별 공시: `https://alio.go.kr/item/itemList.do`
- 공시현황: `https://alio.go.kr/status/disclosureStatus.do`
- 최근공시: `https://alio.go.kr/status/recentDisclosureList.do`
- 감사원/주무부처 지적사항: `https://alio.go.kr/occasional/auditPointList.do`
- 내부·외부 감사결과: `https://alio.go.kr/occasional/boardDirectorsList.do?reportType=43006`
- 내부규정: `https://alio.go.kr/occasional/ruleList.do`

## 기관 식별 절차

1. 사용자가 준 기관명을 그대로 검색한다.
2. 검색 결과가 없으면 정식 명칭, 약칭, 띄어쓰기 차이를 바꿔 본다.
3. 후보가 여러 개면 아래 값으로 구분한다.
   - 주무부처
   - 기관유형
   - 소재지
   - 본부기관/부설기관 여부
4. 보고서에는 최종 확인한 정식 기관명을 쓴다.

## 기관별 공시 확인 절차

1. `기관별 공시` 화면에서 대상 기관을 찾는다.
2. 해당 기관의 `공시` 또는 상세 공시 화면으로 이동한다.
3. 확인할 공시 항목을 고른다.
4. 표·상세 페이지·첨부파일에서 아래 값을 확인한다.
   - 기준연도
   - 공시차수 또는 공시일
   - 항목명
   - 수치와 단위
   - 기간 또는 기준일
   - 비고·주석
5. 필요한 경우 항목별 공시 화면에서 같은 항목을 재확인한다.

## 확인된 URL 패턴

기관별 정기공시 상세 페이지는 아래 형식으로 접근할 수 있다.

```text
https://alio.go.kr/item/itemReportTerm.do?apbaId=<기관ID>&reportFormRootNo=<공시항목번호>
```

페이지 안의 실제 본문은 `/upload/disclosure/.../doc.html`로 로드되는 경우가 많다. 상세 수치 확인 시 `itemReportTerm.do` 화면에서 본문 `doc.html` 경로를 찾아 본문까지 확인한다.

통계 화면은 보조 확인에 쓸 수 있다.

```text
https://alio.go.kr/statisticsSearch/findItemTreeList.json
https://alio.go.kr/statisticsSearch/findSingleItemSearchList.json?pageNo=1&countPerPage=100&reportFormNo=<공시항목번호>&itemNo=<항목코드>
```

자주 쓰는 항목 예시:

- 임직원수: `reportFormRootNo=20201`, 통계 보조 확인 시 임직원 총계 `itemNo=GI03`
- 신규채용 현황: `reportFormRootNo=20401`
- 임원연봉: `reportFormRootNo=20501`
- 직원 평균보수: `reportFormRootNo=20601`, 통계 보조 확인 시 정규직(일반정규직) 1인당 평균 보수액 `itemNo=GI0101`
- 기관장 업무추진비: `reportFormRootNo=20701`
- 복리후생비: `reportFormRootNo=20801`
- 그 밖의 복리후생제도 등의 운영현황: `reportFormRootNo=63701`
- 소송 및 소송대리인 현황: `reportFormRootNo=21301`
- 일·가정 양립 지원제도 및 양성평등 운영 현황: `reportFormRootNo=21401`
- 요약재무상태표: `reportFormRootNo=31201`
- 요약손익계산서: `reportFormRootNo=31301`
- 수입지출현황: `reportFormRootNo=31401`
- 투자 및 출자 현황: `reportFormRootNo=31901` — 기관에 따라 상세 본문이 없을 수 있으므로 실패 시 `해당사항 없음/상세본문 없음`으로 기록한다.
- 출연 현황: `reportFormRootNo=32001`
- 법인세정보: `reportFormRootNo=32211`

단, 통계 JSON 값만으로 끝내지 말고 `itemReportTerm.do` 상세 본문에서 기준일·제출일·주석을 확인한다.

수시공시 감사자료는 아래 JSON을 보조로 쓸 수 있다.

```text
/occasional/findPointList.json?type=apbaNa&word=<기관명>&reportFormNo=B1220
/occasional/findBoardDirectorsList.json?type=apbaNa&word=<기관명>&reportType=43006
/item/itemReportFiles.json?disclosureNo=<공시번호>
/download/file.json?f=<파일번호>&d=<공시번호>
```

감사결과는 목록 제목만으로 결론내지 말고 상세 `doc.html`과 첨부 PDF/HWP까지 확인한다. 특히 `유출`, `징계`, `비위`, `보안`처럼 민감한 키워드는 `실제 발생`, `발생 여부 점검`, `위험/우려`, `모범사례`를 분리한다.

내부규정은 아래 JSON과 다운로드 경로를 쓴다.

```text
/occasional/findRuleList.json?type=apbaNa&word=<기관명>&pageNo=<페이지>&divis=<분류코드>
/occasional/findRuleDtl.json?seq=<규정 seq>
/download/rulefiledown.json?fileNo=<파일번호>
```

분류코드 예시는 `K1500=정관`, `K1100=인사·복무·징계`, `K1200=보수`, `K1300=직제`, `K1400=기타`다. 상세 JSON의 `bFiles`는 `파일번호|파일명` 형식이며, ZIP으로 여러 개정본 HWP가 묶여 있을 수 있다. ALIO 화면에서 본문을 HTML로 바로 제공하지 않는 경우가 많으므로, 규정 전문 확인은 첨부파일을 다운로드해 ZIP/HWP/PDF를 해제·추출해서 확인한다.

## 자주 확인하는 공시 항목

### 일반현황

확인할 값:
- 기관명
- 기관유형
- 주무부처
- 설립근거
- 설립목적
- 소재지
- 홈페이지

주의:
- 기관 소개 문구와 법적 설립근거를 구분한다.

### 임직원 수

확인할 값:
- 정원
- 현원
- 임원 수
- 직원 수
- 비정규직 또는 소속외 인력 여부
- 기준일

주의:
- 정원과 현원을 혼동하지 않는다.
- 본부와 부설기관 포함 여부를 확인한다.

### 임원 현황

확인할 값:
- 기관장
- 상임임원
- 비상임임원
- 임기
- 선임 방식 또는 주요 경력 공개 여부

주의:
- 개인 신상보다 공시된 직위·임기·현황 중심으로 정리한다.

### 재무정보

확인할 값:
- 자산
- 부채
- 자본
- 수익
- 비용
- 당기순이익 또는 손익
- 회계연도
- 단위

주의:
- 개별/연결, 회계 기준, 단위가 다르면 비교하지 않는다.

### 주요사업

확인할 값:
- 사업명
- 사업 목적
- 사업비 또는 예산
- 추진 실적
- 대상
- 기준연도

주의:
- 기관 홈페이지의 홍보성 설명과 ALIO 공시 내용을 구분한다.

### 감사·평가·지적사항

확인할 값:
- 지적기관
- 지적일 또는 공개일
- 지적내용
- 조치결과
- 관련 첨부파일

주의:
- 지적사항은 표현을 과장하지 말고 공시 문구에 맞춰 요약한다.
- 첨부자료가 있으면 본문 요약만 보지 말고 첨부 원문에서 실제 지적 문구를 확인한다.
- `유출 우려`, `유출 여부 점검`, `유출 확인`은 서로 다른 의미로 구분한다.

### 내부규정

확인할 값:
- 규정명
- 기관명
- 분야: 정관, 인사·복무·징계, 보수, 직제, 기타
- 제·개정 시행일 또는 기준일
- 등록/공시일
- 상세 `seq`
- 첨부파일명과 파일번호

주의:
- 국가법령정보센터 공공기관 규정은 보조 출처일 뿐이며, ALIO 내부규정 목록이 더 넓을 수 있다.
- ALIO 내부규정은 전문이 HTML 본문으로 보이지 않고 ZIP/HWP/PDF 첨부로 제공될 수 있다.
- ZIP에는 여러 개정 이력 파일이 함께 들어갈 수 있으므로 최신 시행일 파일을 골라 확인한다.

## k-dart와 다른 점

- DART는 OpenAPI 중심으로 `corp_code`를 확보한 뒤 endpoint를 호출한다.
- ALIO 기관별 공시는 웹 화면의 기관 검색과 항목 선택 흐름이 중요하다.
- 따라서 이 스킬은 API 호출보다 **상세 공시 화면 확인 절차와 출처 기록**을 우선한다.
- 향후 ALIO 본공시에 안정적인 API나 내부 JSON endpoint가 확인되면 scripts로 분리한다.

## 결과 정리 원칙

- 공시 원문에 있는 사실과 에이전트의 해석을 분리한다.
- 수치에는 단위와 기준일을 붙인다.
- 비교는 같은 기준연도와 같은 항목끼리만 한다.
- 화면에서 확인하지 못한 값은 `확인 필요`로 남긴다.
- ALIO PLUS 자료를 근거로 썼다면 반드시 `보조 출처`라고 표시한다. 오늘 범위에서는 기본적으로 쓰지 않는다.
