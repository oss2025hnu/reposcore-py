#!/usr/bin/env python3

from typing import Dict, Optional
import matplotlib.pyplot as plt
import matplotlib.cm as cm

import pandas as pd
import requests
from prettytable import PrettyTable
from datetime import datetime
from zoneinfo import ZoneInfo
from .utils.retry_request import retry_request

import logging
import sys
import os
import matplotlib.font_manager as fm

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

ERROR_MESSAGES = {
    401: "❌ 인증 실패: 잘못된 GitHub 토큰입니다. 토큰 값을 확인해 주세요.",
    403: ("⚠️ 요청 실패 (403): GitHub API rate limit에 도달했습니다.\n"
            "🔑 토큰 없이 실행하면 1시간에 최대 60회 요청만 허용됩니다.\n"
            "💡 해결법: --api-key 옵션으로 GitHub 개인 액세스 토큰을 설정해 주세요."),
    404: "⚠️ 요청 실패 (404): 리포지토리가 존재하지 않습니다.",
    500: "⚠️ 요청 실패 (500): GitHub 내부 서버 오류 발생!",
    503: "⚠️ 요청 실패 (503): 서비스 불가",
    422: ("⚠️ 요청 실패 (422): 처리할 수 없는 컨텐츠\n"
            "⚠️ 유효성 검사에 실패 했거나, 엔드 포인트가 스팸 처리되었습니다.")
}

def check_github_repo_exists(repo: str) -> bool:
    return True  # 지금 여러 개의 저장소를 입력하는 경우 문제를 일으키기 때문에 무조건 True로 바꿔놓음


#    """주어진 GitHub 저장소가 존재하는지 확인하는 함수"""
#    url = f"https://api.github.com/repos/{repo}"
#    response = requests.get(url)
#    
#    if response.status_code == 403:
#        logging.warning("⚠️ GitHub API 요청 실패: 403 (비인증 상태로 요청 횟수 초과일 수 있습니다.)")
#        logging.info("ℹ️ 해결 방법: --token 옵션으로 GitHub Access Token을 전달해보세요.")
#    elif response.status_code == 404:
#        logging.warning(f"⚠️ 저장소 '{repo}'가 존재하지 않습니다.")
#    elif response.status_code != 200:
#        logging.warning(f"⚠️ 요청 실패: {response.status_code}")
#
#    return response.status_code == 200

