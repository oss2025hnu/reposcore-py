#!/usr/bin/env python3

import argparse
import sys
from .analyzer import RepoAnalyzer

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="GitHub Repo Analyzer")
    parser.add_argument("--owner", type=str, required=True, help="GitHub Repository Owner")
    parser.add_argument("--repo", type=str, required=True, help="GitHub Repository Name")
    parser.add_argument("--token", type=str, required=True, help="GitHub API Token")
    parser.add_argument("--output", type=str, default="results", help="Output directory for results")
    parser.add_argument("--format", choices=["table", "chart", "both"], default="both", help="Output format")
    return parser.parse_args()

def main():
    """Main execution function"""
    args = parse_arguments()

    analyzer = RepoAnalyzer(args.owner, args.repo, args.token)

    try:
        print("Collecting commit and issue data...")
        analyzer.fetch_data()

        scores = analyzer.calculate_scores()

        if args.format in ["table", "both"]:
            table = analyzer.generate_table(scores)
            table.to_csv(f"{args.output}_scores.csv", encoding="utf-8-sig")
            print("\nParticipation Scores Table:")
            print(table)

        if args.format in ["chart", "both"]:
            analyzer.generate_chart(scores, f"{args.output}_chart.png")
            print(f"Chart saved as {args.output}_chart.png")

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
