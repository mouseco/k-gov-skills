---
name: transport-receipt-collector
description: 공공기관 출장·여비·교통비 정산에 필요한 하이패스, 코레일, SRT 영수증을 공식 사이트 또는 승인된 제공자 경로에서 수집하고 PDF와 PNG 증빙 파일로 정리할 때 사용한다.
license: See docs/attribution.md
metadata:
  category: utility
  locale: ko-KR
  phase: v0.3
---

# Transport Receipt Collector

## 목적

출장·여비 정산에 필요한 교통비 증빙을 월별로 모으고, 제출 가능한 파일명과 형식으로 정리한다. 현재 지원 대상은 **하이패스, SRT, KTX/Korail** 3종이다.

핵심 원칙은 간단하다.

- 추가 본인확인과 CAPTCHA는 사람이 직접 처리한다.
- 스킬은 가능한 범위의 로그인, 조회, 선택, 저장, 파일명 정리를 맡는다.
- 영수증 산출물은 provider별로 **PDF, PNG, redacted JSON**을 저장한다.
- JPG는 만들지 않는다.

## When to use

- 하이패스 사용내역 영수증을 월별로 모아야 할 때
- SRT 이용내역 영수증을 PNG로 저장해야 할 때
- KTX/Korail 구입이력의 코레일톡 스타일 영수증 PNG와 redacted JSON을 저장해야 할 때
- 출장비 정산용 교통비 증빙을 한 스킬에서 provider별로 정리해야 할 때

## When not to use

- 타인 명의 계정이나 차량·카드 사용내역을 조회하려는 경우
- 인증번호, 공동인증서, CAPTCHA, 추가 본인확인 화면을 자동 통과하려는 경우
- 결제, 취소, 환불 같은 부작용 있는 업무를 같이 처리하려는 경우
- 기관 약관이나 접근 제한을 우회해야만 가능한 경우

## Provider model

이 스킬은 기관별 처리를 provider 단위로 나눈다.

| provider | 상태 | 기본 인증 방식 | 역할 |
| --- | --- | --- | --- |
| `hipass-idpw-login` | v0.3 지원 | 로컬 실행 환경에서 읽은 계정 정보 | 추가 본인확인 없이 로그인 가능한 경우 자동 로그인 후 조회·저장 |
| `hipass-browser-session` | 대체 방식 | 사용자가 직접 로그인한 Chrome 세션 재사용 | ID/PW 자동 로그인이 막힐 때 같은 Chrome 세션으로 조회·저장 |
| `korail-local-connector` | v0.3 지원 | `ktx-booking` 스킬 helper + KTX 계정 환경변수 | 공개 저장소에는 내부 호출 세부사항을 두지 않고, `ktx-booking` helper를 사용하는 로컬/private connector로 영수증 PNG/JSON 저장 |
| `korail-browser-session` | v0.2 대체 지원 | 사용자 직접 로그인 세션 | 코레일/KTX 웹 구입이력 영수증 화면을 PNG로 크롭 저장 |
| `srt-browser-session` | v0.3 지원 | 사용자 직접 로그인 세션 또는 로컬 계정 정보 | SRT 승차권 구입이력 영수증 화면을 PNG로 저장 |

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

기본 산출물은 provider별 특성에 맞춰 같은 base name으로 저장한다.

```text
outputs/receipts/YYYY-MM/
  YYYY-MM-DD_provider_route_or_train_amount.pdf
  YYYY-MM-DD_provider_route_or_train_amount.png
  YYYY-MM-DD_provider_route_or_train_amount.json
```

예시:

```text
outputs/receipts/2026-05/
  2026-05-03_hipass_서울TG-동대구TG_12800.pdf
  2026-05-03_hipass_서울TG-동대구TG_12800.png
```

PNG 생성 우선순위:

