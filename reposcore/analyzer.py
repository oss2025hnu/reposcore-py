#!/usr/bin/env python3

import matplotlib.pyplot as plt
import pandas as pd
import requests
from typing import Dict

class RepoAnalyzer:
    """GitHub 저장소의 기여도를 분석하는 클래스"""
    
    def __init__(self, owner: str, repo: str, token: str):
        self.owner = owner  # 저장소 소유자
        self.repo = repo  # 저장소 이름
        self.token = token  # GitHub API 토큰
        self.participants: Dict = {}  # 기여자 데이터 저장
        self.score_weights = {
            'commits': 0.4,  # 커밋 기여도 가중치
            'issues_created': 0.3,  # 생성한 이슈 기여도 가중치
            'issue_comments': 0.3  # 이슈에 남긴 댓글 기여도 가중치
        }
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def fetch_all_pages(self, url: str):
        """GitHub API의 페이지네이션을 처리하여 모든 데이터를 가져오는 함수"""
        results = []
        page = 1
        while True:
            response = requests.get(f"{url}?per_page=100&page={page}", headers=self.headers)
            data = response.json()
            if not data or 'message' in data:  # 데이터 없음 또는 API 제한
                break
            results.extend(data)
            page += 1
        return results

    def fetch_data(self) -> None:
        """커밋, 이슈, 이슈 댓글 데이터를 가져와서 참여자 정보를 저장하는 함수"""
        base_url = f"https://api.github.com/repos/{self.owner}/{self.repo}"

        # 커밋 데이터 수집
        commits_url = f"{base_url}/commits"
        commits = self.fetch_all_pages(commits_url)
        for commit in commits:
            author = commit.get("author", {}).get("login")  # GitHub 아이디 사용
            if author:
                self.participants.setdefault(author, {'commits': 0, 'issues_created': 0, 'issue_comments': 0})
                self.participants[author]['commits'] += 1

        # 생성된 이슈 데이터 수집
        issues_url = f"{base_url}/issues"
        issues = self.fetch_all_pages(issues_url)
        for issue in issues:
            author = issue.get("user", {}).get("login")  # GitHub 아이디 사용
            if author:
                self.participants.setdefault(author, {'commits': 0, 'issues_created': 0, 'issue_comments': 0})
                self.participants[author]['issues_created'] += 1

        # 이슈 댓글 데이터 수집
        comments_url = f"{base_url}/issues/comments"
        comments = self.fetch_all_pages(comments_url)
        for comment in comments:
            author = comment.get("user", {}).get("login")  # GitHub 아이디 사용
            if author:
                self.participants.setdefault(author, {'commits': 0, 'issues_created': 0, 'issue_comments': 0})
                self.participants[author]['issue_comments'] += 1

    def calculate_scores(self) -> Dict:
        """각 기여자의 점수를 계산하는 함수"""
        scores = {}
        for participant, activities in self.participants.items():
            total_score = (
                activities.get('commits', 0) * self.score_weights['commits'] +
                activities.get('issues_created', 0) * self.score_weights['issues_created'] +
                activities.get('issue_comments', 0) * self.score_weights['issue_comments']
            )
            scores[participant] = round(total_score, 1)  # 소수점 한 자리 반올림
        return scores

    def generate_table(self, scores: Dict) -> pd.DataFrame:
        """점수 데이터를 테이블 형태로 변환하고 정렬하는 함수"""
        df = pd.DataFrame.from_dict(scores, orient='index', columns=['Score'])
        df.index.name = 'GitHub ID'
        df = df.sort_values(by='Score', ascending=False)  # 점수 순 정렬
        return df

    def generate_chart(self, scores: Dict, output_path: str) -> None:
        """점수를 가로 막대그래프로 시각화하는 함수"""
        sorted_scores = dict(sorted(scores.items(), key=lambda item: item[1], reverse=True))
        ids = list(sorted_scores.keys())
        values = list(sorted_scores.values())

        plt.figure(figsize=(10, max(5, len(ids) * 0.4)))  # 동적 크기 조정
        plt.barh(ids, values, height=0.5)
        plt.xlabel('Participation Score')
        plt.ylabel('GitHub ID')
        plt.title('Repository Participation Scores')
        plt.gca().invert_yaxis()  # 점수 높은 사람이 위로
        plt.tight_layout()
        plt.savefig(output_path)  # 그래프 저장
        plt.close()

    def run(self) -> None:
        """전체 분석을 수행하는 실행 함수"""
        self.fetch_data()  # 데이터 수집
        scores = self.calculate_scores()  # 점수 계산
        df = self.generate_table(scores)  # 테이블 생성

        # CSV 저장
        df.to_csv("result_score.csv")

        # 터미널에 출력
        print(df.to_string())

        # 차트 생성
        self.generate_chart(scores, "results_chart.png")
