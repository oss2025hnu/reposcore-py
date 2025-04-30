## 한국 시간대(Asia/Seoul) 설정 가이드

### Codespaces에서 한국 시간대 적용하기

Codespaces 터미널에서 아래 명령어를 입력하세요:

```bash
export TZ=Asia/Seoul
```

또는 `.bashrc` / `.zshrc` 파일에 아래 내용을 추가하면 자동 적용됩니다:

```bash
echo 'export TZ=Asia/Seoul' >> ~/.bashrc
source ~/.bashrc
```

### devcontainer.json을 통한 한국 시간대 설정

Codespaces의 개발 환경은 `devcontainer.json`을 통해 설정할 수 있습니다. 저장소 루트의 `.devcontainer/devcontainer.json` 파일에 다음을 추가하여 한국 시간대(`Asia/Seoul`)를 설정하세요:

```json
{
  "name": "Your Codespace",
  "image": "mcr.microsoft.com/devcontainers/base:ubuntu",
  "runArgs": ["--env", "TZ=Asia/Seoul"],
  "containerEnv": {
    "TZ": "Asia/Seoul"
  }
}
```

- **`runArgs`**: 컨테이너 실행 시 환경 변수 설정.
- **`containerEnv`**: 컨테이너 내부의 환경 변수 정의.
- **주의**: `devcontainer.json`이 없는 경우, 저장소에 `.devcontainer/` 디렉토리와 파일을 생성해야 합니다. 이 작업은 별도 이슈로 처리하세요.

설정 후 Codespaces를 재빌드하면 한국 시간대가 자동 적용됩니다:

```bash
# Codespaces 재빌드
gh codespace rebuild
```

---

### 주의사항

- Python `datetime.now()`는 OS의 기본 시간대를 따르�므로 위 설정이 되어 있어야 한국 시간으로 로그가 표시됩니다.
- 시스템 시간 설정이 불가한 환경이라면 `datetime.now(tz=...)` 사용을 고려할 수 있습니다.