class RepoAnalyzer:
    """Class to analyze repository participation for scoring"""

    def __init__(self, repo_path: str, token: Optional[str] = None):
        if not check_github_repo_exists(repo_path):
            logging.error(f"입력한 저장소 '{repo_path}'가 GitHub에 존재하지 않습니다.")
            sys.exit(1)

        self.repo_path = repo_path
        self.participants: Dict = {}
        self.score = {
            'feat_bug_pr': 3,
            'doc_pr': 2,
            'typo_pr': 1,
            'feat_bug_is': 2,
            'doc_is': 1
        }

        self._data_collected = True  # 기본값을 True로 설정

        self.SESSION = requests.Session()
        self.SESSION.headers.update({'Authorization': f'Bearer {token}'}) if token else None

    def collect_PRs_and_issues(self) -> None:
        """
        하나의 API 호출로 GitHub 이슈 목록을 가져오고,
        pull_request 필드가 있으면 PR로, 없으면 issue로 간주.
        PR의 경우, 실제로 병합된 경우만 점수에 반영.
        이슈는 open / reopened / completed 상태만 점수에 반영합니다.
        """
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
            status_code = response.status_code
            if status_code == 401:
                message = ERROR_MESSAGES[status_code]
                logging.error(message)
                self._data_collected = False
                return
            elif status_code == 403:
                message = ERROR_MESSAGES[status_code]
                logging.error(message)
                self._data_collected = False
                return
            elif status_code == 404:
                message = ERROR_MESSAGES[status_code]
                logging.error(message)
                self._data_collected = False
                return
            elif status_code == 500:
                message = ERROR_MESSAGES[status_code]
                logging.error(message)
                self._data_collected = False
                return
            elif status_code == 503:
                message = ERROR_MESSAGES[status_code]
                logging.error(message)
                self._data_collected = False
                return
            elif status_code == 422:
                message = ERROR_MESSAGES[status_code]
                logging.error(message)
                self._data_collected = False
                return
            elif status_code != 200:
                logging.warning(f"⚠️ GitHub API 요청 실패: {response.status_code}")
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
                        'p_typo' : 0,
                        'i_enhancement': 0,
                        'i_bug': 0,
                        'i_documentation': 0,
                    }

                labels = item.get('labels', [])
                label_names = [label.get('name', '') for label in labels if label.get('name')]

                state_reason = item.get('state_reason')

                # PR 처리 (병합된 PR만)
                if 'pull_request' in item:
                    merged_at = item.get('pull_request', {}).get('merged_at')
                    if merged_at:
                        for label in label_names:
                            key = f'p_{label}'
                            if key in self.participants[author]:
                                self.participants[author][key] += 1

                # 이슈 처리 (open / reopened / completed 만 포함, not planned 제외)
                else:
                    if state_reason in ('completed', 'reopened', None):
                        for label in label_names:
                            key = f'i_{label}'
                            if key in self.participants[author]:
                                self.participants[author][key] += 1

            # 다음 페이지 검사
            link_header = response.headers.get('link', '')
            if 'rel="next"' in link_header:
                page += 1
            else:
                break

        if not self.participants:
            logging.warning("⚠️ 수집된 데이터가 없습니다. (참여자 없음)")
            logging.info("📄 참여자는 없지만, 결과 파일은 생성됩니다.")
        else:
            excluded_ids = {"kyahnu", "kyagrd"}
            self.participants = {
                user: info for user, info in self.participants.items()
                if user not in excluded_ids
            }
            logging.info("\n참여자별 활동 내역 (participants 딕셔너리):")
            for user, info in self.participants.items():
                logging.info(f"{user}: {info}")

    def calculate_scores(self, user_info=None) -> Dict:
        """Calculate participation scores for each contributor using the refactored formula"""
        scores = {}
        total_score_sum = 0

        for participant, activities in self.participants.items():
            p_f = activities.get('p_enhancement', 0)
            p_b = activities.get('p_bug', 0)
            p_d = activities.get('p_documentation', 0)
            p_t = activities.get('p_typo', 0)
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
                    self.score['typo_pr'] * p_t +
                    self.score['feat_bug_is'] * i_fb_at +
                    self.score['doc_is'] * i_d_at
            )

            scores[participant] = {
                "feat/bug PR": self.score['feat_bug_pr'] * p_fb_at,
                "document PR": self.score['doc_pr'] * p_d_at,
                "typo PR": self.score['typo_pr'] * p_t,
                "feat/bug issue": self.score['feat_bug_is'] * i_fb_at,
                "document issue": self.score['doc_is'] * i_d_at,
                "total": S
            }

            total_score_sum += S

        for participant in scores:
            total = scores[participant]["total"]
            rate = (total / total_score_sum) * 100 if total_score_sum > 0 else 0
            scores[participant]["rate"] = round(rate, 1)

        if user_info:
            scores = {user_info[k]: scores.pop(k) for k in list(scores.keys()) if user_info.get(k) and scores.get(k)}

        return dict(sorted(scores.items(), key=lambda x: x[1]["total"], reverse=True))

    def calculate_averages(self, scores):
        """점수 딕셔너리에서 각 카테고리별 평균을 계산합니다."""
        if not scores:
            return {"feat/bug PR": 0, "document PR": 0, "feat/bug issue": 0, "document issue": 0, "total": 0, "rate": 0}

        num_participants = len(scores)
        totals = {
            "feat/bug PR": 0,
            "document PR": 0,
            "typo PR": 0,
            "feat/bug issue": 0,
            "document issue": 0,
            "total": 0
        }

        for participant, score_data in scores.items():
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
        logging.info(f"📊 CSV 결과 저장 완료: {save_path}")
        count_csv_path = os.path.join(dir_path or '.', "count.csv")
        with open(count_csv_path, 'w') as f:
            f.write("name,feat/bug PR,document PR,typo PR,feat/bug issue,document issue\n")
            for name, score in scores.items():
                pr_fb = int(score["feat/bug PR"] / self.score["feat_bug_pr"])
                pr_doc = int(score["document PR"] / self.score["doc_pr"])
                pr_typo = int(score["typo PR"] / self.score["typo_pr"])
                is_fb = int(score["feat/bug issue"] / self.score["feat_bug_is"])
                is_doc = int(score["document issue"] / self.score["doc_is"])
                f.write(f"{name},{pr_fb},{pr_doc},{pr_typo},{is_fb},{is_doc}\n")
        logging.info(f"📄 활동 개수 CSV 저장 완료: {count_csv_path}")

    def generate_text(self, scores: Dict, save_path) -> None:
        table = PrettyTable()
        table.field_names = ["name", "feat/bug PR", "document PR", "typo PR","feat/bug issue", "document issue", "total", "rate"]

        # 평균 계산
        averages = self.calculate_averages(scores)

        # 평균 행 추가
        table.add_row([
            "avg",
            round(averages["feat/bug PR"], 1),
            round(averages["document PR"], 1),
            round(averages["typo PR"], 1),
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
                score["typo PR"],
                score['feat/bug issue'],
                score['document issue'],
                score['total'],
                f'{score["rate"]:.1f}%'
            ])

        dir_path = os.path.dirname(save_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)

        # 생성 날짜 및 시간 추가 (텍스트 파일 상단)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        with open(save_path, 'w') as txt_file:
            txt_file.write(f"Generated on: {current_time}\n\n")
            txt_file.write(str(table))
        logging.info(f"📝 텍스트 결과 저장 완료: {save_path}")

    def generate_chart(self, scores: Dict, save_path: str, show_grade: bool = False) -> None:
        # 폰트 설정 변경 - 나눔고딕 폰트가 있는지 확인하고 있으면 사용
        fonts = [f.name for f in fm.fontManager.ttflist]
        if 'NanumGothic' in fonts:
            plt.rcParams['font.family'] = ['NanumGothic']
        else:
            plt.rcParams['font.family'] = ['DejaVu Sans']  # fallback
        
        sorted_scores = sorted(
            [(key, value.get('total', 0)) for (key, value) in scores.items()],
            key=lambda item: item[1],
            reverse=True
        )
        participants, scores_sorted = zip(*sorted_scores) if sorted_scores else ([], [])
        num_participants = len(participants)
        height = max(3., num_participants * 0.4)

        # 등수 계산 (동점 처리)
        ranks = []
        current_rank = 1
        prev_score = None
        for i, score in enumerate(scores_sorted):
            if score != prev_score:
                ranks.append(current_rank)
                prev_score = score
            else:
                ranks.append(ranks[-1])
            current_rank += 1

        plt.figure(figsize=(10, height))
        bars = plt.barh(participants, scores_sorted, height=0.5)

        # 동적 색상 매핑
        norm = plt.Normalize(min(scores_sorted or [0]), max(scores_sorted or [1]))
        colormap = plt.colormaps['viridis']
        for bar, score in zip(bars, scores_sorted):
            bar.set_color(colormap(norm(score)))

        plt.xlabel('Participation Score')
        timestamp = datetime.now(ZoneInfo("Asia/Seoul")).strftime("Generated at %Y-%m-%d %H:%M:%S")
        plt.title(f'Repository Participation Scores\n{timestamp}')
        plt.suptitle(f"Total Participants: {num_participants}", fontsize=10, x=0.98, ha='right')
        plt.gca().invert_yaxis()

        # 점수와 (선택적으로) 등급 표시
        for i, (bar, score) in enumerate(zip(bars, scores_sorted)):
            grade = ''
            if show_grade:
                if score >= 90:
                    grade = 'A'
                elif score >= 80:
                    grade = 'B'
                elif score >= 70:
                    grade = 'C'
                elif score >= 60:
                    grade = 'D'
                elif score >= 50:
                    grade = 'E'
                else:
                    grade = 'F'
                grade = f" ({grade})"

            plt.text(
                bar.get_width() + 0.5,
                bar.get_y() + bar.get_height() / 2,
                f'{int(score)}{grade} ({ranks[i]}place)',
                va='center',
                fontsize=9
            )

        # 디렉토리가 없으면 생성
        save_dir = os.path.dirname(save_path)
        if save_dir and not os.path.exists(save_dir):
            os.makedirs(save_dir, exist_ok=True)

        plt.tight_layout(pad=2)
        plt.savefig(save_path)
        logging.info(f"📈 차트 저장 완료: {save_path}")
        plt.close()
