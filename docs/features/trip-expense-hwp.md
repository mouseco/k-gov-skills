# 출장증빙 HWP 작성 가이드

출장·여비 정산에 필요한 출장증빙 HWP와 교통 영수증 파일을 한 묶음으로 정리하는 스킬입니다.

## 할 수 있는 일

- 출장비 정산서 HWP 템플릿 복사
- 출장일자, 장소, 출장자, 출장사유, 예산 항목 등 필드 정리
- KTX/SRT/하이패스 영수증 PNG/PDF와 연계
- HWP 내부 영수증 이미지 슬롯 교체 절차 안내
- 외부 PNG와 HWP 내부 이미지 stream의 SHA256 일치 여부 검증
- 최종 HWP와 영수증 파일을 ZIP으로 패키징

## 먼저 알아둘 점

공개판은 개인·기관 전용 기본값을 포함하지 않습니다.

- 부서명 없음
- 출장자명 없음
- 카드번호 또는 카드 뒤 4자리 없음
- 회사메일 없음
- 내부 문서번호 없음
- 실제 출장 산출물 없음

실제 업무에서 쓰는 기본값은 공개 저장소가 아니라 로컬 profile 또는 사용자의 입력으로 처리합니다.

## 입력값

필수:

- 출장일자
- 출장지 또는 출장 지역
- 출장사유
- 출장자명
- 부서명
- 사용카드 뒤 4자리 또는 카드 식별값
- 식비 차감 필요 여부와 제공 식사 횟수
- 교통편 또는 영수증 파일

선택:

- 동행 여부
- 예산 항목
- 관련문서 번호
- 승차권 취소 여부
- 취소 금액
- 수수료 자비부담 여부

## 기본 템플릿

```text
skills/trip-expense-hwp/references/trip_sample_public.hwp
```

원본은 직접 수정하지 않고, 작업 폴더로 복사한 뒤 수정합니다.

## 영수증 수집

교통 영수증은 `transport-receipt-collector`를 우선 사용합니다.

예시:

```powershell
node skills\transport-receipt-collector\scripts\collect_transport_receipts.cjs collect-latest --provider korail --start-date 2026-05-01 --end-date 2026-05-31 --row-index 1 --output-dir outputs\receipts\2026-05
```

SRT나 하이패스도 같은 collector의 provider를 사용합니다.

## HWP 이미지 검증

HWP 내부에 들어간 영수증 이미지와 제출용 PNG가 같은지 해시로 확인합니다. 파일명이나 육안 확인만으로는 완료 처리하지 않습니다.

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

## 결과물 구조

```text
outputs/trip-expense/YYYY-MM/
  trip_expense_<date>_<destination>.hwp
  receipt_1_outbound.png
  receipt_2_inbound.png
  trip_expense_<date>_<destination>.zip
```

ZIP은 최종 HWP 검증이 끝난 뒤 새로 만듭니다.

## 공개 저장소에 넣지 말 것

- 실제 출장자명
- 실제 부서명
- 실제 카드번호 또는 카드 뒤 4자리
- 실제 회사메일
- 내부 문서번호
- 실제 출장 산출물 HWP/ZIP/영수증
- 계정값, 인증정보, 토큰
