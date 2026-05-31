---
name: trip-expense-hwp
description: 출장, 출장서류, 출장증빙, 출장증빙자료, 출장비 정산서, 교통비 영수증, SRT/KTX 영수증을 바탕으로 공개 배포용 출장증빙 HWP 패키지를 작성할 때 사용한다. transport-receipt-collector와 연계해 영수증 PNG/PDF를 모으고, 출장비 정산서 HWP의 텍스트 필드와 영수증 이미지 슬롯을 검증한다.
license: See docs/attribution.md
metadata:
  category: utility
  locale: ko-KR
  phase: v0.1
---

# Trip Expense HWP

## 목적

출장·여비 정산에 필요한 출장증빙 HWP와 영수증 파일 묶음을 만든다. 사용자는 출장일, 출장지, 출장사유, 식비 차감 여부, 교통편을 알려 주고, 스킬은 템플릿 복사, 필드 채우기, 영수증 이미지 연결, 최종 검증 절차를 안내한다.

**필수 선행 스킬:** `transport-receipt-collector`가 설치되어 있어야 한다. 이 스킬은 영수증 수집을 직접 구현하지 않고, KTX/SRT/하이패스 영수증 수집은 `transport-receipt-collector`에 위임한다.

이 공개판은 개인·기관 전용 기본값을 포함하지 않는다. 부서명, 출장자명, 카드번호 뒤 4자리, 내부 문서번호, 회사메일 주소는 사용자가 매번 제공하거나 로컬 환경에서만 관리한다.

## When to use

- 출장증빙자료 또는 출장비 정산서 HWP를 만들어야 할 때
- KTX/SRT/하이패스 영수증 PNG를 출장서류와 함께 묶어야 할 때
- 출장일자, 출장지, 출장사유, 식비 차감 여부를 정리해 정산용 문서를 준비해야 할 때
- 기존 출장비 정산서 템플릿의 영수증 이미지 슬롯을 교체해야 할 때

## When not to use

- 일반 HWPX 보고서나 공문을 작성하는 경우
- 교통 영수증만 내려받으면 되는 경우
- 본인 또는 기관 권한이 없는 타인의 출장·카드·승차권 정보를 조회하려는 경우
- CAPTCHA, 2차 인증, 결제, 취소, 환불, 계정 변경을 자동화해야 하는 경우

## Linked skills

- `transport-receipt-collector` **필수**: KTX/SRT/하이패스 영수증 PDF/PNG 수집
- `read-hwp`: HWP/HWPX 텍스트 확인과 필드 검증
- `rhwp-edit`: HWP 필드 수정과 이미지 스트림 교체
- `hwpx-mouseco` 또는 HWPX 계열 스킬: 템플릿/프로파일 관리 원칙 참고

## Source template

공개 배포용 기본 템플릿:

```text
skills/trip-expense-hwp/references/trip_sample_public.hwp
```

절대 원본 템플릿을 직접 수정하지 않는다. 항상 작업 폴더로 복사한 뒤 수정한다.

권장 작업 위치:

```text
tmp/trip-expense-hwp/YYYY-MM-DD-<slug>/
outputs/trip-expense/YYYY-MM/
```

## Required input

최소 입력값:

- 출장일자
- 출장지 또는 출장 지역
- 출장사유
- 출장자명
- 부서명
- 사용카드 뒤 4자리 또는 카드 식별 방식
- 식비 차감 필요 여부와 제공 식사 횟수
- 교통편 또는 영수증 파일

선택 입력값:

- 동행 여부
- 예산 항목
- 관련문서 번호
- 승차권 취소 여부, 취소 금액, 수수료 자비부담 여부
- 회사 차량 이용 여부
- 개인차량 이용 여부

## Public defaults

공개판 기본값은 민감하지 않은 값만 둔다.

