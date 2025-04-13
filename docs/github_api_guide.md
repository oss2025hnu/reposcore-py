## 1. **GitHub API란?**

GitHub에서 제공하는 공식 API로, GitHub의 저장소, 이슈, PR(Pull Request), 커밋 등 다양한 정보를 코드로 가져오거나 조작할 수 있게 해줍니다.

- 공식 문서: https://docs.github.com/ko/rest

---

## 2. **지금 프로젝트에서 사용하는 방식 요약**

현재 프로젝트는 GitHub API를 활용해서 아래 데이터를 자동으로 수집해 **참여도 점수**를 계산하고 있어요:

| 수집 대상 | 방식 |
| --- | --- |
| PR (Pull Requests) | `GET /repos/{owner}/{repo}/issues` 호출 → `pull_request` 필드가 존재하면 PR로 간주 |
| 병합 여부 | `pull_request.merged_at` 필드가 `null`이 아니면 병합된 것으로 간주 |
| Issue | `pull_request` 필드가 없으면 일반 이슈로 처리 |
| 라벨 분석 | `enhancement`, `bug`, `documentation` 등의 label을 기준으로 활동 분류 |

사용된 API 예시:

```python
url = f"https://api.github.com/repos/{repo_path}/issues"
params = {
    'state': 'all',
    'per_page': 100,
    'page': page
}
```

- 이 `/issues` API는 PR과 Issue를 **한 번에 가져오는** 특징이 있어요. PR도 사실 내부적으로는 Issue 객체라서 가능한 방식입니다.

---

## 3. **API 인증과 제한 (Rate Limit)**

- 인증 없이: 시간당 60회 요청
- 인증 시 (Personal Access Token): 시간당 5,000회까지 가능

    → `Authorization: token <your_token>` 헤더로 추가해야 해요.

예:

```python
session.headers.update({"Authorization": f"token {your_token}"
})
```

[토큰 생성 방법](docs/github-token-guide.md)

### ✅ `--check-limit` 옵션

- 이 옵션은 GitHub API의 **잔여 요청 가능 횟수**와 **전체 한도**를 출력합니다.
- `repository` 인자를 생략해도 사용 가능하며, 프로그램은 API 요청 없이 현재의 Rate Limit 정보만 조회하고 종료됩니다.

사용 예시:

```bash
python -m reposcore --check-limit
```

출력 예:

```
GitHub API Rate Limit: 4992 / 5000 remaining
```

### ✅ `repository` 인자와 Rate Limit 관련성

- GitHub 저장소(`owner/repo`)를 인자로 넘기면, 실제 데이터를 수집하기 위해 **다수의 API 호출**이 발생합니다.
- 이때 **토큰을 설정하지 않으면** API 호출이 차단될 수 있으며, 잘못된 형식의 인자(`abcd` 또는 `repo` 등)는 오류를 발생시킵니다.

예시:

```bash
python -m reposcore owner/repo  # 정상 실행
python -m reposcore abcd        # 에러 발생 (형식 오류)
```

이런 형식 유효성 검사는 내부적으로 `owner/repo` 문자열을 검사하는 로직으로 구현되어 있습니다.

---

## 4. **직접 실습 가능한 튜토리얼 링크**

1. [GitHub REST API에 대한 빠른 시작](https://docs.github.com/ko/rest/quickstart?apiVersion=2022-11-28)
2. [Github REST API - Python | Pygithub 시작하기](https://waytocse.tistory.com/111)
3. [파이썬 requests로 API 호출 연습](https://realpython.com/api-integration-in-python/)

---

## 추천 학습 흐름

1. **Postman으로 API 테스트 해보기**
    
    → GitHub API 문서에서 `Try it` 기능 활용
    
2. **Python에서 `requests`로 호출해보기**
3. **Label과 merged 상태 확인하면서 PR/Issue 분석 코드 연습**

