#!/usr/bin/env python3

from typing import Dict, Optional

import matplotlib.pyplot as plt
import pandas as pd
from prettytable import PrettyTable

from .utils.retry_request import retry_request

class RepoAnalyzer:
    """Class to analyze repository participation for scoring"""

    def __init__(self, repo_path: str, token: Optional[str] = None):
        self.repo_path = repo_path
        self.token = token
        self.participants: Dict = {}
        self.score_weights = {
            'PRs': 1,  # 이 부분은 merge된 PR의 PR 갯수, issues 갯수만 세기 위해 임시로 1로 변경
            'issues_created': 1,  # 향후 배점이 필요할 경우 PRs: 0.4, issues: 0.3으로 바꿔주세요.
            'issue_comments': 1
        }

    def collect_PRs_and_issues(self) -> None:
        """
        하나의 API 호출로 GitHub 이슈 목록을 가져오고,
        pull_request 필드가 있으면 PR로, 없으면 issue로 간주.
        PR의 경우, 실제로 병합된 경우만 점수에 반영.
        """
        page = 1
        per_page = 100

        while True:
            url = f"https://api.github.com/repos/{self.repo_path}/issues"

            response = retry_request(url,
                                    max_retries=3,
                                    params={
                                        'state': 'all',
                                        'per_page': per_page,
                                        'page': page
                                    })
            if response.status_code != 200:
                print(f"⚠️ GitHub API 요청 실패: {response.status_code}")
                return

            items = response.json()
            if not items:
                break

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

                labels = item.get('labels', [])
                label_names = [label.get('name', '') for label in labels if label.get('name')]

                if 'pull_request' in item:
                    merged_at = item.get('pull_request', {}).get('merged_at')
                    if merged_at:
                        for label in label_names:
                            key = f'p_{label}'
                            if key in self.participants[author]:
                                self.participants[author][key] += 1
                else:
                    for label in label_names:
                        key = f'i_{label}'
                        if key in self.participants[author]:
                            self.participants[author][key] += 1

            # 'link'가 없으면 False 처리
            link_header = response.headers.get('link', '')
            if 'rel="next"' in link_header:
                page += 1
            else:
                break

        print("\n참여자별 활동 내역 (participants 딕셔너리):")
        for user, info in self.participants.items():
            print(f"{user}: {info}")

    def calculate_scores(self) -> Dict:
        """Calculate participation scores for each contributor using the refactored formula"""
        scores = {}
        # global scores_temp
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

            scores[participant] = {
                "feat/bug PR": 3 * p_fb_at,
                "document PR": 2 * p_d_at,
                "feat/bug issue": 2 * i_fb_at,    
                "document issue": 1 * i_d_at,
                "total" : S
            }
            # 임시 코드
            
        # 내림차순 정렬
        return dict(sorted(scores.items(), key=lambda x: x[1]["total"], reverse=True))

    def generate_table(self, scores: Dict, save_path) -> None:
        """Generate a table of participation scores"""
        df = pd.DataFrame.from_dict(scores, orient="index")
        df.to_csv(save_path)

    def generate_text(self, scores: Dict, save_path) -> None:
        """Generate a table of participation scores"""
        table = PrettyTable()
        table.field_names = ["name", "feat/bug PR","document PR","feat/bug issue","document issue","total"]
        for name, score in scores.items():
            table.add_row(
                [name, 
                score["feat/bug PR"], 
                score["document PR"], 
                score['feat/bug issue'], 
                score['document issue'], 
                score['total']]
            )

        # table.txt 작성
        with open(save_path, 'w') as txt_file:
            txt_file.write(str(table))

    def generate_chart(self, scores: Dict, save_path: str = "results") -> None:
        """Generate a visualization of participation scores"""
        # scores 딕셔너리의 항목들을 점수를 기준으로 내림차순 정렬
        sorted_scores = sorted([(key, value.get('total',0)) for (key,value) in scores.items()], key=lambda item: item[1], reverse=True)
        
        # 정렬된 결과에서 참여자와 점수를 분리
        # 정렬된 결과가 없으면 빈 튜플을 사용
        participants, scores_sorted = zip(*sorted_scores) if sorted_scores else ([], [])
        
        # 참여자 수에 따라 차트의 세로 길이를 동적으로 결정
        # 최소 높이는 3인치로 설정하고, 참여자 수에 0.2인치를 곱해 높이를 정함
        num_participants = len(participants)
        height = max(3., num_participants * 0.2)
        
        # 가로 10인치, 세로 'height'인 그림 창을 생성
        plt.figure(figsize=(10, height))
        
        # 수평 막대그래프를 그리며, 막대의 두께를 0.5로 설정
        bars = plt.barh(participants, scores_sorted, height=0.5)
        
        # x축 레이블을 'Participation Score'로 설정
        plt.xlabel('Participation Score')
        
        # 차트 제목을 'Repository Participation Scores'로 설정
        plt.title('Repository Participation Scores')
        
        # y축의 순서를 반전시켜, 가장 높은 점수가 위쪽에 표시되도록 합니다.
        plt.gca().invert_yaxis()
        
        # 각 막대의 오른쪽에 해당 점수를 텍스트로 표시하는 파트
        for bar in bars:
            plt.text(
                bar.get_width() + 0.2,          # 막대의 길이에 0.2만큼 더해 오른쪽에 위치
                bar.get_y() + bar.get_height(), # 막대의 y위치에서 막대 높이만큼 내려가 텍스트 위치를 지정
                f'{bar.get_width():.1f}',       # 막대의 길이(점수)를 정수 형태의 문자열로 표시
                va='center',                    # 텍스트를 수직 중앙 정렬
                fontsize=9                      # 글씨 크기를 9로 설정
            )
        
        # 전체 레이아웃을 정리하고, 패딩을 2로 설정해 여백을 조정
        plt.tight_layout(pad=2)
        
        # 설정한 경로에 차트를 저장
        plt.savefig(save_path)
