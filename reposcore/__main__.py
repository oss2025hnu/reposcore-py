#!/usr/bin/env python3

import argparse
import sys
from .analyzer import RepoAnalyzer

def parse_arguments():
    """명령줄 인수를 파싱하는 함수"""
    parser = argparse.ArgumentParser(description="GitHub Repo Analyzer")
    parser.add_argument("--owner", type=str, required=True, help="GitHub 저장소 소유자")
    parser.add_argument("--repo", type=str, required=True, help="GitHub 저장소 이름")
    parser.add_argument("--token", type=str, required=True, help="GitHub API 토큰")
    parser.add_argument("--output", type=str, default="results", help="결과 파일 이름")
    parser.add_argument("--format", choices=["table", "chart", "both"], default="both", help="출력 형식 선택")
    return parser.parse_args()

def main():
    """메인 실행 함수"""
    args = parse_arguments()

    analyzer = RepoAnalyzer(args.owner, args.repo, args.token)

    try:
        print("커밋 및 이슈 데이터를 수집 중...")
        analyzer.fetch_data()  # 데이터 수집

        scores = analyzer.calculate_scores()  # 점수 계산

        if args.format in ["table", "both"]:
            table = analyzer.generate_table(scores)
            table.to_csv(f"{args.output}_scores.csv", encoding="utf-8-sig")  # CSV 저장
            print("\n참여 점수 테이블:")
            print(table)

        if args.format in ["chart", "both"]:
            analyzer.generate_chart(scores, f"{args.output}_chart.png")  # 차트 생성
            print(f"차트가 {args.output}_chart.png 로 저장됨")

    except Exception as e:
        print(f"오류 발생: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
