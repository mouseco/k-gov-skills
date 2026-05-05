# HWPX 구조 참고 노트

## 패키지 구조

- HWPX는 KS X 6101 기반 OWPML 패키지 포맷이다. 단순 ZIP+XML이 아니라 참조 구조와 패키징 무결성을 함께 본다.
- `mimetype`은 일반적으로 `application/hwp+zip`이며 ZIP 첫 엔트리와 무압축(`ZIP_STORED`) 유지를 기본 원칙으로 한다.
- `META-INF/manifest.xml`, `container.xml`, `container.rdf`는 패키지 목록과 루트 문서 관계를 담는다.
- `BinData/`는 이미지, OLE, 기타 바이너리 리소스를 담는다. 의도 없이 누락하지 않는다.
- `Preview/PrvText.txt`, `Preview/PrvImage.png`는 미리보기 정보다. 필요 시 갱신하되 암호 문서에서는 보존 여부를 신중히 본다.
- `Scripts/`, `settings.xml`, `version.xml`이 있으면 임의 삭제하지 않는다.

## Contents 핵심 파일

- `Contents/content.hpf`
  - OPF 기반 패키지 명세다.
  - `manifest`는 파일 목록이고 `spine`은 읽기 순서 기준이다.
- `Contents/header.xml`
  - 문서 전역 글꼴, 글자모양, 문단모양, 스타일, 번호 등 참조 테이블이다.
  - `secCnt`와 실제 `section*.xml` 개수 정합성을 확인한다.
  - `compatibleDocument`, `docOption`, `metaTag`, 변경 추적 관련 정보는 보존한다.
- `Contents/section*.xml`
  - 실제 본문 구역이다. 페이지 단위가 아니라 구역 단위다.
  - 문단은 `<hp:p>`, 실행 단위는 `<hp:run>`, 텍스트는 `<hp:t>` 중심이다.
  - `run` 아래에는 `t`뿐 아니라 `tbl`, `pic`, `ctrl`, `secPr` 등이 올 수 있다.
  - `<hp:t>`는 mixed content일 수 있으므로 `tab`, `lineBreak`, `nbSpace`, `fwSpace`를 단순 삭제하지 않는다.
  - 표, 글상자 등 특수 구조는 내부 `subList`와 문단 목록을 가진다.

## 참조 구조

- 문단 `<hp:p paraPrIDRef>`는 `header.xml/refList/paraProperties`를 참조한다.
- 문단 `<hp:p styleIDRef>`는 `header.xml/refList/styles`를 참조한다.
- 실행 `<hp:run charPrIDRef>`는 `header.xml/refList/charProperties`를 참조한다.
- 스타일 보존 문서는 새 노드를 무리하게 재구성하기보다 기존 문단/런 구조를 복제해 최소 수정한다.

## 글머리와 내어쓰기

- 글머리 문자열은 `앞머리 공백 + 글머리 기호 + 글머리 뒤 공백` 전체다.
- 앞머리 공백은 텍스트 표현 자원이고, 내어쓰기는 줄바꿈 이후 본문 정렬을 위한 문단 속성이다.
- 내어쓰기 적용 시 기존 왼쪽 여백(`hc:left`)을 임의로 늘리지 않는다.
- 문단별 실제 prefix와 `charPrIDRef`, 글자 크기, 장평, 자간, 글꼴 참조를 기준으로 폭을 계산한다.
- `□ = 30pt`, `ㅇ = 38.9pt` 같은 값은 특정 문서 관찰값일 뿐 전역 상수로 쓰지 않는다.
- 계산값이 같은 문단만 같은 새 `paraPr`를 공유하고 다른 문단은 별도 `paraPr`를 만든다.
- `lineSegArray`는 편집기 레이아웃 캐시일 수 있으므로 텍스트 길이·문단 속성 변경 후 오래된 값이 남아 있으면 제거하거나 재계산되도록 처리한다.

## 최소 검증

- ZIP 재패키징 정상 여부
- `mimetype` 첫 엔트리 및 무압축 여부
- 주요 XML 및 `content.hpf` 파싱 가능 여부
- `content.hpf manifest/spine` 참조 정합성
- `header.xml` 참조 구조 유지 여부
- 수정한 문단, 표, 그림이 의도대로 남아 있는지 여부
- `BinData/`, `Preview/`, `Scripts/` 등 기존 자산 누락 여부
