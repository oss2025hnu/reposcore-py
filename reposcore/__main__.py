#!/usr/bin/env python3

import argparse
import sys
from .analyzer import RepoAnalyzer

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='A CLI tool to score participation in an open-source course repository'
    )
    parser.add_argument(
        '--owner',
        type=str,
        required=True,
        help='GitHub repository owner'
    )
    parser.add_argument(
        '--repo',
        type=str,
        required=True,
        help='GitHub repository name'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='results',
        help='Output directory for results'
    )
    parser.add_argument(
        '--format',
        choices=['table', 'chart', 'both'],
        default='both',
        help='Output format (table, chart, or both)'
    )
    return parser.parse_args()

def main():
    """Main execution function"""
    args = parse_arguments()
    
    # Initialize analyzer
    analyzer = RepoAnalyzer(args.owner, args.repo)
    
    try:
        # Collect participation data
        print("Collecting commit data...")
        analyzer.collect_commits()
        
        print("Collecting issues data...")
        analyzer.collect_issues()
        
        # Calculate scores
        scores = analyzer.calculate_scores()
        
        # Generate outputs based on format
        if args.format in ['table', 'both']:
            table = analyzer.generate_table(scores)
            table.to_csv(f"{args.output}_scores.csv", encoding="utf-8-sig")
            print("\nParticipation Scores Table:")
            print(table)
            
        if args.format in ['chart', 'both']:
            analyzer.generate_chart(scores, "participation_chart.png")
            print(f"Chart saved as participation_chart.png")
            
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
