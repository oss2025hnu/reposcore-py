# Test

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