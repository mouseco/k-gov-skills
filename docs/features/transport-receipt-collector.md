# 교통비 증빙 수집 가이드

출장·여비·교통비 정산에 필요한 교통 영수증을 PDF/PNG/JSON 산출물로 정리하는 스킬입니다.

현재 지원 provider는 **하이패스, SRT, KTX/Korail** 3종입니다.

## 이 기능으로 할 수 있는 일

- 하이패스 사용내역 조회 및 영수증 PDF/PNG 저장
- SRT 이용내역 조회 및 영수증 PNG 저장
- KTX/Korail 승차권 구입이력 조회
- KTX/Korail 로컬 커넥터 기반 영수증 데이터 조회
- KTX/Korail 코레일톡 스타일 영수증 PNG 저장
- 월별 폴더와 일관된 파일명으로 증빙 정리
- headless 모드 또는 로컬 커넥터 기반 백그라운드 수집
- 실패 항목과 실패 사유 요약

## 먼저 알아둘 점

- 하이패스는 `KGOV_HIPASS_ID`, `KGOV_HIPASS_PW`로 자동 로그인합니다.
- SRT는 로컬 SRT 계정 환경변수를 사용합니다.
- KTX/Korail은 `ktx-booking` 스킬을 먼저 설치한 뒤, 그 스킬의 helper를 사용하는 로컬/private connector로 처리합니다. 공개 저장소에는 Korail 내부 호출 세부 구현을 두지 않습니다.
- 추가 본인확인, CAPTCHA, 인증서 조작, 2차 인증 자동 통과는 공개 스킬 범위 밖입니다.
- 계정 비밀번호, 인증번호, 카드번호 원문, 승차권 토큰은 저장소나 로그에 남기지 않습니다.

## 입력

- provider: `hipass`, `korail`, `srt`
- 시작일과 종료일
- 저장 폴더
- 선택 항목: row index 또는 전체 저장 확장
- 선택 옵션: `--headless`, `--auth-mode session`, `--list-only`, `--no-render-local`

## 출력

- 하이패스: PDF + PNG
- SRT: PNG
- KTX/Korail: 코레일톡 스타일 PNG + redacted JSON
- 성공·실패 요약
- 실패한 항목의 사유

예시 출력 구조:

```text
outputs/receipts/2026-05/
  2026-05-03_hipass_서울TG-동대구TG_12800.pdf
  2026-05-03_hipass_서울TG-동대구TG_12800.png
  2026-04-21_korail_오송-동대구_24800.png
  2026-04-21_korail_오송-동대구_24800.json
```

## 기본 흐름

1. provider와 기간을 확인합니다.
2. provider별 인증 정보를 읽습니다.
3. 추가 본인확인이 나오면 자동화를 중단합니다.
4. 사용내역 또는 승차권 구입이력을 조회합니다.
5. 대상 건의 영수증 데이터를 조회합니다.
6. 제출 가능한 PNG/PDF 산출물을 저장합니다.
7. 저장된 파일과 실패 항목을 요약합니다.

## 하이패스

하이패스는 ID/비밀번호 자동 로그인을 기본값으로 합니다.

- 기본적으로 `KGOV_ENV_FILE` 또는 사용자 홈 아래의 환경파일(`$HOME/.openclaw/.env`)을 로드합니다.
- `KGOV_HIPASS_ID`, `KGOV_HIPASS_PW`를 읽습니다.
- 로그인 후 사용내역 조회 화면에 접근합니다.
- 날짜 범위를 적용해 조회합니다.
- 대상 건의 영수증 출력 화면 또는 팝업을 엽니다.
- PDF와 PNG를 저장합니다.

```powershell
node skills\transport-receipt-collector\scripts\collect_transport_receipts.cjs collect --provider hipass --start-date 2026-05-01 --end-date 2026-05-31 --row-index 1 --headless --output-dir outputs\receipts\2026-05
```

## SRT

SRT는 자동 로그인 후 이용내역 조회와 영수증 화면 캡처를 지원합니다.

```powershell
node skills\transport-receipt-collector\scripts\collect_transport_receipts.cjs collect-latest --provider srt --start-date 2026-02-09 --end-date 2026-05-09 --row-index 1 --output-dir outputs\receipts\2026-05
```

## KTX/Korail

KTX/Korail은 공개 저장소에 내부 호출 세부사항을 포함하지 않습니다. 공개 스킬은 `ktx-booking` 스킬의 helper를 사용하는 로컬/private connector를 호출하는 구조만 제공합니다.