- `budget_item`: 국내여비
- `transport_base_origin`: 대구 또는 사용자가 지정한 출발지
- `companion`: ① 해당(  ) ② 해당 없음(  )
- 지정하지 않은 기관명, 부서명, 출장자명, 카드번호는 비워 둔다.

개인용 기본값을 넣고 싶으면 공개 저장소가 아니라 로컬 설정 파일이나 별도 private profile에 둔다.

## Field model

사용자 입력을 아래 구조로 정규화한다.

```json
{
  "trip_date": "YYYY-MM-DD",
  "destination_place": "",
  "destination_region": "",
  "destination_station": "",
  "traveler": "",
  "department": "",
  "business_purpose": "",
  "budget_item": "국내여비",
  "card_last4": "",
  "companion": "",
  "transport_refund": {
    "personal_card_transport": "",
    "personal_card_lodging": "",
    "personal_vehicle": ""
  },
  "deduction": {
    "company_vehicle": "",
    "meal_deduction_required": "",
    "provided_meal_count": "",
    "related_document_no": ""
  },
  "ticket_cancel": {
    "cancel_required": "",
    "cancel_amount": "",
    "fee_self_paid": ""
  },
  "receipt_labels": [],
  "receipt_images": []
}
```

## Destination station inference

출장지와 실제 영수증이 다를 수 있으므로 영수증 데이터를 우선한다.

기본 추론:

- 세종 -> 오송
- 서울 -> 서울
- 대전 -> 대전
- 부산 -> 부산
- 대구/동대구 -> 동대구

예: 대구에서 세종 출장일 때 일반적으로 `대구 ↔ 오송`, `오송 ↔ 대구` 라벨을 쓴다. 실제 승차권 출발·도착역이 다르면 영수증 출발·도착역을 우선한다.

## Receipt collection

교통 영수증은 **필수 선행 스킬인 `transport-receipt-collector`**를 사용한다. 설치되어 있지 않으면 영수증 자동 수집 단계는 진행하지 않는다.

- KTX/Korail: `collect-latest --provider korail`
- SRT: `collect-latest --provider srt`
- 하이패스: `collect --provider hipass`

원칙:

- 가능한 한 PNG를 확보한다.
- PDF는 보조 산출물로 보관한다.
- 새 출장서류를 만들 때는 기존 영수증 재사용을 사용자가 명시하지 않는 한 새로 수집한다.
- 로그인, 2차 인증, CAPTCHA가 필요하면 자동화하지 말고 사용자가 공식 화면에서 처리해야 한다.

권장 파일명:

```text
receipt_1_outbound.png
receipt_2_inbound.png
receipt_3_local_transport.png
```

## Editing strategy

1. 원본 템플릿을 작업 폴더로 복사한다.
2. `read-hwp` 또는 HWP 분석 도구로 현재 텍스트와 필드 위치를 확인한다.
3. 안정적인 라벨 앵커를 기준으로 값 셀을 수정한다.
4. 영수증 이미지는 기존 이미지 슬롯 교체를 우선한다.
5. 최종 HWP를 다시 읽어 주요 필드가 바뀌었는지 확인한다.
6. 영수증 PNG와 HWP 내부 `BinData` 이미지가 같은지 해시로 검증한다.

수정 대상 라벨 예시:

- 출장일자
- 장 소
- 출장자
- 출장사유
- 예산 항목
- 사용카드 뒤 4자리
- 식비차감 필요여부
- 제공 횟수
- 관련문서 번호
- 승차권 취소여부
- 취소 금액
- 수수료 자비부담
- 관련 영수증

## Image rule

HWP 이미지 삽입은 깨지기 쉽다. 가장 안전한 방식은 템플릿에 이미 있는 영수증 이미지 슬롯을 교체하는 것이다.

- 최선: 기존 영수증 이미지 placeholder 교체
- 가능: 고정 크기 빈 이미지 박스가 있는 공개 템플릿 사용
- 피할 것: 매번 새 floating image를 병합 셀에 삽입

