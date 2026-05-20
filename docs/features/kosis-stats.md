# KOSIS 공식 통계 조회 가이드

이 스킬은 `NomaDamas/k-skill`의 `kosis-stats` 원본을 가져와 공공기관 보고서·사업계획·정책근거 조사에 자주 쓰는 지표 프리셋을 보강한 파생·적응본입니다.

## 할 수 있는 일

- KOSIS 통계표를 키워드로 검색
- 통계표 메타데이터, 분류, 항목, 단위 확인
- 기간·분류 조건을 지정해 통계 수치 조회
- 공공기관 보고서용 인구·고용·물가·지역경제·교육·복지 지표 후보 탐색
- KOSIS table id, 기간, 단위, endpoint를 포함한 출처 메모 작성

## 대표 사용 장면

- “대구 청년정책 근거로 볼 공식 통계 찾아줘”
- “우리나라 최신 인구·고용·물가 핵심지표 뽑아줘”
- “저출생·고령화 보고서에 넣을 KOSIS 지표 후보 정리해줘”
- “공공기관 사업계획서에 쓸 지역 현황 수치 찾아줘”

## 공공기관용 지표 프리셋

`references/public-sector-indicator-presets.md`에 아래 묶음을 넣어뒀습니다.

1. 국가 기본 스냅샷
2. 지역 기본 현황
3. 청년정책
4. 저출생·고령화
5. 고용·지역경제
6. 복지·취약계층
7. 교육·장학
8. 행정수요·서비스 기획

공공기관·공무원 보고서, 사업계획서, 정책 배경자료, 지역 현황 분석처럼 “무슨 지표를 봐야 하는지”부터 정해야 하는 요청이면 이 프리셋을 먼저 봅니다.

## 기본 흐름

1. 한국어 키워드로 통계표를 검색합니다.
2. 후보 통계표의 `org_id`와 `tbl_id`를 고릅니다.
3. `meta`로 분류·항목·단위·주기를 확인합니다.
4. `data`로 작은 기간과 좁은 분류부터 조회합니다.
5. 응답에는 table id, 기간, 단위, endpoint를 함께 남깁니다.

## 실행 예시

```powershell
python -X utf8 skills\kosis-stats\scripts\run_kosis_stats.py search --query "주민등록인구" --direct --text
python -X utf8 skills\kosis-stats\scripts\run_kosis_stats.py meta --table-id DT_1YL20651E --meta-type ITM --direct --text
python -X utf8 skills\kosis-stats\scripts\run_kosis_stats.py data --table-id DT_1YL20651E --prd-se M --start 202604 --end 202604 --itm-id ALL --obj-l 1=ALL --direct --text
```

## 인증키

기본 원본 스킬은 hosted proxy를 사용할 수 있게 설계되어 있지만, 환경에 따라 proxy가 실패할 수 있습니다. 이 경우 KOSIS Open API 인증키를 발급받아 `KSKILL_KOSIS_API_KEY` 환경변수로 넣고 `--direct`를 사용합니다.

인증키 발급 경로:

- https://kosis.kr/openapi/

## 주의사항

- 주민등록인구와 인구총조사는 같은 지표가 아닙니다.
- 청년 연령 기준은 정책마다 다릅니다. 15~29세, 19~34세, 조례상 청년 기준을 구분해야 합니다.
- 월별 지표와 연간 지표를 섞을 때는 기준기간을 명시합니다.
- 국가예산·재정수지는 KOSIS보다 기획재정부·열린재정 자료가 더 적합한 경우가 많습니다.
- 금리·금융시장 지표는 한국은행 ECOS가 더 적합한 경우가 많습니다.
- 장래추계는 관측값이 아니라 전망값으로 표시합니다.

## 출처와 소유권

원본은 `NomaDamas/k-skill` 저장소의 `kosis-stats`입니다. 이 저장소에서는 공공기관 실무 지표 프리셋과 공개 문서 설명을 추가했습니다. 원 출처와 MIT 라이선스를 존중하며, 자세한 출처와 수정 범위는 `docs/attribution.md`를 따릅니다.
