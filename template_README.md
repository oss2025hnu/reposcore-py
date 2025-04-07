# reposcore-py
A CLI for scoring student participation in an open-source class repo, implemented in Python.

>
> **주의**
> - 절대로 `README.md`의 내용을 직접 수정하지 말 것! (템플릿에서 자동으로 생성하는 스크립트 추가됨)
> - 반드시 `template_README.md`의 내용을 수정한 후 `make readme` 실행하여 내용을 갱신해야 함.
>

## Install dependencies

```bash
make venv
make requirements
```

## Usage
아래는 `python -m reposcore -h` 또는 `python -m reposcore --help` 실행 결과를 붙여넣은 것이므로
명령줄 관련 코드가 변경되면 아래 내용도 그에 맞게 수정해야 함.

```
{{ usage }}
```

## Test

이 저장소에서 기본적인 동작 이상 여부를 테스트하기 위한 자동화된 테스트 스위트를 사용할 수 있습니다.

### Install dependencies

테스트 과정을 진행하기 위해서 먼저 설치 후 실행.
```bash
make venv
make requirements
```

### Run Tests
다음 명령어를 수행하면 테스트가 진행됩니다.
```bash
make test
```

### How to Read Test Results

테스트 실행 결과는 다음과 같은 형식으로 출력됩니다.
```
=== test session starts ===
...
collected 3 items

tests/test_analyzer.py ..F [100%]

=== FAILURES ===
tests/test_analyzer.py::test_analyzer_initialization
```
- `.` : 테스트 성공
- `F` : 테스트 실패
- `[100%]` : 전체 테스트 실행 비율

자세한 실패 원인은 터미널 로그에서 확인할 수 있습니다.

### Writing New Tests

새로운 기능을 추가하면 `tests/` 디렉터리에 테스트 파일을 작성해야 합니다.

#### 예시 테스트 파일 (`tests/test_analyzer.py`)
```python
import pytest
from reposcore.analyzer import RepoAnalyzer

@pytest.fixture
def analyzer():
    return RepoAnalyzer("oss2025hnu/reposcore-py")

def test_initialization(analyzer):
    assert analyzer.repo == "oss2025hnu/reposcore-py"
    assert isinstance(analyzer.scores, dict)

def test_add_score(analyzer):
    analyzer.add_score("jass2345", 10)
    assert analyzer.scores["jass2345"] == 10
```
원하는 테스트를 추가한 후 `make test`를 실행하여 검증하세요.

## Score Formula
아래는 PR 개수와 이슈 개수의 비율에 따라 점수로 인정가능한 최대 개수를 구하고 각 배점에 따라 최종 점수를 산출하는 공식이다.

- $P_{fb}$ : 기능 또는 버그 관련 Merged PR 개수 (**3점**) ($P_{fb} = P_f + P_b$)  
- $P_d$ : 문서 관련 Merged PR 개수 (**2점**)  
- $I_{fb}$ : 기능 또는 버그 관련 Open 또는 해결된 이슈 개수 (**2점**) ($I_{fb} = I_f + I_b$)  
- $I_d$ : 문서 관련 Open 또는 해결된 이슈 개수 (**1점**)

$P_{\text{valid}} = P_{fb} + \min(P_d, 3P_{fb}) ~~\quad$ 점수 인정 가능 PR 개수\
$I_{\text{valid}} = \min(I_{fb} + I_d, 4 \times P_{\text{valid}}) \quad$ 점수 인정 가능 이슈 개수

PR의 점수를 최대로 하기 위해 기능/버그 PR을 먼저 계산한 후 문서 PR을 계산합니다.

$P_{fb}^* = \min(P_{fb}, P_{\text{valid}}) \quad$ 기능/버그 PR 최대 포함\
$P_d^* = P_{\text{valid}} - P_{fb}^* ~~\quad$ 남은 개수에서 문서 PR 포함

이슈의 점수를 최대로 하기 위해 기능/버그 이슈를 먼저 계산한 후 문서 이슈를 계산합니다.

$I_{fb}^* = \min(I_{fb}, I_{\text{valid}}) \quad$ 기능/버그 이슈 최대 포함\
$I_d^* = I_{\text{valid}} - I_{fb}^* ~~\quad$ 남은 개수에서 문서 이슈 포함

최종 점수 계산 공식:\
$S = 3P_{fb}^* + 2P_d^* + 2I_{fb}^* + 1I_d^*$

## 토큰 생성 방법
`docs/github-tokne-guide.md` 문서를 참고 부탁드립니다.

## 프로젝트 작성 시 주의사항

### 1. 이슈 선점 및 작업 기간
- **버그/기능**
  - 선점 유지: 24시간 (타인이 PR 작성 권한 선점 가능)  
  - 책임자 우선권: 댓글 후 48시간 (이후 타인에게 우선권 이관)
- **문서**
  - 선점 유지: 24시간

### 2. 이슈 템플릿 & 레이블
- 올바른 템플릿(`bug`, `feature`, `document`) 선택 시 자동 레이블 부여  
- 레이블 수동 변경 금지 (잘못 변경 시 이슈 반려)

### 3. PR 작성 가이드
- PR에는 레이블 자동 부여 없음 → 이슈와 동일한 레이블 수동 추가  
- PR 본문 최상단에 “참조 이슈 #번호” 링크 필수

### 4. 동시 작업 제한
- 한 저장소 내 개인당 동시 작업 이슈 최대 1개  
- 다른 저장소(`reposcore-js` 등)에서는 별도 1개 작업 가능

### 5. 이슈 작성 가이드
- 문제를 구체적으로 기술 (관련 파일/함수/라인 등)  
- 해결 후 기대 동작 및 결과 명시  
- 솔루션 방향 및 구현 제안 포함
