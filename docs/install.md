# 설치 가이드

`k-gov-skills`는 표준 `SKILL.md` 구조를 사용합니다. Claude Code, Codex, Cursor, OpenClaw 등 Agent Skills를 읽는 도구에 필요한 스킬만 설치할 수 있습니다.

## 가장 빠른 설치

Node.js가 있다면 [`skills`](https://github.com/vercel-labs/skills) CLI를 사용하는 방법이 가장 간단합니다.

```bash
# 저장소에서 설치 가능한 스킬 확인
npx skills add mouseco/k-gov-skills --list

# 스킬 하나를 전역 설치
npx skills add mouseco/k-gov-skills --skill official-report-skillset -g

# 여러 스킬을 한 번에 전역 설치
npx skills add mouseco/k-gov-skills \
  --skill official-report-skillset \
  --skill deep-research-pro \
  --skill hwpx-mouseco \
  -g

# 13개 스킬 전체 설치
npx skills add mouseco/k-gov-skills --all -g
```

설치할 에이전트를 직접 지정하려면 `-a` 옵션을 사용합니다.

```bash
npx skills add mouseco/k-gov-skills \
  --skill gov-meeting-minutes \
  -a claude-code \
  -a codex \
  -g
```

> `skills` CLI는 기본적으로 익명 설치 통계를 수집합니다. 원하지 않으면 `DISABLE_TELEMETRY=1` 환경변수를 설정하세요.

## Git으로 직접 설치

CLI를 사용하지 않는 환경에서는 저장소를 복제한 뒤 필요한 `skills/<skill-name>` 폴더를 에이전트의 스킬 경로로 복사하면 됩니다.

```bash
git clone https://github.com/mouseco/k-gov-skills.git
```

예를 들어 Codex의 전역 스킬 경로에 보고서 스킬을 설치하려면 다음과 같이 복사합니다.

```bash
cp -R k-gov-skills/skills/official-report-skillset ~/.codex/skills/
```

에이전트마다 스킬 경로가 다를 수 있으므로 해당 도구의 Agent Skills 문서를 함께 확인하세요.

## 추천 조합

### 보고서 작성

```bash
npx skills add mouseco/k-gov-skills \
  --skill deep-research-pro \
  --skill official-report-skillset \
  --skill hwpx-mouseco \
  -g
```

공식 근거 조사 → 의사결정용 보고서 구조화 → HWPX 산출 순서로 연결합니다.

### 회의와 후속 기록

```bash
npx skills add mouseco/k-gov-skills \
  --skill gov-meeting-minutes \
  --skill official-report-skillset \
  -g
```

전사 원문을 회의 기록으로 정리한 뒤, 필요한 경우 결과보고나 후속조치 문서로 이어갑니다.

### 출장 정산

```bash
npx skills add mouseco/k-gov-skills \
  --skill transport-receipt-collector \
  --skill trip-expense-hwp \
  -g
```

`trip-expense-hwp`는 `transport-receipt-collector`와 함께 설치해야 합니다. 로그인·본인확인·CAPTCHA·결제·취소는 자동화 범위에 포함하지 않습니다.

## 설치 후 확인

1. 에이전트를 새 세션으로 시작합니다.
2. 설치한 스킬 이름으로 작업을 요청합니다.
3. 스킬이 요구하는 입력값과 제한사항을 확인합니다.
4. HWPX·PDF·영수증처럼 파일을 만드는 작업은 결과 파일을 실제로 열어 확인합니다.
5. API 키가 필요한 스킬은 저장소가 아니라 환경변수나 에이전트의 시크릿 저장소에 값을 둡니다.

## 저장소 자체 검증

저장소를 수정했다면 루트에서 다음 명령을 실행합니다.

```bash
python3 scripts/validate_skills.py
python3 -m unittest discover -s tests -p "test_*.py"
python3 -m unittest discover -s skills/kosis-stats/tests -p "test_*.py"
```

Windows에서는 다음 명령을 사용할 수 있습니다.

```powershell
python -X utf8 scripts\validate_skills.py
python -X utf8 -m unittest discover -s tests -p "test_*.py"
python -X utf8 -m unittest discover -s skills\kosis-stats\tests -p "test_*.py"
```
