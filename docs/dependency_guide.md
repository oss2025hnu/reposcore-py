# 의존성 관리 가이드

## 설치 방법
필요한 라이브러리는 requirements.txt 파일 및 requirements-dev.txt 에 명시되어 있습니다.

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

또한 이 명령어들은 devcontainer.json의 코드에 의해 자동 수행되고 있습니다.
```json
 {
    "postCreateCommand": "pip install -r requirements.txt && pip install -r requirements-dev.txt",
    ...
 }
