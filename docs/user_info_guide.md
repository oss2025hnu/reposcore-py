# 📘 `--user-info` 사용 가이드

이 문서는 CLI에서 `--user-info` 옵션을 사용할 때 필요한 JSON 파일 형식과 사용 방법을 안내합니다.

---

## ✅ JSON 스키마 예시

```json
{
  "github_username": "alice",
  "display_name": "Alice"
}
```

또는:

```json
{
  "github_username": "bob42"
}
```

| 필드 이름             | 설명                             | 필수 유문          |                        |    |
| ----------------- | ------------------------------ | -------------- | ---------------------- | -- |
| `github_username` | GitHub 사용자명. 내부 프리플 연동에 사용됩니다. | ✅              |                        |    |
| `display_name`    | Í                              | `display_name` | \xcd9c력에 사용할 표시 이름입니다. | ⛘️ |

---

## ❌ 잘못된 형식 입력 예시 및 에러 메시지

| 입력 JSON                                        | 예상 에러 메시지                                        |
| ---------------------------------------------- | ------------------------------------------------ |
| `{}`                                           | `Missing required field: github_username`        |
| `{"github_username": 123}`                     | `Invalid type: github_username must be a string` |
| `invalid_json.txt` (파싱 불가)                     | `Failed to parse --user-info JSON file`          |
| `{ "display_name": "NoGitHub" }`               | `Missing required field: github_username`        |
| `{ "github_username": "alice", "extra": 123 }` | `Unexpected field: extra`                        |

---

## 📌 사용 예

```bash
mytool run --user-info user_info.json
```
