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

```
[2025-05-12 14:36:21] [INFO] generated new fontManager
usage: python -m reposcore [-h] [-v] [owner/repo ...] [--output dir_name] [--format {table, text, chart, all}] [--check-limit] [--user-info path]

오픈 소스 수업용 레포지토리의 기여도를 분석하는 CLI 도구

positional arguments:
  owner/repo            분석할 GitHub 저장소들 (형식: '소유자/저장소'). 여러 저장소의 경우 공백 혹은 쉼표로
                        구분하여 입력

options:
  -h, --help            도움말 표시 후 종료
  -v, --verbose         자세한 로그를 출력합니다.
  --output dir_name     분석 결과를 저장할 출력 디렉토리 (기본값: 'results')
  --format {table, text, chart, all} [{table, text, chart, all} ...]
                        결과 출력 형식 선택 (복수 선택 가능, 예: --format table chart)
                        (기본값:'all')
  --grade               차트에 등급 표시
  --use-cache           participants 데이터를 캐시에서 불러올지 여부 (기본: API를 통해 새로 수집)
  --token TOKEN         API 요청 제한 해제를 위한 깃허브 개인 액세스 토큰
  --check-limit         현재 GitHub API 요청 가능 횟수와 전체 한도를 확인합니다.
  --user-info USER_INFO
                        사용자 정보 파일의 경로
  --user username       특정 사용자의 점수와 등수를 출력합니다 (GitHub 사용자명)
  --theme {default,dark}, -t {default,dark}
                        테마 선택 (default 또는 dark)
```
## Clean results directory

`make clean` 명령어는 분석 결과가 저장된 `results` 디렉토리를 삭제하는 기능을 제공합니다. 이 명령어를 사용하여 저장된 분석 결과를 초기화할 수 있습니다. 

```
make clean
```

### 단일 저장소 분석

아래 명령어로 단일 GitHub 저장소의 기여도를 분석할 수 있습니다:

```bash
python -m reposcore oss2025hnu/reposcore-py --format all
```

분석 결과는 `results/사용자명_저장소명/` 경로에 아래와 같이 저장됩니다:

- `score.csv`: 기여자별 점수 테이블 (CSV 형식)
- `score.txt`: 기여자별 점수 요약 텍스트
- `chart.png`: 기여도 시각화 차트

---

### 여러 저장소 통합 분석

여러 저장소를 동시에 분석하면, 각 저장소 결과와 함께 **통합 점수**도 함께 출력됩니다:

```bash
python -m reposcore oss2025hnu/reposcore-py oss2025hnu/reposcore-js oss2025hnu/reposcore-cs --format all
```

- 개별 저장소 분석 결과는 각각 `results/사용자명_저장소명/` 폴더에 저장됩니다.
- 통합 분석 결과는 `results/overall/` 폴더에 저장되며 다음 파일들이 포함됩니다:
  - `score.csv`: 전체 통합 기여자 점수 테이블
  - `score.txt`: 전체 기여자 점수 요약 텍스트
  - `chart.png`: 통합 기여도 시각화 차트

## Score Formula
아래는 PR 개수와 이슈 개수의 비율에 따라 점수로 인정가능한 최대 개수를 구하고 각 배점에 따라 최종 점수를 산출하는 공식이다.

- $P_{fb}$ : 기능 또는 버그 관련 Merged PR 개수 (**3점**) ($P_{fb} = P_f + P_b$)  
- $P_d$ : 문서 관련 Merged PR 개수 (**2점**)  
- $P_t$ : 오타 수정 Merged PR 개수 (**1점**)  
- $I_{fb}$ : 기능 또는 버그 관련 Open 또는 해결된 이슈 개수 (**2점**) ($I_{fb} = I_f + I_b$)  
- $I_d$ : 문서 관련 Open 또는 해결된 이슈 개수 (**1점**)

$P_{\text{valid}} = P_{fb} + \min(P_d + P_t, 3 \times \max(P_{fb}, 1)) \quad$ 점수 인정 가능 PR 개수  
$I_{\text{valid}} = \min(I_{fb} + I_d, 4 \times P_{\text{valid}}) \quad$ 점수 인정 가능 이슈 개수

PR의 점수를 최대로 하기 위해 기능/버그 PR을 먼저 계산한 후 문서 PR과 오타 PR을 계산합니다.  
($P_{fb}$이 0일 경우에도 문서 PR과 오타 PR 합산으로 최대 3개까지 인정됩니다.)

$P_{fb}^* = \min(P_{fb}, P_{\text{valid}}) \quad$ 기능/버그 PR 최대 포함  

$P_d^* = \min(P_d, P_{\text{valid}} - P_{fb}^*)$  문서 PR 포함

$P_t^* = P_{\text{valid}} - P_{fb}^* - P_d^*$  남은 개수에서 오타 PR 포함

이슈의 점수를 최대로 하기 위해 기능/버그 이슈를 먼저 계산한 후 문서 이슈를 계산합니다.

$I_{fb}^* = \min(I_{fb}, I_{\text{valid}}) \quad$ 기능/버그 이슈 최대 포함  
$I_d^* = I_{\text{valid}} - I_{fb}^* \quad$ 남은 개수에서 문서 이슈 포함

최종 점수 계산 공식:  
$S = 3P_{fb}^* + 2P_d^* + 1P_t^* + 2I_{fb}^* + 1I_d^*$

## 📚 가이드 문서 모음

### ⚙️ 프로젝트 시작
- [프로젝트 참여 주의사항 (필수)](docs/project_guidelines.md)
  - 프로젝트 규칙과 참여 방법.
- [fork 저장소를 원본 저장소와 sync 하는 방법](docs/fork_sync_guide.md)
  - 포크 저장소 동기화 가이드.

### 🛠️ 개발 환경 설정
- [한국 시간대(Asia/Seoul) 설정 가이드](docs/korean-timezone-guide.md)
  - Codespaces에서 한국 시간대 설정 방법.
- [파이썬 플러그인 설치 가이드](docs/python_plugin_guide.md)
  - Python 개발 환경 설정.
- [차트 생성시 한글 폰트 깨짐 이슈 해결 가이드](docs/chart-font-guide.md)
  - 차트 폰트 문제 해결 방법.

### 📊 도구 활용
- [README.md 자동 생성 및 최신 상태 유지 가이드](docs/readme_version_check_guide.md)
  - README 자동화 방법.
- [Pylint 사용 가이드](docs/pylint.md)
  - Pylint를 사용한 검사 기능 사용 방법.

### 🔗 GitHub 관련 기능
- [GitHub API 가이드](docs/github_api_guide.md)
  - GitHub API 사용 방법.
- [토큰 생성 방법](docs/github-token-guide.md)
  - GitHub 토큰 생성 및 설정.

### 🧪 테스트 및 개발
- [테스트 가이드](docs/test-guide.md)
  - 테스트 작성 및 실행 방법.
- [디버깅 및 로깅 가이드](docs/debug_guide.md)
  - 디버깅과 로깅 기술.
