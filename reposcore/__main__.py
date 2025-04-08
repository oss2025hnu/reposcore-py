#!/usr/bin/env python3

import argparse
import sys
import os
import requests
from .analyzer import RepoAnalyzer

# 깃허브 저장소 기본 URL
GITHUB_BASE_URL = "https://github.com/"

def validate_repo_format(repo: str) -> bool:
    """Check if the repo input follows 'owner/repo' format"""
    parts = repo.split("/") # '/'를 기준으로 분리 (예: 'oss2025hnu/reposcore-py' → ['oss2025hnu', 'reposcore-py'])
    return len(parts) == 2 and all(parts) # 두 개의 부분(owner, repo)이 존재해야 하고, 비어 있으면 안 됨

def check_github_repo_exists(repo: str) -> bool:
    """Check if the given GitHub repository exists"""
    url = f"https://api.github.com/repos/{repo}" # 예: 'oss2025hnu/reposcore-py' → 'https://api.github.com/repos/oss2025hnu/reposcore-py'
    response = requests.get(url) # API 요청 보내기
    return response.status_code == 200 # 응답코드가 정상이면 저장소가 존재함

def parse_arguments() -> argparse.Namespace:
    """커맨드라인 인자를 파싱하는 함수"""
    parser = argparse.ArgumentParser(
        prog="python -m reposcore",
        usage="python -m reposcore [-h] owner/repo [--output dir_name] [--format {table,chart,both}]",
        description="오픈 소스 수업용 레포지토리의 기여도를 분석하는 CLI 도구",
        add_help=False  # 기본 --help 옵션을 비활성화
    )
    
    parser.add_argument(
        "-h", "--help",
        action="help",
        help="도움말 표시 후 종료"
    )
    parser.add_argument(
        "repository",
        type=str,
        metavar="owner/repo",
        help="분석할 GitHub 저장소 (형식: '소유자/저장소')"
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
        default="all",
        metavar="{table,text,chart,both}",
        help = "결과 출력 형식 선택 (테이블: 'table', 텍스트 : 'text', 차트: 'chart', 모두 : 'all')"
    )

    parser.add_argument(
        "--use-cache",
        action="store_true",
        help="participants 데이터를 캐시에서 불러올지 여부 (기본: API를 통해 새로 수집)"
    )

    parser.add_argument(
        '--token',
        type=str,
        help='API 요청 제한 해제를 위한 깃허브 개인 액세스 토큰'
    )

    return parser.parse_args()


def main():
    """Main execution function"""
    args = parse_arguments()

    # Validate repo format

    if not validate_repo_format(args.repository):
        print("오류 : 저장소는 'owner/repo' 형식으로 입력해야 함. 예) 'oss2025hnu/reposcore-py'")
        sys.exit(1)

    # (Optional) Check if the repository exists on GitHub

    if not check_github_repo_exists(args.repository):
        print(f"입력한 저장소 '{args.repository}' 가 깃허브에 존재하지 않을 수 있음.")
    
    print(f"저장소 분석 시작 : {args.repository}")

    # Initialize analyzer

    analyzer = RepoAnalyzer(args.repository, token=args.token)
    
        # 디렉토리 먼저 생성
    output_dir = args.output
    os.makedirs(output_dir, exist_ok=True)

    # 캐시 파일 경로 설정
    cache_path = os.path.join(output_dir, "cache.json")

    # 캐시 처리
    if args.use_cache and os.path.exists(cache_path):
        print("✅ 캐시 파일이 존재합니다. 캐시에서 데이터를 불러옵니다.")
        import json
        with open(cache_path, "r", encoding="utf-8") as f:
            analyzer.participants = json.load(f)
    else:
        print("🔄 캐시를 사용하지 않거나 캐시 파일이 없습니다. GitHub API로 데이터를 수집합니다.")
        analyzer.collect_PRs_and_issues()
        import json
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(analyzer.participants, f, indent=2, ensure_ascii=False)

    try:
        # Calculate scores
        scores = analyzer.calculate_scores()

        output_dir = args.output
        os.makedirs(output_dir, exist_ok=True)

        # Generate outputs based on format
        if args.format in ["table", "text", "all"]:
            table_path = os.path.join(output_dir, "table.csv")
            analyzer.generate_table(scores, save_path=table_path)
            print(f"\nThe table has been saved as 'table.csv' in the '{output_dir}' directory.")

        if args.format in ["text", "all"]:
            txt_path = os.path.join(output_dir, "table.txt")
            analyzer.generate_text(scores,txt_path)
            print(f"\nThe table has been saved as 'table.txt' in the '{output_dir}' directory.")

        if args.format in ["chart", "all"]:
            chart_path = os.path.join(output_dir, "chart.png")
            analyzer.generate_chart(scores, save_path=chart_path)
            print(f"\nThe chart has been saved as 'chart.png' in the '{output_dir}' directory.")

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
