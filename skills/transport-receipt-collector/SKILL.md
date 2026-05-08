---
name: transport-receipt-collector
description: 공공기관 출장·여비·교통비 정산에 필요한 하이패스, 코레일, SRT 영수증을 공식 사이트 또는 승인된 제공자 경로에서 수집하고 PDF와 PNG 증빙 파일로 정리할 때 사용한다.
license: See docs/attribution.md
metadata:
  category: utility
  locale: ko-KR
  phase: v0.1
---

# Transport Receipt Collector

## 목적

출장·여비 정산에 필요한 교통비 증빙을 월별로 모으고, 제출 가능한 파일명과 형식으로 정리한다. v0.1의 1차 구현 대상은 **하이패스 영수증**이며, 코레일·SRT는 같은 provider 구조로 확장한다.

핵심 원칙은 간단하다.

- 로그인과 본인확인은 사람이 직접 처리한다.
- 스킬은 로그인 이후의 조회, 선택, 저장, 파일명 정리를 맡는다.
- 영수증 산출물은 **PDF와 PNG**를 기본으로 한다.
- JPG는 만들지 않는다.

## When to use

- 하이패스 사용내역 영수증을 월별로 모아야 할 때
- 출장비 정산용 교통비 증빙을 PDF와 PNG로 저장해야 할 때
- 코레일·SRT 영수증 수집 스킬을 같은 구조로 확장해야 할 때
- 로그인 이후 공식 사이트의 영수증 출력 화면을 안전하게 자동화해야 할 때

## When not to use

- 타인 명의 계정이나 차량·카드 사용내역을 조회하려는 경우
- 인증번호, 공동인증서, CAPTCHA, 추가 본인확인 화면을 자동 통과하려는 경우
- 결제, 취소, 환불 같은 부작용 있는 업무를 같이 처리하려는 경우
- 기관 약관이나 접근 제한을 우회해야만 가능한 경우

## Provider model

이 스킬은 기관별 처리를 provider 단위로 나눈다.

| provider | 상태 | 기본 인증 방식 | 역할 |
| --- | --- | --- | --- |
| `hipass-idpw-login` | v0.1 기본값 | 로컬 실행 환경에서 읽은 ID/비밀번호 | 추가 본인확인 없이 로그인 가능한 경우 자동 로그인 후 조회·저장 |
| `hipass-browser-session` | 대체 방식 | 사용자가 직접 로그인한 Chrome 세션 재사용 | ID/PW 자동 로그인이 막힐 때 같은 Chrome 세션으로 조회·저장 |
| `korail-browser-session` | 예정 | 사용자 직접 로그인 세션 | 코레일 승차권·영수증 저장 |
| `srt-browser-session` | 예정 | 사용자 직접 로그인 세션 | SRT 승차권·영수증 저장 |

새 provider를 붙일 때는 아래 항목을 먼저 정한다.

- `provider id`
- 공식 진입 URL
- 인증 방식과 중단 조건
- 날짜 범위 입력 형식
- 영수증 목록을 식별하는 방법
- PDF 저장 방법
- PNG 저장 방법
- 파일명 규칙
- 실패 모드와 사용자 개입 지점

## Security boundary

- 계정 비밀번호, 인증서 파일, 인증서 비밀번호, 인증번호, 카드번호 원문을 저장소·로그·대화에 남기지 않는다.
- CAPTCHA 인식, 2차 인증 자동 통과, 공동인증서 자동 조작은 공개 스킬 범위 밖이다.
- ID/PW 자동 로그인은 기본값으로 시도하되, 추가 본인확인이 나오면 즉시 중단한다.
- 비밀번호 변경 안내, 휴대전화 인증, 이메일 인증, 공동인증서, SNS 인증, 아이핀, CAPTCHA가 나오면 즉시 중단하고 사용자의 직접 처리를 요구한다.

## Output rule

기본 산출물은 항상 같은 base name의 PDF와 PNG다.

```text
outputs/receipts/YYYY-MM/
  YYYY-MM-DD_provider_route_or_train_amount.pdf
  YYYY-MM-DD_provider_route_or_train_amount.png
```

예시:

```text
outputs/receipts/2026-05/
  2026-05-03_hipass_서울TG-동대구TG_12800.pdf
  2026-05-03_hipass_서울TG-동대구TG_12800.png
```

PNG 생성 우선순위:

1. 1건 기준으로 영수증 출력 화면의 하이패스 사각형 영수증 영역만 PNG로 캡처한다.
2. 영수증 영역 자동 감지가 실패하면 현재 하이패스 출력 화면의 좌측 영수증 기본 위치를 고정 크롭한다.
3. PDF만 확보된 경우 PDF 첫 페이지를 PNG로 렌더링한다.
4. 둘 다 실패하면 영수증 팝업 URL, 화면 제목, 실패 사유를 남기고 사용자가 수동 저장할 수 있게 한다.

## Standalone script

