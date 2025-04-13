#!/usr/bin/env python3

import argparse
import sys
import os
import requests
from .analyzer import RepoAnalyzer
from typing import Optional, List
from datetime import datetime
import json
import logging

# logging 모듈 기본 설정 (analyzer.py와 동일한 설정)
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 깃허브 저장소 기본 URL
GITHUB_BASE_URL = "https://github.com/"

# 친절한 오류 메시지를 출력할 ArgumentParser 클래스
class FriendlyArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        if '--format' in message:
            # --format 옵션에서만 오류 메시지를 사용자 정의
            logging.error(f"❌ 인자 오류: {message}")
            logging.error("사용 가능한 --format 값: table, text, chart, all")
        else:
            super().error(message)
        sys.exit(2)

def validate_repo_format(repo: str) -> bool:
    """Check if the repo input follows 'owner/repo' format"""
    parts = repo.split("/")
    return len(parts) == 2 and all(parts)

def check_github_repo_exists(repo: str) -> bool:
    """Check if the given GitHub repository exists"""
    url = f"https://api.github.com/repos/{repo}"
    response = requests.get(url)
    if response.status_code == 403:
        logging.warning("⚠️ GitHub API 요청 실패: 403 (비인증 상태로 요청 횟수 초과일 수 있습니다.)")
        logging.info("ℹ️ 해결 방법: --token 옵션으로 GitHub Access Token을 전달해보세요.")
        return False
    return response.status_code == 200

def check_rate_limit(token: Optional[str] = None) -> None:
    """현재 GitHub API 요청 가능 횟수와 전체 한도를 확인하고 출력하는 함수"""
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"
    response = requests.get("https://api.github.com/rate_limit", headers=headers)
    if response.status_code == 200:
        data = response.json()
        core = data.get("resources", {}).get("core", {})
        remaining = core.get("remaining", "N/A")
        limit = core.get("limit", "N/A")
        logging.info(f"GitHub API 요청 가능 횟수: {remaining} / {limit}")
    else:
        logging.error(f"API 요청 제한 정보를 가져오는데 실패했습니다 (status code: {response.status_code}).")

def parse_arguments() -> argparse.Namespace:
    """커맨드라인 인자를 파싱하는 함수"""
    parser = FriendlyArgumentParser(
        prog="python -m reposcore",
        usage="python -m reposcore [-h] [owner/repo ...] [--output dir_name] [--format {table,text,chart,all}] [--check-limit]",
        description="오픈 소스 수업용 레포지토리의 기여도를 분석하는 CLI 도구",
        add_help=False
    )
    parser.add_argument(
        "-h", "--help",
        action="help",
        help="도움말 표시 후 종료"
    )
    # 저장소 인자를 하나 이상 받도록 nargs="+"로 변경
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
        help = "결과 출력 형식 선택 (복수 선택 가능, 예: --format table chart). 옵션: 'table', 'text', 'chart', 'all'"
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
        "--user-info",
        type=str,
        help="사용자 정보 파일의 경로"
    )
    return parser.parse_args()

def merge_participants(overall: dict, new_data: dict) -> dict:
    """두 participants 딕셔너리를 병합합니다."""
    for user, activities in new_data.items():
        if user not in overall:
            overall[user] = activities.copy()
        else:
            # 각 항목별로 활동수를 누적합산합니다.
            for key, value in activities.items():
                overall[user][key] = overall[user].get(key, 0) + value
    return overall

def main():
    """Main execution function"""
    args = parse_arguments()
    github_token = args.token

    if not args.token:
        github_token = os.getenv('GITHUB_TOKEN')
    elif args.token == '-':
        github_token = sys.stdin.readline().strip()

    # --check-limit 옵션 처리: 이 옵션이 있으면 repository 인자 없이 실행됨.
    if args.check_limit:
        check_rate_limit(token=github_token)
        sys.exit(0)

    repositories: List[str] = args.repository
    # 쉼표로 여러 저장소가 입력된 경우 분리
    final_repositories = list(dict.fromkeys(
    [r.strip() for repo in repositories for r in repo.split(",") if r.strip()]
    ))

    # 각 저장소 유효성 검사
    for repo in final_repositories:
        if not validate_repo_format(repo):
            logging.error(f"오류: 저장소 '{repo}'는 'owner/repo' 형식으로 입력해야 합니다. 예) 'oss2025hnu/reposcore-py'")
            sys.exit(1)
        if not check_github_repo_exists(repo):
            logging.warning(f"입력한 저장소 '{repo}'가 깃허브에 존재하지 않을 수 있음.")

    logging.info(f"저장소 분석 시작: {', '.join(final_repositories)}")

    overall_participants = {}

    # 각 저장소별로 분석을 수행하고 participants 데이터를 병합합니다.
    for repo in final_repositories:
        logging.info(f"분석 시작: {repo}")
        analyzer = RepoAnalyzer(repo, token=github_token)
        # 저장소별 캐시 파일 생성 (예: cache_oss2025hnu_reposcore-py.json)
        cache_file_name = f"cache_{repo.replace('/', '_')}.json"
        cache_path = os.path.join(args.output, cache_file_name)
        
        os.makedirs(args.output, exist_ok=True)

        if args.use_cache and os.path.exists(cache_path):
            logging.info(f"✅ 캐시 파일({cache_file_name})이 존재합니다. 캐시에서 데이터를 불러옵니다.")
            with open(cache_path, "r", encoding="utf-8") as f:
                analyzer.participants = json.load(f)
        else:
            logging.info(f"🔄 캐시를 사용하지 않거나 캐시 파일({cache_file_name})이 없습니다. GitHub API로 데이터를 수집합니다.")
            analyzer.collect_PRs_and_issues()
            if not getattr(analyzer, "_data_collected", True):
                logging.error("❌ GitHub API 요청에 실패했습니다. 결과 파일을 생성하지 않고 종료합니다.")
                logging.error("ℹ️ 인증 없이 실행한 경우 요청 횟수 제한(403)일 수 있습니다. --token 옵션을 사용해보세요.")
                sys.exit(1)
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(analyzer.participants, f, indent=2, ensure_ascii=False)
        overall_participants = merge_participants(overall_participants, analyzer.participants)

        logging.info(f"분석 완료: {repo}")

    # 병합된 데이터를 가지고 통합 분석을 진행합니다.
    aggregator = RepoAnalyzer("multiple_repos", token=github_token)
    aggregator.participants = overall_participants

    try:
        user_info = json.load(open(args.user_info, "r", encoding="utf-8")) if args.user_info and os.path.exists(args.user_info) else None
        scores = aggregator.calculate_scores(user_info)
        formats = set(args.format)

        os.makedirs(args.output, exist_ok=True)

        if "all" in formats:
            formats =  {"table", "text", "chart"}

        if "table" in formats:
            table_path = os.path.join(args.output, "table.csv")
            aggregator.generate_table(scores, save_path=table_path)
            logging.info(f"\nCSV 저장 완료: {table_path}")

        if "text" in formats:
            txt_path = os.path.join(args.output, "table.txt")
            aggregator.generate_text(scores, txt_path)
            logging.info(f"\n텍스트 저장 완료: {txt_path}")

        if "chart" in formats:
            chart_path = os.path.join(args.output, "chart.png")
            aggregator.generate_chart(scores, save_path=chart_path)
            logging.info(f"\n차트 이미지 저장 완료: {chart_path}")

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
