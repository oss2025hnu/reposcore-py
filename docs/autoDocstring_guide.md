# autoDocstring 사용 가이드
Python 함수, 클래스, 메서드에 대해 **자동으로 Docstring(주석)을 생성**해주는 VS Code 확장 기능인 **autoDocstring**의 설치 방법과 사용법을 안내합니다.

## 1. 설치 방법
해당 프로젝트는 Codespace 또는 Devcontainer 환경에서 열면 `autoDocstring` 확장 기능이 자동으로 설치되도록 설정되어 있습니다.

만약 로컬 환경에서 사용하는 경우에는 다음과 같이 수동 설치가 필요합니다:

1. VS Code 좌측 Extensions 탭(또는 `Ctrl+Shift+X`) 클릭  
2. `autoDocstring` 검색 후 설치  
3. Python 확장도 함께 설치되어 있어야 정상 동작합니다.

## 2. 단축키 안내
Docstring을 자동으로 생성하려면 함수 정의에 커서를 놓고 아래 단축키를 입력하세요:

- **Windows / Linux**: `Alt + Shift + 2`
- **macOS**: `Cmd + Shift + 2`

## 3. 지원되는 Docstring 형식
autoDocstring은 다양한 포맷을 지원합니다. 아래 포맷 중에서 원하는 형식을 선택해 사용할 수 있습니다:

- **google** (기본값)
- **numpy**
- **sphinx** (reStructuredText)
- **docblock** (JavaDoc-style)
- **googleTyped**, **numpyTyped** (타입 힌트 포함)

## 4. 실사용 예시 및 생성 결과
Docstring은 함수 선언에 커서를 둔 후 단축키를 입력하면 자동으로 생성됩니다.  
아래는 동일한 함수에 대해 스타일별로 생성된 결과 예시입니다.

### Google 스타일 (기본값)
입력:
```python
def subtract(a: int, b: int) -> int:
```

→ 생성 결과:
```python
def subtract(a: int, b: int) -> int:
    """
    Parameters:
        a (int): 첫 번째 숫자
        b (int): 두 번째 숫자

    Returns:
        int: 두 수의 차
    """
    return a - b
```
위 예시는 autoDocstring의 기본 설정 기준입니다.
현재 프로젝트에서는 includeDescription, includeTypeHint 등의 설정이 활성화되어 있어 실제 생성 결과는 다를 수 있습니다.

### NumPy 스타일
입력:
```python
def subtract(a: int, b: int) -> int:
```

→ 생성 결과:
```python
def subtract(a: int, b: int) -> int:
    """
    Parameters
    ----------
    a : int
        첫 번째 숫자
    b : int
        두 번째 숫자

    Returns
    -------
    int
        두 수의 차
    """
    return a - b
```

## 5. settings.json 설정 예시
해당 프로젝트는 `.devcontainer/devcontainer.json` 파일을 통해  
autoDocstring 확장 기능이 자동으로 설치되며, 기본값이 아닌 아래와 같은 설정이 미리 적용되어 있습니다:

```json
{
    "autoDocstring.docstringFormat": "google",
    "autoDocstring.generateDocstringOnEnter": true,
    "autoDocstring.quoteStyle": "\"\"\"",
    "autoDocstring.includeName": true,
    "autoDocstring.includeTypeHint": true,
    "autoDocstring.startOnNewLine": false
}
```
위 설정은 프로젝트의 기본 개발 환경에 포함되어 있으며,
로컬 환경에서 동일한 설정을 사용하려면 VS Code의 `settings.json`에 수동으로 추가할 수 있습니다.


**설정 위치:** VS Code 하단 톱니바퀴 → Command Palette → `Preferences: Open Settings (JSON)`

Docstring 스타일은 팀의 코딩 컨벤션이나 린터 설정에 따라 달라질 수 있으므로,  
상황에 맞게 포맷을 선택하여 설정해 주세요.  

autoDocstring을 통해 문서화를 자동화하고, 개발 효율을 높여보세요.