# reposcore-py
A CLI for scoring student participation in an open-source class repo, implemented in Python.

## Install dependencies

```bash
pip install -r requirements.txt
```

## Usage
아래는 `python reposcore -h` 또는 `python reposcore --help` 실행 결과를 붙여넣은 것이므로
명령줄 관련 코드가 변경되면 아래 내용도 그에 맞게 수정해야 함.

```
usage: python -m reposcore --owner <OWNER> --repo <REPO> --token <GITHUB_TOKEN>

A CLI tool to score participation in an open-source course repository

options:
  -h, --help            show this help message and exit
  --repo REPO           Path to the git repository
  --output OUTPUT       Output directory for results
  --format {table,chart,both}
                        Output format
```
