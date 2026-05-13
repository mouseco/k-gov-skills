# 하이패스 provider 설계

## 적용 범위

하이패스 provider는 고속도로 통행료 홈페이지의 사용내역 조회와 영수증 출력 화면을 이용해 출장·여비 정산용 증빙을 수집한다.

v0.1 기본 provider는 `hipass-browser-session`이다.

## 공식 표면

- 메인: `https://www.hipass.co.kr/main.do`
- 로그인: `https://www.hipass.co.kr/comm/lginpg.do`
- 사용내역 조회 진입: `https://www.hipass.co.kr/usepculr/InitUsePculrTabSearch.do`
- 사용내역 목록: `/usepculr/UsePculrTabSearchList.do`
- 영수증 출력: `/usepculr/UsePculrReceiptPrint.do`
- 세션 확인: `/comm/sessionCheck.do`

공식 이용안내 기준:

- 현재일로부터 3년간 조회 가능
- 최대 조회기간은 개인 3개월, 법인 1개월
- 최근 내역은 데이터 전송 지연 가능
- 후불카드는 승인·청구 지연 가능
- 후불카드 청구일 기준 조회 시 영수증 출력이 제한될 수 있음

## 인증 방식

### 기본: `hipass-idpw-login`

하이패스가 ID/비밀번호만으로 로그인 가능한 경우 기본 provider로 사용한다.

조건:

- ID와 비밀번호는 대화나 저장소에 남기지 않는다.
- 기본 env 파일은 사용자 홈 아래의 OpenClaw 환경파일(`.openclaw/.env`)이며, ID는 `KGOV_HIPASS_ID`, 비밀번호는 `KGOV_HIPASS_PW`에서 읽는다.
- 휴대전화 인증, 이메일 인증, SNS 인증, 공동인증서, 아이핀, 비밀번호 변경 안내, CAPTCHA가 나오면 즉시 중단한다.
- 자동 로그인 실패 시 브라우저 직접 로그인 세션 방식으로 전환할 수 있다.

### 대체: `hipass-browser-session`

1. 사용자가 Chrome에서 공식 하이패스 홈페이지에 직접 로그인한다.
2. 스킬은 Chrome DevTools Protocol 또는 Playwright persistent context로 로그인된 세션에 붙는다.
3. 사용내역 조회 화면으로 이동한다.
4. 세션 만료나 권한 확인 화면이 나오면 중단한다.

이 방식은 `--auth-mode session`으로 선택한다.

### v2: headless 모드

`--headless`를 붙이면 브라우저 창을 띄우지 않고 ID/PW 로그인부터 조회·영수증 저장까지 시도한다.

조건:

- `KGOV_HIPASS_ID`, `KGOV_HIPASS_PW`가 기본 env 파일에 있어야 한다.
- 수동 로그인 세션 재사용 방식과 함께 쓰지 않는다.
- 추가 본인확인, 보안 프로그램, 팝업 차단 등으로 실패하면 headed/CDP 방식으로 재시도한다.

### 제외: 자동 본인확인 통과

아래는 공개 스킬 범위 밖이다.

- CAPTCHA 인식과 자동 입력
- 휴대전화 인증번호 자동 수신·입력
- 이메일 인증번호 자동 수신·입력
- 공동인증서 자동 조작
- 장기 쿠키 보관 후 무인 재사용

## 조회 조건

기본 입력:

- 시작일: `YYYY-MM-DD`
- 종료일: `YYYY-MM-DD`
- 날짜 기준: 기본 거래일
- 카드 조건: 기본 전체
- 페이지 크기: 가능한 경우 30 또는 50

내부 요청에 쓰이는 대표 필드:

- `sDate`: 시작일 `YYYYMMDD`
- `eDate`: 종료일 `YYYYMMDD`
- `date_type`: 날짜 기준
- `pageSize`: 페이지 크기
- `pageNo`: 페이지 번호
- `order_type`: 정렬 방향
- `order_item`: 정렬 항목

## 결과 필드

사용내역 목록에서 가능한 범위로 아래 값을 정규화한다.

```json
{
  "provider": "hipass",
  "workDateTime": "2026-05-03 09:12:00",
  "cardNumberMasked": "1234-****-****-5678",
  "inTollgateName": "서울TG",
  "outTollgateName": "동대구TG",
  "transactionAmount": 12800,
  "billDate": "2026-05-06",
  "rowIndex": 1
}
```

카드번호는 마스킹 값만 사용한다. 원문 카드번호를 저장하지 않는다.

## 영수증 저장

저장 순서:

1. 조회 목록에서 대상 row를 고른다.
2. 영수증 출력 화면 또는 팝업을 연다.
3. PDF를 저장한다.
4. 영수증 영역을 PNG로 캡처한다.
5. PDF만 있을 경우 PDF 첫 페이지를 PNG로 렌더링한다.

파일명 규칙:

```text
YYYY-MM-DD_hipass_입구-출구_금액.pdf
YYYY-MM-DD_hipass_입구-출구_금액.png
```

파일명에 쓸 수 없는 문자는 `_`로 바꾼다.

## 세션 만료 감지

아래 신호가 있으면 인증 실패로 본다.

- 로그인 페이지로 이동
- 권한 확인 화면
- `mgs_type 11` 또는 `mgs_type 12`
- 세션 종료 안내 문구

이 경우 재로그인을 요구하고 같은 세션에서 다시 시도한다.

## 구현 참고

기존 k-skill의 `hipass-receipt` 구현은 아래 흐름을 이미 확인했다.

- 사용내역 조회 진입
- 조회 조건 form submit
- 사용내역 HTML 파싱
- 세션 상태 감지
- 영수증 팝업 진입

`transport-receipt-collector`에서는 이 흐름을 공공기관 정산 증빙 수집 목적에 맞춰 좁히고, PDF와 PNG 산출 규칙을 추가한다.

## 완료 기준

- 로그인된 하이패스 세션으로 사용내역을 조회했다.
- 요청 기간의 영수증 대상 row를 식별했다.
- 각 대상에 대해 PDF와 PNG 저장을 시도했다.
- 실패 항목은 사유를 남겼다.
- 민감한 인증정보와 카드번호 원문이 저장되지 않았다.