1. KTX/Korail은 `ktx-booking` 스킬을 먼저 설치하고, 그 helper를 사용하는 로컬/private connector에서 반환받은 공식 영수증 데이터로 확정된 v3 코레일톡 스타일 PNG를 렌더링한다.
2. 하이패스는 1건 기준으로 영수증 출력 화면의 사각형 영수증 영역만 PNG로 캡처한다.
3. SRT는 영수증 화면의 본문 영역을 PNG로 저장한다.
4. PDF만 확보된 경우 PDF 첫 페이지를 PNG로 렌더링한다.
5. 둘 다 실패하면 영수증 팝업 URL, 화면 제목, 실패 사유를 남기고 사용자가 수동 저장할 수 있게 한다.

## Standalone script

중심 스크립트는 아래 파일이다. 기존 `hipass-receipt` 패키지에 의존하지 않고, 하이패스 조회·파싱·저장 로직을 이 스킬 안에서 직접 처리한다. 단, Chrome 제어를 위해 실행 환경에 `playwright-core` 또는 `playwright`는 필요하다.

```powershell
node skills\transport-receipt-collector\scripts\collect_transport_receipts.cjs --help
```

공식 사이트 로그인용 Chrome 실행문 출력:

```powershell
node skills\transport-receipt-collector\scripts\collect_transport_receipts.cjs chrome-command --provider hipass --debugging-port 9222
node skills\transport-receipt-collector\scripts\collect_transport_receipts.cjs chrome-command --provider korail --debugging-port 9222
node skills\transport-receipt-collector\scripts\collect_transport_receipts.cjs chrome-command --provider srt --debugging-port 9222
```

하이패스 사용내역 조회 기본값은 로컬 계정 환경변수 기반 자동 로그인이다. 스크립트는 기본적으로 `KGOV_ENV_FILE` 또는 사용자 홈 아래의 환경파일(`$HOME/.openclaw/.env`)을 로드하며, 아래 키를 사용한다.

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

KTX/SRT 자동 로그인 후 구입이력/영수증 화면 진입:

```powershell
node skills\transport-receipt-collector\scripts\collect_transport_receipts.cjs open-history --provider korail --cdp-url http://127.0.0.1:9222
node skills\transport-receipt-collector\scripts\collect_transport_receipts.cjs open-history --provider srt --cdp-url http://127.0.0.1:9222
```

KTX/SRT 현재 영수증 화면 크롭 저장:

```powershell
node skills\transport-receipt-collector\scripts\collect_transport_receipts.cjs capture-current --provider korail --cdp-url http://127.0.0.1:9222 --output-dir outputs\receipts\2026-05
node skills\transport-receipt-collector\scripts\collect_transport_receipts.cjs capture-current --provider srt --cdp-url http://127.0.0.1:9222 --output-dir outputs\receipts\2026-05
```

SRT 자동 로그인 → 이용내역 조회 → 선택 행 영수증 PNG 저장:

```powershell
node skills\transport-receipt-collector\scripts\collect_transport_receipts.cjs collect-latest --provider srt --start-date 2026-02-09 --end-date 2026-05-09 --row-index 1 --output-dir outputs\receipts\2026-05
```

KTX/Korail `ktx-booking` helper 기반 영수증 저장:

KTX/Korail은 먼저 connector 경로부터 확인한다. 공개 저장소에는 실사용 `korail_receipt_connector.py`가 아니라 계약 예시인 `korail_receipt_connector.example.py`만 포함한다. 실사용 connector는 개인 경로에 복사해 구현한 뒤 `KGOV_KORAIL_CONNECTOR`로 지정한다.

```powershell
cd C:\path\to\k-gov-skills
Test-Path .\skills\transport-receipt-collector\scripts\korail_receipt_connector.example.py
New-Item -ItemType Directory -Force "$HOME\.openclaw\private-connectors"
Copy-Item .\skills\transport-receipt-collector\scripts\korail_receipt_connector.example.py "$HOME\.openclaw\private-connectors\korail_receipt_connector.py"
$env:KGOV_KORAIL_CONNECTOR="C:\Users\<you>\.openclaw\private-connectors\korail_receipt_connector.py"
Test-Path $env:KGOV_KORAIL_CONNECTOR
python $env:KGOV_KORAIL_CONNECTOR --help
```

경로가 확인되면 목록 조회부터 실행한다.

