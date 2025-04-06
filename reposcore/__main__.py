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
        usage="python -m reposcore [-h] --repo owner/repo [--output dir_name] [--format {table,chart,both}]",
        description="오픈 소스 수업용 레포지토리의 기여도를 분석하는 CLI 도구",
        add_help=False  # 기본 --help 옵션을 비활성화
    )
    
    parser.add_argument(
        "-h", "--help",
        action="help",
        help="도움말 표시 후 종료"
    )
    parser.add_argument(
        "--repo",
        type=str,
        required=True,
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
        choices=["table", "chart", "both"],
        default="both",
        metavar="{table,chart,both}",
        help="결과 출력 형식 선택 (테이블: 'table', 차트: 'chart', 둘 다: 'both')"
    )
    return parser.parse_args()


def main():
    """Main execution function"""
    args = parse_arguments()

    # Validate repo format
    if not validate_repo_format(args.repo):
        print("오류 : --repo 옵션은 'owner/repo' 형식으로 입력해야 함. 예) 'oss2025hnu/reposcore-py'")
        sys.exit(1)

    # (Optional) Check if the repository exists on GitHub
    if not check_github_repo_exists(args.repo):
        print(f"입력한 저장소 '{args.repo}' 가 깃허브에 존재하지 않을 수 있음.")
    
    print(f"저장소 분석 시작 : {args.repo}")

    # Initialize analyzer
    analyzer = RepoAnalyzer(args.repo)
    
    try:
        # Collect participation data

        print("Collecting PRs_and_issues data...")
        analyzer.collect_PRs_and_issues()    

        # Calculate scores
        scores = analyzer.calculate_scores()
        
        output_dir = args.output
        os.makedirs(output_dir, exist_ok=True)
        # Generate outputs based on format
        if args.format in ["table", "both"]:
            table_path = os.path.join(output_dir, "table.txt")
            analyzer.generate_table(scores, save_path=table_path)
            print(f"\nThe table has been saved as 'table.txt' in the '{output_dir}' directory.")
            
        if args.format in ["chart", "both"]:
            chart_path = os.path.join(output_dir, "chart.png")
            analyzer.generate_chart(scores, save_path=chart_path)
            print(f"\nThe chart has been saved as 'chart.png' in the '{output_dir}' directory.")
            
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
