#!/usr/bin/env python3

from typing import Dict

import matplotlib.pyplot as plt
import pandas as pd
import requests
from prettytable import PrettyTable

scores_temp = {}

class RepoAnalyzer:
    """Class to analyze repository participation for scoring"""

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.participants: Dict = {}
        self.score_weights = {
            'PRs': 1,  # 이 부분은 merge된 PR의 PR 갯수, issues 갯수만 세기 위해 임시로 1로 변경
            'issues_created': 1,  # 향후 배점이 필요할 경우 PRs: 0.4, issues: 0.3으로 바꿔주세요.
            'issue_comments': 1
        }

    def collect_PRs_and_issues(self) -> None:
        """
        collect_PRs와 collect_issues의 기능을 통합한 함수.
        GitHub 이슈 목록을 한 번에 가져온 뒤,
        pull_request 필드로 PR 여부를 구분하고,
        병합된 PR이면 PR 카운트로,
        일반 이슈라면 이슈 카운트로 기록한다.
        """
        page = 1
        per_page = 100

        pages_remaining = True

        while pages_remaining:
            url = f'https://api.github.com/repos/{self.repo_path}/pulls'
            response = requests.get(url,
                                    params={
                                        'state': 'all',
                                        'per_page': per_page,
                                        'page': page
                                    })

            if response.status_code != 200:
                print(f"⚠️ GitHub API 요청 실패: {response.status_code}")
                return

            items = response.json()

            for item in items:
                author = item.get('user', {}).get('login', 'Unknown')
                if author not in self.participants:
                    self.participants[author] = {
                        'p_enhancement': 0,
                        'p_bug': 0,
                        'p_documentation': 0,
                        'i_enhancement': 0,
                        'i_bug': 0,
                        'i_documentation': 0,
                    }

                if len(item['labels']) != 0:
                    label_names = list(map(lambda x: x.get('name', ''), item['labels']))
                    # print(label_names)
                    for label in label_names:
                        self.participants[author][f'p_{label}'] += 1

            pages_remaining = True if 'rel="next"' in response.headers['link'] else False
            page += 1

        page = 1
        pages_remaining = True

        while pages_remaining:
            # GitHub Issues API (pull request 역시 issue로 취급)
            url = f'https://api.github.com/repos/{self.repo_path}/issues'
            response = requests.get(url,
                                    params={
                                        'state': 'all',
                                        'per_page': per_page,
                                        'page': page
                                    })

            if response.status_code != 200:
                print(f'⚠️ GitHub API 요청 실패: {response.status_code}')
                return

            items = response.json()

            for item in items:
                author = item.get('user', {}).get('login', 'Unknown')
                if author not in self.participants:
                    self.participants[author] = {
                        'p_enhancement': 0,
                        'p_bug': 0,
                        'p_documentation': 0,
                        'i_enhancement': 0,
                        'i_bug': 0,
                        'i_documentation': 0,
                    }

                if len(item['labels']) != 0:
                    label_names = list(map(lambda x: x.get('name', ''), item['labels']))
                    for label in label_names:
                        self.participants[author][f'i_{label}'] += 1

            pages_remaining = True if 'rel="next"' in response.headers['link'] else False
            page += 1

    def calculate_scores(self) -> Dict:
        """Calculate participation scores for each contributor"""
        scores = {}
        global scores_temp
        for participant, activities in self.participants.items():
            p_f = activities.get('p_enhancement', 0)
            p_b = activities.get('p_bug', 0)
            p_d = activities.get('p_documentation', 0)

            p_fb = p_f + p_b

            i_f = activities.get('i_enhancement', 0)
            i_b = activities.get('i_bug', 0)
            i_d = activities.get('i_documentation', 0)

            i_fb = i_f + i_b

            p_valid = p_fb + min(p_d, 3 * p_fb)
            i_valid = min(i_fb + i_d, 4 * p_valid)

            p_fb_at = min(p_fb, p_valid)
            p_d_at = p_valid - p_fb

            i_fb_at = min(i_fb, i_valid)
            i_d_at = i_valid - i_fb_at

            S = 3 * p_fb_at + 2 * p_d_at + 2 * i_fb_at + 1 * i_d_at
            scores[participant] = S
            scores_temp[participant] = {
                "p_feat_bug": 3 * p_fb_at,
                "p_doc": 2 * p_d_at,
                "i_feat_bug": 2 * i_fb_at,    
                "i_doc": 1 * i_d_at,
                "total" : S
            }

        # 내림차순 정렬
        scores_temp = dict(sorted(scores_temp.items(), key=lambda x: x[1]["total"], reverse=True))

        # participants 딕셔너리 출력
        print("\n참여자별 활동 내역 (participants 딕셔너리):")
        for user, info in self.participants.items():
            print(f"{user}: {info}")

        return scores

    def generate_table(self, scores: Dict, save_path: str = "results") -> None:
        """Generate a table of participation scores"""
        table = PrettyTable()
        table.field_names = ["name", "feat/bug PR","document PR","feat/bug issue","document issue","total"]
        for name, score in scores_temp.items():
            table.add_row([name, score['p_feat_bug'], score['p_doc'], score['i_feat_bug'], score['i_doc'], score['total']])

        # table.txt 작성
        with open(save_path, 'w') as txt_file:
            txt_file.write(str(table))  

    def generate_chart(self, scores: Dict, save_path: str = "results") -> None:
        """Generate a visualization of participation scores"""
        plt.figure(figsize=(10, 6))
        plt.bar(scores.keys(), scores.values())
        plt.xticks(rotation=45)
        plt.ylabel('Participation Score')
        plt.title('Repository Participation Scores')
        plt.tight_layout()
        plt.ylim(bottom=0)
        plt.savefig(save_path)
