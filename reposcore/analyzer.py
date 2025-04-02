#!/usr/bin/env python3

import matplotlib.pyplot as plt
import pandas as pd
import requests
from typing import Dict

class RepoAnalyzer:
    """Class to analyze repository participation for scoring"""
    
    def __init__(self, owner: str, repo: str):
        self.owner = owner
        self.repo = repo
        self.participants: Dict = {}
        self.score_weights = {
            'commits': 0.4,
            'issues_created': 0.3,
            'issue_comments': 0.3
        }

    def collect_commits(self) -> None:
        """Collect commit data from GitHub API"""
        headers = {"Accept": "application/vnd.github.v3+json"}
        base_url = f"https://api.github.com/repos/{self.owner}/{self.repo}"

        commits_url = f"{base_url}/commits"
        commits_response = requests.get(commits_url, headers=headers)
        commits = commits_response.json()

        for commit in commits:
            author = commit.get("author", {}).get("login")  
            if author:
                self.participants.setdefault(author, {'commits': 0, 'issues_created': 0, 'issue_comments': 0})
                self.participants[author]['commits'] += 1

    def collect_issues(self) -> None:
        """Collect issues and comments data"""
        headers = {"Accept": "application/vnd.github.v3+json"}
        base_url = f"https://api.github.com/repos/{self.owner}/{self.repo}"

        issues_url = f"{base_url}/issues"
        issues_response = requests.get(issues_url, headers=headers)
        issues = issues_response.json()

        for issue in issues:
            author = issue.get("user", {}).get("login")  
            if author:
                self.participants.setdefault(author, {'commits': 0, 'issues_created': 0, 'issue_comments': 0})
                self.participants[author]['issues_created'] += 1

    def calculate_scores(self) -> Dict:
        """Calculate participation scores for each contributor"""
        scores = {}
        for participant, activities in self.participants.items():
            total_score = (
                activities.get('commits', 0) * self.score_weights['commits'] +
                activities.get('issues_created', 0) * self.score_weights['issues_created'] +
                activities.get('issue_comments', 0) * self.score_weights['issue_comments']
            )
            scores[participant] = round(total_score, 1)  
        return scores

    def generate_table(self, scores: Dict) -> pd.DataFrame:
        """Generate a table of participation scores"""
        df = pd.DataFrame.from_dict(scores, orient='index', columns=['Score'])
        df.index.name = 'GitHub ID'  
        return df

    def generate_chart(self, scores: Dict, output_path: str) -> None:
        """Generate a visualization of participation scores"""
        plt.figure(figsize=(10, 5))
        plt.bar(scores.keys(), scores.values(), width=0.4)
        plt.xticks(rotation=45)
        plt.ylabel('Participation Score')
        plt.title('Repository Participation Scores')
        plt.tight_layout()
        plt.savefig("participation_chart.png")
        plt.close()