현재 공개 템플릿은 영수증 이미지 슬롯이 `BinData/BIN0001.png`, `BinData/BIN0002.png` 형태일 수 있다. 실제 파일마다 stream 이름은 다를 수 있으므로 작업 전 반드시 확인한다.

`olefile.write_stream`을 사용할 때는 기존 stream과 byte length 제약이 있을 수 있다. 새 PNG가 짧으면 trailing null padding을 붙이고, 길면 PNG 크기나 압축을 조정한다.

## Mandatory receipt consistency check

패키징 전, HWP에 들어간 영수증 이미지와 함께 제출할 PNG가 같은지 SHA256으로 검증한다.

검증 규칙:

1. 원본 영수증 PNG bytes를 읽는다.
2. HWP `BinData` stream bytes를 읽는다.
3. HWP stream의 trailing null만 제거한다.
4. 두 SHA256이 같은지 비교한다.
5. 다르면 패키징하지 말고 이미지 교체부터 다시 한다.

예시:

```python
from pathlib import Path
import hashlib
import olefile

checks = [
    (Path(r"<receipt_1_outbound.png>"), ["BinData", "BIN0001.png"]),
    (Path(r"<receipt_2_inbound.png>"), ["BinData", "BIN0002.png"]),
]
hwp = Path(r"<final.hwp>")
with olefile.OleFileIO(str(hwp)) as ole:
    for png, stream in checks:
        source = png.read_bytes()
        embedded = ole.openstream(stream).read().rstrip(b"\x00")
        assert hashlib.sha256(source).hexdigest() == hashlib.sha256(embedded).hexdigest(), (png, stream)
```

## Packaging

최종 산출물은 같은 폴더에 모은다.

```text
outputs/trip-expense/YYYY-MM/
  trip_expense_<date>_<destination>.hwp
  receipt_1_outbound.png
  receipt_2_inbound.png
  trip_expense_<date>_<destination>.zip
```

ZIP은 HWP 이미지 교체와 해시 검증이 끝난 뒤 마지막에 다시 만든다. 수정 전 ZIP을 재사용하지 않는다.

## Email preparation

메일 발송은 외부 action이다. 발송 전 아래를 요약하고 확인한다.

- 최종 HWP 경로
- 첨부 영수증 경로
- ZIP 경로
- 수신자
- 제목
- 첨부 개수

사용자가 이번 메시지에서 특정 수신자에게 보내라고 명확히 지시했고 수신자가 알려져 있으면 보낼 수 있다. 그 외에는 확인을 받는다.

## Safety and public hygiene

공개 저장소에 넣지 않는다.

- 실제 부서명
- 실제 출장자명
- 실제 카드번호 또는 카드 뒤 4자리
- 회사메일 주소
- 내부 문서번호
- 실제 출장 산출물 HWP/ZIP/영수증
- 계정값, 인증정보, 토큰

공개 예시는 placeholder만 사용한다.

## Done criteria

완료 조건:

- 원본 템플릿을 덮어쓰지 않았다.
- 최종 HWP가 `outputs/trip-expense/YYYY-MM/`에 있다.
- 필요한 영수증 PNG/PDF가 있거나 blocker가 명확하다.
- 주요 필드를 최종 HWP에서 다시 확인했다.
- HWP 내부 영수증 이미지와 외부 PNG의 SHA256이 일치한다.
- ZIP은 마지막 HWP 이미지 교체 후 새로 만들었다.
- 메일 발송은 사용자 승인 범위 안에서 처리했다.

## Failure modes

- HWP 필드 위치를 안전하게 특정하지 못하면 문서를 손상시키기 전에 멈춘다.
- 영수증 수집에 로그인/2FA/CAPTCHA가 필요하면 공식 화면에서 사용자가 처리해야 한다.
- 이미지 삽입이 불안정하면 HWP와 영수증 파일을 패키지로 보존하고, 템플릿 placeholder 보완을 다음 작업으로 남긴다.
