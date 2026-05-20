# Public-Sector Indicator Presets

Use this reference when a user asks for official statistics for public-sector reports, policy evidence, business plans, regional analysis, or administrative briefings.

This file does not replace the KOSIS search, meta, and data workflow. It narrows the first search and gives common indicator packs that Korean public officials and public institutions repeatedly need.

## Operating Rule

1. Start from the user's policy domain and geography.
2. Pick one preset below.
3. Search KOSIS with the Korean search terms.
4. Prefer observed/latest official statistics over long-range projections unless the user asks for outlook.
5. Run `meta` before `data` and cite `org_id`, `tbl_id`, period, unit, and endpoint.
6. For report writing, separate facts from interpretation. Do not turn KOSIS numbers into policy conclusions without saying the judgment basis.

## Preset 1. National Snapshot

Use for: country overview, report introductions, macro context, budget/environment sections.

Core indicators:
- Resident registration population
- Employment rate
- Unemployment rate
- Consumer price inflation
- Nominal GDP
- Real GDP growth
- Births and total fertility rate
- Aged population ratio or aging index

Search terms:
- 주민등록인구
- 경제활동인구
- 실업률
- 소비자물가
- 국내총생산
- 합계출산율
- 고령인구비율

Known useful table candidates:
- `101/DT_1YL20651E` 주민등록인구(시도/시/군/구)
- `101/DT_1DA7001S` 성별 경제활동인구 총괄
- `101/DT_1J22042` 월별 소비자물가 등락률
- `301/DT_200Y101` 한국은행 주요지표(연간지표)
- `101/DT_1B81A23` 시군구/출생아수, 합계출산율

## Preset 2. Regional Basic Profile

Use for: local government reports, regional project plans, branch/service coverage, 균형발전.

Core indicators:
- Resident registration population by city/county/district
- Population change
- Aged population ratio
- Youth population ratio
- One-person households
- GRDP
- Establishments and workers by industry

Search terms:
- 주민등록인구
- 인구증감률
- 고령인구비율
- 청년인구비율
- 1인가구
- 지역내총생산
- 사업체수 종사자수

Report use:
- Use population and age structure for demand.
- Use GRDP, establishment count, and workers for economic base.
- Use one-person households for welfare, housing, safety, and administrative-service demand.

## Preset 3. Youth Policy

Use for: youth employment, scholarship, housing, startup, training, local youth retention.

Core indicators:
- Youth population ratio
- Youth employment rate
- Youth unemployment rate
- Economically inactive youth
- College or higher-education population when relevant
- One-person youth households when available
- Regional population movement

Search terms:
- 청년인구비율
- 청년 고용률
- 청년 실업률
- 비경제활동인구 청년
- 대학 재학생
- 인구이동률
- 1인가구 연령

Report use:
- Match the age definition before comparing indicators. Korean youth policy may use 15-29, 19-34, or local ordinance definitions.
- State the age range explicitly.

## Preset 4. Low Birthrate And Aging

Use for: education, family, welfare, care, regional extinction, local-service redesign.

Core indicators:
- Births
- Total fertility rate
- Aged population ratio
- Aging index
- Dependency ratio
- Single elderly households
- School-age population

Search terms:
- 출생아수
- 합계출산율
- 고령인구비율
- 노령화지수
- 부양비
- 독거노인가구비율
- 학령인구

Known useful table candidates:
- `101/DT_1B81A23` 시군구/출생아수, 합계출산율
- `101/DT_1YL20631` 고령인구비율(시도/시/군/구)

Report use:
- Use births/fertility for inflow.
- Use aging/dependency ratio for service burden.
- Use school-age population for education demand.

## Preset 5. Employment And Local Economy

Use for: job projects, vocational training, startup support, local industry, labor-market diagnosis.

Core indicators:
- Economically active population
- Employed persons
- Unemployed persons
- Employment rate
- Unemployment rate
- Youth employment/unemployment
- Establishments and workers by industry
- GRDP by region

Search terms:
- 경제활동인구
- 취업자
- 실업률
- 고용률
- 청년고용률
- 청년실업률
- 사업체수
- 종사자수
- 지역내총생산

Known useful table candidates:
- `101/DT_1DA7001S` 성별 경제활동인구 총괄

Report use:
- For monthly labor-market snapshots, prefer recent monthly tables.
- For structural regional comparison, prefer annual or multi-year regional tables.

## Preset 6. Welfare And Vulnerable Groups

Use for: social welfare, scholarship support, living-cost support, care services, vulnerable-group targeting.

Core indicators:
- Household income
- Median income when available
- Relative poverty rate
- Basic livelihood security recipients
- Elderly living alone
- Disabled population
- Household expenditure
- Housing-cost burden when available

Search terms:
- 가구소득
- 중위소득
- 상대적 빈곤율
- 기초생활보장 수급자
- 독거노인가구
- 장애인 인구
- 가계지출
- 주거비 부담

Report use:
- Be careful with income definitions: household income, disposable income, equivalized income, and official 기준중위소득 are not interchangeable.
- If the indicator is used for eligibility, cite the legal or administrative standard separately from KOSIS statistics.

## Preset 7. Education And Scholarship

Use for: scholarship policy, higher education, regional education demand, youth support, university-related public work.

Core indicators:
- School-age population
- Students by school level
- Higher education students
- University enrollment
- Graduation and employment rates
- Regional education participation indicators
- Household education expenditure when needed

Search terms:
- 학령인구
- 학생수
- 고등교육기관 재학생
- 대학 진학률
- 졸업자 취업률
- 교육비 지출
- 장학금
- 학자금대출

Report use:
- KOSIS may not cover every scholarship or student-loan operational statistic. For KOSAF-specific figures, use internal/open institutional sources separately and use KOSIS for background demand indicators.

## Preset 8. Administrative Demand And Service Planning

Use for: public service demand estimation, call center, civil service volume, digital-service planning.

Core indicators:
- Population by age and region
- Households
- One-person households
- Elderly living alone
- Population mobility
- Digital divide or internet-use indicators when available
- Local establishments and workers for business-facing services

Search terms:
- 세대수
- 1인가구
- 독거노인가구
- 인구이동
- 인터넷 이용률
- 정보격차
- 사업체수
- 종사자수

Report use:
- Use demographic indicators to estimate service demand.
- Use mobility and household structure for outreach and delivery-channel planning.

## Output Pattern

When summarizing results, prefer this shape:

```text
확인 기준: KOSIS <기관명> <통계표명>, <기간>, <단위>

핵심 수치:
- <지역/대상> <지표>: <값> <단위>

해석:
- 이 수치는 <사업/정책>에서 <수요/위험/성과기준> 근거로 쓸 수 있다.
- 단, <정의/연령범위/단위/잠정치 여부>는 별도 확인해야 한다.

출처:
- org_id=<ORG_ID>, tbl_id=<TBL_ID>, endpoint=<endpoint>
```

## Common Cautions

- 청년 age range is not fixed. Confirm the user's policy definition.
- Resident registration population is not the same as census population.
- Monthly indicators and annual indicators should not be mixed without saying the reference period.
- National budget and fiscal data are often better sourced from MOEF/Open Fiscal Data than KOSIS.
- Interest rates and financial-market series are often better sourced from Bank of Korea ECOS.
- For projections, label them clearly as projections, not observed results.