기본 실행은 실제 코레일톡 저장본 기준으로 확정한 **v3 코레일톡 스타일 영수증 PNG**와 redacted JSON을 저장합니다. 이 기능을 쓰려면 먼저 `ktx-booking` 스킬을 설치하고, `KGOV_KORAIL_CONNECTOR`에 그 helper를 불러 쓰는 영수증 connector 스크립트 경로를 지정합니다.

### KTX/Korail 경로 설정 빠른 점검

가장 많이 막히는 부분은 `KGOV_KORAIL_CONNECTOR`입니다. 이 값은 **폴더가 아니라 실행 가능한 Python connector 파일 경로**여야 합니다.

권장 실행 위치는 `k-gov-skills` 저장소 루트입니다. 즉 `README.md`와 `skills` 폴더가 보이는 폴더에서 실행합니다.

```powershell
cd C:\path\to\k-gov-skills
```

connector는 가능하면 절대경로로 지정합니다.

```powershell
$env:KGOV_KORAIL_CONNECTOR="C:\Users\<you>\.openclaw\private-connectors\korail_receipt_connector.py"
```

`$HOME`을 써도 되지만, 경로 문제를 확인할 때는 먼저 절대경로가 안전합니다.

```powershell
$env:KGOV_KORAIL_CONNECTOR="$HOME\.openclaw\private-connectors\korail_receipt_connector.py"
```

실행 전 아래 두 줄이 모두 `True` 또는 help 출력을 보여야 합니다.

```powershell
Test-Path $env:KGOV_KORAIL_CONNECTOR
python $env:KGOV_KORAIL_CONNECTOR --help
```

그다음 목록 조회부터 확인합니다.

```powershell
node skills\transport-receipt-collector\scripts\collect_transport_receipts.cjs collect-latest --provider korail --start-date 2025-05-11 --end-date 2026-05-11 --list-only
```

목록이 보이면 저장을 실행합니다.

```powershell
node skills\transport-receipt-collector\scripts\collect_transport_receipts.cjs collect-latest --provider korail --start-date 2025-05-11 --end-date 2026-05-11 --row-index 20 --output-dir outputs\receipts\2026-05
```

렌더링 없이 API 응답 확인만 하려면:

```powershell
node skills\transport-receipt-collector\scripts\collect_transport_receipts.cjs collect-latest --provider korail --start-date 2025-05-11 --end-date 2026-05-11 --row-index 1 --no-render-local
```

### KTX/Korail 경로 오류 체크리스트

- `Korail receipt collection requires a local/private connector`가 나오면 `KGOV_KORAIL_CONNECTOR`가 비어 있거나 `--connector`를 주지 않은 상태입니다.
- `Korail connector not found`가 나오면 connector 파일 경로가 틀렸습니다. 폴더 경로가 아니라 `.py` 파일까지 포함해야 합니다.
- `python ... --help`가 실패하면 transport 스킬 문제가 아니라 connector 설치 또는 Python 실행 환경 문제입니다.
- `--output-dir outputs\receipts\2026-05` 같은 상대경로는 현재 셸 위치 기준으로 해석됩니다. 헷갈리면 `C:\path\to\receipts\2026-05`처럼 절대경로를 사용합니다.
- `ktx-booking` 스킬이 설치되어 있지 않으면 connector가 내부 helper를 찾지 못할 수 있습니다. 이 경우 `ktx-booking` 설치 경로와 connector 안의 import 경로를 먼저 확인합니다.

## 결과 확인 포인트

- PDF/PNG가 같은 거래를 가리키는가
- 파일명에 날짜, provider, 구간, 금액이 들어갔는가
- 조회 기간이 사용자가 요청한 기간과 맞는가
- 실패 항목의 사유가 남아 있는가
- 계정정보, 카드번호 원문, 승차권 토큰이 로그에 남지 않았는가

## 주의할 점

- ID/PW 환경변수가 없으면 로컬 환경변수에 먼저 설정합니다.
- 자동 로그인 실패나 세션 만료가 발생할 수 있습니다.
- 조회 결과가 없으면 기간, 날짜 기준, 카드/승차권 조건을 다시 확인합니다.
- 하이패스 PNG 저장이 실패하면 PDF 첫 페이지를 PNG로 렌더링합니다.
- KTX/Korail은 `ktx-booking` helper와 외부 서비스 변경 시 재검증이 필요합니다.

## 관련 파일

```text
skills/transport-receipt-collector/
  SKILL.md
  references/hipass.md
  references/korail-srt.md
  scripts/collect_transport_receipts.cjs
docs/features/transport-receipt-collector.md
```