중심 스크립트는 아래 파일이다. 기존 `hipass-receipt` 패키지에 의존하지 않고, 하이패스 조회·파싱·저장 로직을 이 스킬 안에서 직접 처리한다. 단, Chrome 제어를 위해 실행 환경에 `playwright-core` 또는 `playwright`는 필요하다.

```powershell
node skills\transport-receipt-collector\scripts\collect_transport_receipts.cjs --help
```

하이패스 로그인용 Chrome 실행문 출력:

```powershell
node skills\transport-receipt-collector\scripts\collect_transport_receipts.cjs chrome-command --provider hipass --debugging-port 9222
```

하이패스 사용내역 조회 기본값은 ID/PW 자동 로그인이다. 스크립트는 기본적으로 `C:\Users\mouse\.openclaw\.env`를 로드하며, 아래 키를 사용한다.

```text
KGOV_HIPASS_ID=...
KGOV_HIPASS_PW=...
```

```powershell
node skills\transport-receipt-collector\scripts\collect_transport_receipts.cjs list --provider hipass --start-date 2026-05-01 --end-date 2026-05-31 --cdp-url http://127.0.0.1:9222
```

이미 브라우저에서 직접 로그인한 세션을 쓰려면 `--auth-mode session`을 붙인다.

```powershell
node skills\transport-receipt-collector\scripts\collect_transport_receipts.cjs list --provider hipass --start-date 2026-05-01 --end-date 2026-05-31 --cdp-url http://127.0.0.1:9222 --auth-mode session
```

하이패스 영수증 PDF와 PNG 저장:

```powershell
node skills\transport-receipt-collector\scripts\collect_transport_receipts.cjs collect --provider hipass --start-date 2026-05-01 --end-date 2026-05-31 --row-index 1 --cdp-url http://127.0.0.1:9222 --output-dir outputs\receipts\2026-05
```

v2 headless 모드:

```powershell
node skills\transport-receipt-collector\scripts\collect_transport_receipts.cjs collect --provider hipass --start-date 2026-05-01 --end-date 2026-05-31 --row-index 1 --headless --output-dir outputs\receipts\2026-05
```

- `--headless`는 ID/PW 자동 로그인 전용이다.
- 직접 로그인된 브라우저 세션을 재사용하는 `--auth-mode session`과 함께 쓰지 않는다.

## Basic workflow

### 1. 요청 범위 확인

확인할 값:

- provider: `hipass`, `korail`, `srt`, 또는 `all`
- 기간: `YYYY-MM-DD` 시작일과 종료일
- 저장 위치: 지정이 없으면 `outputs/receipts/YYYY-MM/`
- 출력 형식: 기본 `pdf,png`

### 2. provider별 로그인 상태 확인

하이패스 v0.1은 `hipass-browser-session`을 기본으로 사용한다.

- 사용자가 Chrome에서 공식 하이패스 홈페이지에 직접 로그인한다.
- 스킬은 로그인된 Chrome 세션에 연결한다.
- 세션 만료나 권한 확인 화면이 나오면 재로그인을 요구한다.

하이패스 상세 절차가 필요하면 `references/hipass.md`를 읽는다.

### 3. 사용내역 또는 영수증 목록 조회

- 날짜 범위를 적용한다.
- 조회 결과에서 거래일, 입구/출구 영업소, 금액, 카드번호 마스킹 값을 읽는다.
- 사용자가 특정 건을 지정하지 않았으면 기간 내 전체 건을 수집 대상으로 둔다.

### 4. 영수증 화면 진입과 저장

- 가능한 경우 공식 영수증 출력 화면 또는 팝업에 진입한다.
- PDF 저장을 시도한다.
- 같은 영수증 영역을 PNG로 저장한다.
- 파일명은 거래일, provider, 구간, 금액 기준으로 만든다.

### 5. 결과 요약

작업이 끝나면 아래만 짧게 보고한다.

- 수집 성공 건수
- 실패 건수와 사유
- 저장 폴더
- 사용자가 직접 처리해야 할 항목

## Failure modes

- 로그인 세션 없음: 사용자가 공식 사이트에서 직접 로그인해야 한다.
- 세션 만료: 다시 로그인해야 한다.
- 추가 본인확인 발생: 자동화를 멈추고 사용자가 직접 처리해야 한다.
- 조회 결과 없음: 기간, 카드, 차량, 청구일/거래일 조건을 다시 확인한다.
- 영수증 출력 불가: 하이패스 안내 기준으로 후불카드 청구일 조회 등 일부 조건에서는 출력이 제한될 수 있다.
- PNG 저장 실패: PDF를 먼저 확보하고 PDF 렌더링으로 PNG를 만든다.

## Done when

- 요청 기간의 하이패스 영수증 대상 목록을 확인했다.
- 각 대상에 대해 PDF와 PNG 저장을 시도했다.
- 저장된 파일의 경로와 실패한 항목의 사유를 보고했다.
- 비밀번호, 인증번호, 인증서 파일, 카드번호 원문이 저장소나 로그에 남지 않았다.

## References

- 하이패스 provider 상세: `references/hipass.md`
- 외부·파생 출처: `docs/attribution.md`
