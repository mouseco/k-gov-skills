# 국회 의안·입법 변화 추적 가이드

national-assembly-tracker는 열린국회정보 Open API로 특정 키워드 관련 법률안을 검색하고, 공공기관 업무에 영향을 줄 수 있는 입법 변화를 추적하는 스킬입니다.

## 해주는 일

- 키워드 기반 법률안 검색
- 제안일, 소관위원회, 처리결과 확인
- 대표발의자·공동발의자 정리
- 의안정보 상세 링크 제공
- 회의록·입법예고 공식 확인 링크 제공

## 적합한 사용 장면

- "인공지능 관련 법안 변화 찾아줘"
- "청년, 고용, 학자금 관련 법안 모니터링해줘"
- "공공기관 업무에 영향 줄 법안이 있는지 봐줘"
- "소관위원회와 처리상태 중심으로 정리해줘"

## 기본 실행

    python -X utf8 skills\\national-assembly-tracker\\scripts\\run_national_assembly_tracker.py bills --query "인공지능" --text

국회 대수 지정:

    python -X utf8 skills\\national-assembly-tracker\\scripts\\run_national_assembly_tracker.py bills --query "학자금" --age 22 --limit 10 --text

공식 확인 링크만 출력:

    python -X utf8 skills\\national-assembly-tracker\\scripts\\run_national_assembly_tracker.py links --query "청년" --text

## 인증

열린국회정보 Open API 인증키를 환경변수 OPEN_ASSEMBLY_API_KEY에 넣습니다.

## 출처

- 열린국회정보: https://open.assembly.go.kr
- 의안정보시스템: API 응답의 DETAIL_LINK
- 회의록시스템: https://likms.assembly.go.kr/record/
- 국회입법예고: https://pal.assembly.go.kr

## 주의사항

- 법안 검색은 열린국회정보 의안 API 기준입니다.
- 회의록과 입법예고 본문은 법안 후보를 좁힌 뒤 공식 시스템에서 추가 확인합니다.
- 이 스킬은 조회 전용입니다. 입법예고 의견 제출이나 로그인 흐름은 처리하지 않습니다.
