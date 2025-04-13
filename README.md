# reposcore-py
A CLI for scoring student participation in an open-source class repo, implemented in Python.

>
> **주의**
> - 절대로 `README.md`의 내용을 직접 수정하지 말 것! (템플릿에서 자동으로 생성하는 스크립트 추가됨)
> - 반드시 `template_README.md`의 내용을 수정한 후 `make readme` 실행하여 내용을 갱신해야 함.
>


## Install dependencies

```bash
make venv
make requirements
```

## Usage
아래는 `python -m reposcore -h` 또는 `python -m reposcore --help` 실행 결과를 붙여넣은 것이므로
명령줄 관련 코드가 변경되면 아래 내용도 그에 맞게 수정해야 함.

**⚠️ 반드시 저장소 최상위 디렉토리에서 실행해야 합니다. (python -m reposcore 명령은 상대 경로 기준으로 동작합니다.)**

```bash
python -m reposcore [OPTIONS]
```

```
usage: python -m reposcore [-h] [owner/repo ...] [--output dir_name] [--format {table,text,chart,all}] [--check-limit]

오픈 소스 수업용 레포지토리의 기여도를 분석하는 CLI 도구

positional arguments:
  owner/repo            분석할 GitHub 저장소들 (형식: '소유자/저장소'). 여러 저장소의 경우 공백 혹은 쉼표로
                        구분하여 입력

options:
  -h, --help            도움말 표시 후 종료
  --output dir_name     분석 결과를 저장할 출력 디렉토리 (기본값: 'results')
  --format {table,text,chart,all} [{table,text,chart,all} ...]
                        결과 출력 형식 선택 (복수 선택 가능, 예: --format table chart). 옵션:
                        'table', 'text', 'chart', 'all'
  --use-cache           participants 데이터를 캐시에서 불러올지 여부 (기본: API를 통해 새로 수집)
  --token TOKEN         API 요청 제한 해제를 위한 깃허브 개인 액세스 토큰
  --check-limit         현재 GitHub API 요청 가능 횟수와 전체 한도를 확인합니다.
  --user-info USER_INFO
                        사용자 정보 파일의 경로
```

### 옵션 설명

- **--check-limit**  
  이 옵션은 GitHub API의 **레이트 리밋 정보**를 확인하는 데 사용됩니다. `repository` 인자를 생략할 수 있으며, 이 경우 잔여 요청 횟수와 전체 한도를 출력합니다.  
  사용 예시:  
  ```bash
  python -m reposcore --check-limit
  ```
  위 명령을 실행하면, 현재 GitHub API의 잔여 요청 횟수와 전체 한도 정보가 출력되고 프로그램이 종료됩니다. 이 옵션은 선택적 옵션으로, 사용자가 필요할 때만 호출할 수 있습니다.

- **repository 인자**  
  `--check-limit` 옵션이 없을 경우, `repository` 인자는 필수로 제공되어야 하며, 올바른 형식("owner/repo")인지 검증하는 로직이 포함되어 있습니다.  
  사용 예시:  
  ```bash
  python -m reposcore owner/repo
  ```
  `owner/repo` 형식의 리포지토리 정보를 제공해야 합니다. 올바른 형식인지 검증이 수행됩니다.

## Test
👉 [테스트 가이드 보기](docs/test-guide.md)

## Score Formula
아래는 PR 개수와 이슈 개수의 비율에 따라 점수로 인정가능한 최대 개수를 구하고 각 배점에 따라 최종 점수를 산출하는 공식이다.

- $P_{fb}$ : 기능 또는 버그 관련 Merged PR 개수 (**3점**) ($P_{fb} = P_f + P_b$)  
- $P_d$ : 문서 관련 Merged PR 개수 (**2점**)  
- $I_{fb}$ : 기능 또는 버그 관련 Open 또는 해결된 이슈 개수 (**2점**) ($I_{fb} = I_f + I_b$)  
- $I_d$ : 문서 관련 Open 또는 해결된 이슈 개수 (**1점**)

$P_{\text{valid}} = P_{fb} + \min(P_d, 3 \times \max(P_{fb}, 1)) \quad$ 점수 인정 가능 PR 개수
$I_{\text{valid}} = \min(I_{fb} + I_d, 4 \times P_{\text{valid}}) \quad$ 점수 인정 가능 이슈 개수

PR의 점수를 최대로 하기 위해 기능/버그 PR을 먼저 계산한 후 문서 PR을 계산합니다.
(p_fb이 0일 경우에도 문서 PR 최대 3개까지 인정됩니다.)

$P_{fb}^* = \min(P_{fb}, P_{\text{valid}}) \quad$ 기능/버그 PR 최대 포함\
$P_d^* = P_{\text{valid}} - P_{fb}^* ~~\quad$ 남은 개수에서 문서 PR 포함

이슈의 점수를 최대로 하기 위해 기능/버그 이슈를 먼저 계산한 후 문서 이슈를 계산합니다.

$I_{fb}^* = \min(I_{fb}, I_{\text{valid}}) \quad$ 기능/버그 이슈 최대 포함\
$I_d^* = I_{\text{valid}} - I_{fb}^* ~~\quad$ 남은 개수에서 문서 이슈 포함

최종 점수 계산 공식:\  
$S = 3P_{fb}^* + 2P_d^* + 2I_{fb}^* + 1I_d^*$

## GitHub API 가이드
👉 [GitHub API 가이드](docs/github_api_guide.md) 문서를 참고 부탁드립니다.

## 토큰 생성 방법
👉 [토큰 생성 방법](docs/github-token-guide.md) 문서를 참고 부탁드립니다.

## 한국 시간대(Asia/Seoul) 설정 가이드
👉 [한국 시간대(Asia/Seoul) 설정 가이드](docs/korean-timezone-guide.md) 문서를 참고 부탁드립니다.

## 프로젝트 작성 시 주의사항
👉 [프로젝트 작성 시 주의사항](docs/project_guidelines.md) 문서를 참고 부탁드립니다.

## README.md 자동 생성 및 최신 상태 유지 가이드
👉 [README.md 자동 생성 및 최신 상태 유지 가이드](docs/readme_version_check_guide.md) 문서를 참고 부탁드립니다.

## 차트 생성시 한글 폰트 깨짐 이슈 해결 가이드
👉 [차트 생성시 한글 폰트 깨짐 이슈 해결 가이드](docs/chart-font-guide.md) 문서를 참고 부탁드립니다.