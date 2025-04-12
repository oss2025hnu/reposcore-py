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

---

### GitHub Actions에서 시간대 변경하기

`.github/workflows/ci.yml` 같은 워크플로우 파일에 다음을 추가합니다:

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Set timezone to Asia/Seoul
        run: |
          sudo ln -sf /usr/share/zoneinfo/Asia/Seoul /etc/localtime
          echo "Asia/Seoul" | sudo tee /etc/timezone
```

---

### 주의사항

- Python `datetime.now()`는 OS의 기본 시간대를 따르므로 위 설정이 되어 있어야 한국 시간으로 로그가 표시됩니다.
- 시스템 시간 설정이 불가한 환경이라면 `datetime.now(tz=...)` 사용을 고려할 수 있습니다.

