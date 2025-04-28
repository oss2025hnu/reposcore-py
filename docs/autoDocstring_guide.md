# autoDocstring 사용 가이드

## 1. 설치 방법
- Visual Studio Code → Extensions → `autoDocstring` 검색 → 설치
- Python extension도 함께 설치되어 있어야 함.

## 2. 단축키 안내
| OS       | 단축키             |
|----------|--------------------|
| Windows  | Alt + Shift + 2    |
| Mac      | Option + Shift + 2 |
| Linux    | Alt + Shift + 2    |

## 3. 설정 예시 (`.vscode/settings.json`)
```json
{
  "autoDocstring.docstringFormat": "google",
  "autoDocstring.generateDocstringOnEnter": true
}
```

## 4. 생성되는 Docstring 형식 선택 방법

`autoDocstring`은 다음 세 가지 Docstring 형식을 지원합니다.

### 1. **google 스타일**
- 간단하고 명확한 Docstring 형식.
- **설정 예시**: `"autoDocstring.docstringFormat": "google"`

### 2. **numpy 스타일**
- 매개변수 및 반환값을 더 자세히 설명하는 형식.
- **설정 예시**: `"autoDocstring.docstringFormat": "numpy"`

### 3. **sphinx 스타일**
- Sphinx 문서화 도구에 적합한 형식.
- **설정 예시**: `"autoDocstring.docstringFormat": "sphinx"`


## 5. 사용 예시 *(google/numpy/sphinx 스타일)
### 적용 전:
```python
def subtract(a, b):
    return a - b
```

### 적용 후 (google 스타일)
```python
def subtract(a, b):
    """
    두 수의 차를 계산합니다.

    Parameters:
        a (int): 첫 번째 숫자
        b (int): 두 번째 숫자

    Returns:
        int: 두 숫자의 차
    """
    return a - b
```

### 적용 후 (numpy 스타일)
```python
def subtract(a, b):
    """
    두 수의 차를 계산합니다.

    Parameters
    ----------
    a : int
        첫 번째 숫자
    b : int
        두 번째 숫자

    Returns
    -------
    int
        두 숫자의 차
    """
    return a - b
```

### 적용 후 (sphinx 스타일)
```python
def subtract(a, b):
    """
    두 수의 차를 계산합니다.

    :param a: 첫 번째 숫자
    :type a: int
    :param b: 두 번째 숫자
    :type b: int
    :returns: 두 숫자의 차
    :rtype: int
    """
    return a - b
```
