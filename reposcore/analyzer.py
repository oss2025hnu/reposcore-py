#!/usr/bin/env python3

from typing import Dict, Optional
import matplotlib.pyplot as plt
import pandas as pd
import requests
from prettytable import PrettyTable
from datetime import datetime
from .utils.retry_request import retry_request

import logging
import sys
import os

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def log(message: str):
    logging.info(message)

def check_github_repo_exists(repo: str) -> bool:
    return True  # 지금 여러 개의 저장소를 입력하는 경우 문제를 일으키기 때문에 무조건 True로 바꿔놓음

class RepoAnalyzer:
    def __init__(self, repo_path: str, token: Optional[str] = None, show_participants: bool = False):
        if not check_github_repo_exists(repo_path):
            log(f"입력한 저장소 '{repo_path}'가 GitHub에 존재하지 않습니다.")
            sys.exit(1)

        self.repo_path = repo_path
        self.participants: Dict = {}
        self.score = {
            'feat_bug_pr': 3,
            'doc_pr': 2,
            'feat_bug_is': 2,
            'doc_is': 1
        }
        self._data_collected = True
        self.show_participants = show_participants  # ✅ 사용자 추가 기능

        self.SESSION = requests.Session()
        if token:
            self.SESSION.headers.update({'Authorization': token})

    def collect_PRs_and_issues(self) -> None:
        page = 1
        per_page = 100

        while True:
            url = f"https://api.github.com/repos/{self.repo_path}/issues"

            response = retry_request(self.SESSION,
                                     url,
                                     max_retries=3,
                                     params={
                                         'state': 'all',
                                         'per_page': per_page,
                                         'page': page
                                     })
            if response.status_code in (403, 404, 500, 503, 422):
                log(f"⚠️ 요청 실패 ({response.status_code}): {response.reason}")
                self._data_collected = False
                return
            elif response.status_code != 200:
                log(f"⚠️ GitHub API 요청 실패: {response.status_code}")
                self._data_collected = False
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

                state_reason = item.get('state_reason')

                if 'pull_request' in item:
                    merged_at = item.get('pull_request', {}).get('merged_at')
                    if merged_at:
                        for label in label_names:
                            key = f'p_{label}'
                            if key in self.participants[author]:
                                self.participants[author][key] += 1
                else:
                    if state_reason in ('completed', 'reopened', None):
                        for label in label_names:
                            key = f'i_{label}'
                            if key in self.participants[author]:
                                self.participants[author][key] += 1

            link_header = response.headers.get('link', '')
            if 'rel="next"' in link_header:
                page += 1
            else:
                break

        if not self.participants:
            log("⚠️ 수집된 데이터가 없습니다. (참여자 없음)")
            log("📄 참여자는 없지만, 결과 파일은 생성됩니다.")
        elif self.show_participants:  # ✅ 사용자 추가 기능
            log("\n참여자별 활동 내역 (participants 딕셔너리):")
            for user, info in self.participants.items():
                log(f"{user}: {info}")

    def calculate_scores(self) -> Dict:
        scores = {}
        total_score_sum = 0

        for participant, activities in self.participants.items():
            p_f = activities.get('p_enhancement', 0)
            p_b = activities.get('p_bug', 0)
            p_d = activities.get('p_documentation', 0)
            p_fb = p_f + p_b

            i_f = activities.get('i_enhancement', 0)
            i_b = activities.get('i_bug', 0)
            i_d = activities.get('i_documentation', 0)
            i_fb = i_f + i_b

            p_valid = p_fb + min(p_d, 3 * max(p_fb, 1))
            i_valid = min(i_fb + i_d, 4 * p_valid)

            p_fb_at = min(p_fb, p_valid)
            p_d_at = p_valid - p_fb_at

            i_fb_at = min(i_fb, i_valid)
            i_d_at = i_valid - i_fb_at

            S = (
                self.score['feat_bug_pr'] * p_fb_at +
                self.score['doc_pr'] * p_d_at +
                self.score['feat_bug_is'] * i_fb_at +
                self.score['doc_is'] * i_d_at
            )

            scores[participant] = {
                "feat/bug PR": self.score['feat_bug_pr'] * p_fb_at,
                "document PR": self.score['doc_pr'] * p_d_at,
                "feat/bug issue": self.score['feat_bug_is'] * i_fb_at,
                "document issue": self.score['doc_is'] * i_d_at,
                "total": S
            }

            total_score_sum += S

        for participant in scores:
            total = scores[participant]["total"]
            rate = (total / total_score_sum) * 100 if total_score_sum > 0 else 0
            scores[participant]["rate"] = round(rate, 1)

        return dict(sorted(scores.items(), key=lambda x: x[1]["total"], reverse=True))

    def calculate_averages(self, scores):
        if not scores:
            return {"feat/bug PR": 0, "document PR": 0, "feat/bug issue": 0, "document issue": 0, "total": 0, "rate": 0}

        num_participants = len(scores)
        totals = {
            "feat/bug PR": 0,
            "document PR": 0,
            "feat/bug issue": 0,
            "document issue": 0,
            "total": 0
        }

        for score_data in scores.values():
            for category in totals.keys():
                totals[category] += score_data[category]

        averages = {category: total / num_participants for category, total in totals.items()}
        total_rates = sum(score_data["rate"] for score_data in scores.values())
        averages["rate"] = total_rates / num_participants if num_participants > 0 else 0

        return averages

    def generate_table(self, scores: Dict, save_path) -> None:
        df = pd.DataFrame.from_dict(scores, orient="index")
        df.reset_index(inplace=True)
        df.rename(columns={"index": "name"}, inplace=True)

        dir_path = os.path.dirname(save_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)

        df.to_csv(save_path, index=False)
        log(f"📊 CSV 결과 저장 완료: {save_path}")

    def generate_text(self, scores: Dict, save_path) -> None:
        table = PrettyTable()
        table.field_names = ["name", "feat/bug PR", "document PR", "feat/bug issue", "document issue", "total", "rate"]

        averages = self.calculate_averages(scores)
        table.add_row([
            "avg",
            round(averages["feat/bug PR"], 1),
            round(averages["document PR"], 1),
            round(averages["feat/bug issue"], 1),
            round(averages["document issue"], 1),
            round(averages["total"], 1),
            f'{averages["rate"]:.1f}%'
        ])

        for name, score in scores.items():
            table.add_row([
                name,
                score["feat/bug PR"],
                score["document PR"],
                score['feat/bug issue'],
                score['document issue'],
                score['total'],
                f'{score["rate"]:.1f}%'
            ])

        dir_path = os.path.dirname(save_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)

        with open(save_path, 'w') as txt_file:
            txt_file.write(str(table))
        log(f"📝 텍스트 결과 저장 완료: {save_path}")

    def generate_chart(self, scores: Dict, save_path: str = "results") -> None:
        sorted_scores = sorted(
            [(key, value.get('total', 0)) for (key, value) in scores.items()],
            key=lambda item: item[1],
            reverse=True
        )
        participants, scores_sorted = zip(*sorted_scores) if sorted_scores else ([], [])
        num_participants = len(participants)
        height = max(3., num_participants * 0.2)

        plt.figure(figsize=(10, height))
        bars = plt.barh(participants, scores_sorted, height=0.5)

        for bar in bars:
            score = bar.get_width()
            if score == 100:
                color = 'red'
            elif 90 <= score < 100:
                color = 'orchid'
            elif 80 <= score < 90:
                color = 'purple'
            elif 70 <= score < 80:
                color = 'darkblue'
            elif 60 <= score < 70:
                color = 'blue'
            elif 50 <= score < 60:
                color = 'green'
            elif 40 <= score < 50:
                color = 'lightgreen'
            elif 30 <= score < 40:
                color = 'lightgray'
            elif 20 <= score < 30:
                color = 'gray'
            elif 10 <= score < 20:
                color = 'dimgray'
            else:
                color = 'black'
            bar.set_color(color)

        plt.xlabel('Participation Score')
        plt.title('Repository Participation Scores')
        plt.suptitle(f"Total Participants: {num_participants}", fontsize=10, x=0.98, ha='right')
        plt.gca().invert_yaxis()

        for bar in bars:
            plt.text(
                bar.get_width() + 0.2,
                bar.get_y() + bar.get_height() / 2,
                f'{int(bar.get_width())}',
                va='center',
                fontsize=9
            )

        if not os.path.exists(save_path):
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

        plt.tight_layout(pad=2)
        plt.savefig(save_path)
        log(f"📈 차트 저장 완료: {save_path}")