```powershell
node skills\transport-receipt-collector\scripts\collect_transport_receipts.cjs collect-latest --provider korail --start-date 2026-02-09 --end-date 2026-05-09 --list-only
```

목록이 보이면 저장을 실행한다.

```powershell
node skills\transport-receipt-collector\scripts\collect_transport_receipts.cjs collect-latest --provider korail --start-date 2026-02-09 --end-date 2026-05-09 --row-index 1 --output-dir outputs\receipts\2026-05
```

위 명령은 기본적으로 최종 확정된 코레일톡 스타일 영수증 PNG와 redacted JSON을 저장한다.

- 공개 저장소에는 Korail 내부 호출 URL, endpoint명, 파라미터명을 문서화하지 않는다.
- Korail 경로는 먼저 `ktx-booking` 스킬을 설치한 뒤, 그 helper를 불러 쓰는 영수증 connector를 `KGOV_KORAIL_CONNECTOR`로 지정해 실행한다.
- `KGOV_KORAIL_CONNECTOR`는 `--start-date`, `--end-date`, `--row-index`, `--output-dir`, `--list-only`, `--render-local` 인자를 처리하고 JSON 요약을 stdout으로 출력하는 connector 스크립트여야 한다.
- 공개 예시 connector는 실행 계약 확인용이며 `status: not_implemented_public_example`을 반환한다. 실제 영수증 저장에는 개인 구현 connector가 필요하다.
- `Korail receipt collection requires a local/private connector`는 connector 미지정, `Korail connector not found`는 파일 경로 오류다.
- `--output-dir` 상대경로가 헷갈리면 절대경로를 사용한다.
- 정산 증빙의 기본 원칙은 **공식 영수증 데이터로 만든 코레일톡 스타일 영수증 PNG**를 산출하는 것이다.
- 2026-05-11 실제 코레일톡 저장본 기준 검수로 `v3` 템플릿을 최종 기준으로 확정했다. 기준은 코레일톡 실제 저장본에서 QR 상단 영역을 제외한 짧은 영수증 본문 이미지다.
- 기본 `collect-latest --provider korail` 실행은 `ktx-booking` helper 기반 connector가 `KGOV_KORAIL_CONNECTOR`로 설정된 경우 이 최종 템플릿 PNG를 생성한다. 데이터 점검만 할 때는 `--list-only` 또는 `--no-render-local`을 사용한다.

자동 로그인부터 현재 화면 캡처까지 한 번에 시도:

```powershell
node skills\transport-receipt-collector\scripts\collect_transport_receipts.cjs collect-current --provider srt --cdp-url http://127.0.0.1:9222 --output-dir outputs\receipts\2026-05
```

화면 자동 감지가 맞지 않으면 수동 크롭 좌표를 준다.

```powershell
node skills\transport-receipt-collector\scripts\collect_transport_receipts.cjs capture-current --provider korail --crop 120,180,760,620 --output-dir outputs\receipts\2026-05 --base-name 2026-05-09_korail_receipt
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

provider별로 가능한 자동 로그인 경로를 먼저 사용한다.

- 하이패스는 기본적으로 저장된 로컬 계정 정보로 자동 로그인을 시도한다.
- KTX/SRT는 기존 예매 스킬과 같은 로컬 계정 환경변수로 자동 로그인한다.
- 세션 만료나 추가 본인확인 화면이 나오면 자동화를 중단하고 사유를 남긴다.

하이패스 상세 절차가 필요하면 `references/hipass.md`를 읽는다.

코레일/KTX 또는 SRT 승차권 구입이력 영수증 크롭 절차가 필요하면 `references/korail-srt.md`를 읽는다.

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

- 요청 기간의 provider별 영수증 대상 목록을 확인했다.
- 각 대상에 대해 provider별 산출물 저장을 시도했다.
- 저장된 파일의 경로와 실패한 항목의 사유를 보고했다.
- 비밀번호, 인증번호, 인증서 파일, 카드번호 원문이 저장소나 로그에 남지 않았다.

## References

- 하이패스 provider 상세: `references/hipass.md`
- 외부·파생 출처: `docs/attribution.md`
