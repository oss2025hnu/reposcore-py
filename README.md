# reposcore-py
A CLI for scoring student participation in an open-source class repo, implemented in Python.

## Install dependencies

```bash
make venv
make requirements
```

## Usage
> **주의**: 이 섹션은 자동 동기화됩니다. 직접 수정하지 마세요.

```bash
'{{ help_output }}'


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

점수로 인정 가능한 PR의 개수\
$P_{\text{valid}} = P_{fb} + \min(P_d, 3P_{fb})$

점수로 인정 가능한 이슈의 개수\
$I_{\text{valid}} = \min(I_{fb} + I_d, 4 \times P_{\text{valid}})$

PR의 점수를 최대로 하기 위해 기능/버그 PR을 먼저 계산한 후 문서 PR을 계산합니다.

기능/버그 PR을 최대로 포함:\
$P_{fb}^* = \min(P_{fb}, P_{\text{valid}})$

남은 개수에서 문서 PR을 포함:\
$P_d^* = P_{\text{valid}} - P_{fb}^*$

이슈의 점수를 최대로 하기 위해 기능/버그 이슈를 먼저 계산한 후 문서 이슈를 계산합니다.

기능/버그 이슈를 최대로 포함:\
$I_{fb}^* = \min(I_{fb}, I_{\text{valid}})$

남은 개수에서 문서 이슈를 포함:\
$I_d^* = I_{\text{valid}} - I_{fb}^*$

최종 점수 계산 공식:\
$S = 3P_{fb}^* + 2P_d^* + 2I_{fb}^* + 1I_d^*$
