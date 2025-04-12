#!/usr/bin/env python3

import argparse
import sys
import os
import requests
from .analyzer import RepoAnalyzer
from typing import Optional, List
from datetime import datetime
import json

def log(message: str):
    now = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{now} {message}")

GITHUB_BASE_URL = "https://github.com/"

class FriendlyArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        if '--format' in message:
            log(f"❌ 인자 오류: {message}")
            log("사용 가능한 --format 값: table, text, chart, all")
        else:
            super().error(message)
        sys.exit(2)

def validate_repo_format(repo: str) -> bool:
    parts = repo.split("/")
    return len(parts) == 2 and all(parts)

def check_github_repo_exists(repo: str) -> bool:
    url = f"https://api.github.com/repos/{repo}"
    response = requests.get(url)
    if response.status_code == 403:
        log("⚠️ GitHub API 요청 실패: 403 (비인증 상태로 요청 횟수 초과일 수 있습니다.)")
        log("ℹ️ 해결 방법: --token 옵션으로 GitHub Access Token을 전달해보세요.")
        return False
    return response.status_code == 200

def check_rate_limit(token: Optional[str] = None) -> None:
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"
    response = requests.get("https://api.github.com/rate_limit", headers=headers)
    if response.status_code == 200:
        data = response.json()
        core = data.get("resources", {}).get("core", {})
        remaining = core.get("remaining", "N/A")
        limit = core.get("limit", "N/A")
        log(f"GitHub API 요청 가능 횟수: {remaining} / {limit}")
    else:
        log(f"API 요청 제한 정보를 가져오는데 실패했습니다 (status code: {response.status_code}).")

def parse_arguments() -> argparse.Namespace:
    parser = FriendlyArgumentParser(
        prog="python -m reposcore",
        usage="python -m reposcore [-h] [owner/repo ...] [--output dir_name] [--format {table,text,chart,all}] [--check-limit] [--show-participants]",
        description="오픈 소스 수업용 레포지토리의 기여도를 분석하는 CLI 도구"
    )
    parser.add_argument(
        "repository",
        type=str,
        nargs="+",
        metavar="owner/repo",
        help="분석할 GitHub 저장소들 (형식: '소유자/저장소'). 여러 저장소의 경우 공백 혹은 쉼표로 구분하여 입력"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results",
        metavar="dir_name",
        help="분석 결과를 저장할 출력 디렉토리 (기본값: 'results')"
    )
    parser.add_argument(
        "--format",
        choices=["table", "text", "chart", "all"],
        nargs='+',
        default=["all"],
        metavar="{table,text,chart,all}",
        help="결과 출력 형식 선택 (복수 선택 가능, 예: --format table chart). 옵션: 'table', 'text', 'chart', 'all'"
    )
    parser.add_argument(
        "--use-cache",
        action="store_true",
        help="participants 데이터를 캐시에서 불러올지 여부 (기본: API를 통해 새로 수집)"
    )
    parser.add_argument(
        "--token",
        type=str,
        help="API 요청 제한 해제를 위한 깃허브 개인 액세스 토큰"
    )
    parser.add_argument(
        "--check-limit",
        action="store_true",
        help="현재 GitHub API 요청 가능 횟수와 전체 한도를 확인합니다."
    )
    parser.add_argument(
        "--show-participants",
        action="store_true",
        help="참여자별 활동 내역 딕셔너리를 출력합니다."
    )
    return parser.parse_args()

def merge_participants(overall: dict, new_data: dict) -> dict:
    for user, activities in new_data.items():
        if user not in overall:
            overall[user] = activities.copy()
        else:
            for key, value in activities.items():
                overall[user][key] = overall[user].get(key, 0) + value
    return overall

def main():
    args = parse_arguments()
    github_token = args.token or os.getenv('GITHUB_TOKEN')

    if args.check_limit:
        check_rate_limit(token=github_token)
        sys.exit(0)

    repositories: List[str] = []
    for repo in args.repository:
        if "," in repo:
            repositories.extend([r.strip() for r in repo.split(",") if r.strip()])
        else:
            repositories.append(repo)
    repositories = list(dict.fromkeys(repositories))

    for repo in repositories:
        if not validate_repo_format(repo):
            log(f"오류: 저장소 '{repo}'는 'owner/repo' 형식으로 입력해야 합니다. 예) 'oss2025hnu/reposcore-py'")
            sys.exit(1)
        if not check_github_repo_exists(repo):
            log(f"입력한 저장소 '{repo}'가 깃허브에 존재하지 않을 수 있음.")

    log(f"저장소 분석 시작: {', '.join(repositories)}")

    overall_participants = {}

    for repo in repositories:
        log(f"분석 시작: {repo}")
        analyzer = RepoAnalyzer(repo, token=github_token, show_participants=args.show_participants)
        cache_file_name = f"cache_{repo.replace('/', '_')}.json"
        cache_path = os.path.join(args.output, cache_file_name)

        os.makedirs(args.output, exist_ok=True)

        if args.use_cache and os.path.exists(cache_path):
            log(f"✅ 캐시 파일({cache_file_name})이 존재합니다. 캐시에서 데이터를 불러옵니다.")
            with open(cache_path, "r", encoding="utf-8") as f:
                analyzer.participants = json.load(f)
        else:
            log(f"🔄 캐시를 사용하지 않거나 캐시 파일({cache_file_name})이 없습니다. GitHub API로 데이터를 수집합니다.")
            analyzer.collect_PRs_and_issues()
            if not getattr(analyzer, "_data_collected", True):
                log("❌ GitHub API 요청에 실패했습니다. 결과 파일을 생성하지 않고 종료합니다.")
                sys.exit(1)
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(analyzer.participants, f, indent=2, ensure_ascii=False)

        overall_participants = merge_participants(overall_participants, analyzer.participants)
        log(f"분석 완료: {repo}")

    aggregator = RepoAnalyzer("multiple_repos", token=github_token)
    aggregator.participants = overall_participants

    try:
        scores = aggregator.calculate_scores()
        formats = set(args.format)

        os.makedirs(args.output, exist_ok=True)

        if "all" in formats:
            formats = {"table", "text", "chart"}

        if "table" in formats:
            table_path = os.path.join(args.output, "table.csv")
            aggregator.generate_table(scores, save_path=table_path)
            log(f"\nCSV 저장 완료: {table_path}")

        if "text" in formats:
            txt_path = os.path.join(args.output, "table.txt")
            aggregator.generate_text(scores, txt_path)
            log(f"\n텍스트 저장 완료: {txt_path}")

        if "chart" in formats:
            chart_path = os.path.join(args.output, "chart.png")
            aggregator.generate_chart(scores, save_path=chart_path)
            log(f"\n차트 이미지 저장 완료: {chart_path}")

    except Exception as e:
        log(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
