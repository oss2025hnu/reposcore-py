# GitHub 토큰을 환경변수로 설정하기

GitHub API 요청 제한을 피하거나 개인 리포지토리에 접근하려면 **개인 액세스 토큰**을 설정해야 합니다.

## 환경변수 `GITHUB_TOKEN` 사용

```bash
# macOS / Linux
export GITHUB_TOKEN="your_token"

# Windows PowerShell
$env:GITHUB_TOKEN="your_token"
```