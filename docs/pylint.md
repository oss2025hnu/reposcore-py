## 개발 환경 설정

### 1. pylint 설치
pylint는 개발자용 도구가 정의된 `requirements-dev.txt`에 정의되어 있습니다. 아래 명령어를 통해 개발자용 도구를 설치합니다.

```bash
pip install -r requirements-dev.txt
```

또한 `.devcontainer/devcontainer.json`에도 pylint가 추가되어 있어 `.pylintrc` 기반 lint 검사를 자동 적용 중입니다.

---

### 2. 코드 검사 도구 (pylint) 안내

이 프로젝트는 `pylint`를 사용하여 기본적인 문법 오류만 검사합니다.  
다른 린팅 규칙은 `.pylintrc` 파일을 통해 비활성화되어 있습니다.

활성화된 검사 항목:
- 문법 오류 (`syntax-error`)
- 정의되지 않은 변수 사용 (`undefined-variable`)

아래 명령어로 위치를 지정하여 코드를 검사할 수 있습니다.
ex) reposcore 폴더 내 파일에 대한 검사
```bash
pylint reposcore --rcfile=.pylintrc
```