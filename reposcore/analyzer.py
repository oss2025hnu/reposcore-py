#!/usr/bin/env python3  # 이 파일을 파이썬 인터프리터로 실행할 수 있게 설정

# 필요한 라이브러리 불러오기
import matplotlib.pyplot as plt  # 시각화를 위한 라이브러리
import pandas as pd              # 표 형식 데이터 처리를 위한 라이브러리
from typing import Dict          # 타입 힌팅을 위한 Dict 불러오기
import requests                  # GitHub API 요청을 위한 라이브러리
import time                      # API 요청 제한 대응을 위한 대기 함수

class RepoAnalyzer:
    """저장소 참여도를 분석하고 점수를 계산하는 클래스"""

    def __init__(self, repo_path: str):
        # 분석할 저장소 경로 저장 (예: 'oss2025hnu/reposcore-py')
        self.repo_path = repo_path

        # 참여자 데이터를 담을 딕셔너리. 예: {'alice': {'commits': 10, 'issues_created': 2, ...}}
        self.participants: Dict = {}

        # 활동별 점수 가중치 설정
        self.score_weights = {
            'commits': 0.4,          # 커밋 점수 비율
            'issues_created': 0.3,   # 이슈 생성 점수 비율
            'issue_comments': 0.3    # 이슈 댓글 점수 비율
        }

    def collect_commits(self) -> None:
        """
        GitHub API를 사용하여 저장소의 커밋 기여자 데이터를 수집.
        예: {'alice': {'commits': 15, 'issues_created': 0, 'issue_comments': 0}}
        """
        print("GitHub API에서 커밋 데이터 수집 중...")

        owner_repo = self.repo_path
        api_url = f"https://api.github.com/repos/{owner_repo}/contributors"

        try:
            response = requests.get(api_url)
            response.raise_for_status()
            data = response.json()

            for user in data:
                username = user.get("login")
                commit_count = user.get("contributions", 0)
                self.participants[username] = {
                    'commits': commit_count,
                    'issues_created': 0,
                    'issue_comments': 0
                }

        except requests.RequestException as e:
            print("GitHub API 요청 중 오류 발생:", e)

    def collect_issues(self) -> None:
        """
        GitHub API를 사용해 각 참여자의 이슈 생성 수와 댓글 수를 수집.
        self.participants에 추가하거나 갱신함.
        """
        print("GitHub API에서 이슈 및 댓글 데이터 수집 중...")

        owner_repo = self.repo_path
        issues_url = f"https://api.github.com/repos/{owner_repo}/issues?state=all&per_page=100"
        comments_url = f"https://api.github.com/repos/{owner_repo}/issues/comments?per_page=100"

        # 이슈 생성자 수집
        try:
            page = 1
            while True:
                response = requests.get(f"{issues_url}&page={page}")
                response.raise_for_status()
                issues = response.json()

                if not issues:
                    break

                for issue in issues:
                    if 'pull_request' in issue:
                        continue  # PR은 제외하고 실제 이슈만 포함

                    user = issue.get("user", {}).get("login")
                    if not user:
                        continue

                    if user not in self.participants:
                        self.participants[user] = {
                            'commits': 0,
                            'issues_created': 1,
                            'issue_comments': 0
                        }
                    else:
                        self.participants[user]['issues_created'] += 1

                page += 1
                time.sleep(0.1)

        except requests.RequestException as e:
            print("이슈 수집 중 오류 발생:", e)

        # 이슈 댓글 작성자 수집
        try:
            page = 1
            while True:
                response = requests.get(f"{comments_url}&page={page}")
                response.raise_for_status()
                comments = response.json()

                if not comments:
                    break

                for comment in comments:
                    user = comment.get("user", {}).get("login")
                    if not user:
                        continue

                    if user not in self.participants:
                        self.participants[user] = {
                            'commits': 0,
                            'issues_created': 0,
                            'issue_comments': 1
                        }
                    else:
                        self.participants[user]['issue_comments'] += 1

                page += 1
                time.sleep(0.1)

        except requests.RequestException as e:
            print("댓글 수집 중 오류 발생:", e)

    def calculate_scores(self) -> Dict:
        """참여자별 활동 데이터를 바탕으로 점수를 계산"""
        scores = {}
        for participant, activities in self.participants.items():
            total_score = (
                activities.get('commits', 0) * self.score_weights['commits'] +
                activities.get('issues_created', 0) * self.score_weights['issues_created'] +
                activities.get('issue_comments', 0) * self.score_weights['issue_comments']
            )
            scores[participant] = total_score
        return scores

    def generate_table(self, scores: Dict) -> pd.DataFrame:
        """점수 데이터를 표 형식으로 변환"""
        df = pd.DataFrame.from_dict(scores, orient='index', columns=['Score'])
        return df

    def generate_chart(self, scores: Dict) -> None:
        """점수 데이터를 막대그래프로 시각화"""
        plt.figure(figsize=(10, 6))
        plt.bar(scores.keys(), scores.values())
        plt.xticks(rotation=45)
        plt.ylabel('Participation Score')
        plt.title('Repository Participation Scores')
        plt.tight_layout()
        plt.savefig('participation_chart.png')
