#!/usr/bin/env python3

from typing import Dict, Optional
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import matplotlib.cm as cm

import pandas as pd
import requests
from prettytable import PrettyTable
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from .utils.retry_request import retry_request
from .utils.theme_manager import ThemeManager 
from .utils.github_utils import check_github_repo_exists

import logging
import sys
import os

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

def get_emoji(score):
    if score >= 90: return "🌟"     # 최상위 성과
    elif score >= 80: return "⭐"    # 탁월한 성과
    elif score >= 70: return "🎯"    # 목표 달성
    elif score >= 60: return "🎨"    # 양호한 성과
    elif score >= 50: return "🌱"    # 성장 중
    elif score >= 40: return "🍀"    # 발전 가능성
    elif score >= 30: return "🌿"    # 초기 단계
    elif score >= 20: return "🍂"    # 개선 필요
    elif score >= 10: return "🍁"    # 참여 시작
    else: return "🌑"                # 최소 참여

class RepoAnalyzer:
    """Class to analyze repository participation for scoring"""
    # 점수 가중치
    SCORE_WEIGHTS = {
        'feat_bug_pr': 3,
        'doc_pr': 2,
        'typo_pr': 1,
        'feat_bug_is': 2,
        'doc_is': 1
    }
    
    # 차트 설정
    CHART_CONFIG = {
        'height_per_participant': 0.4,  # 참여자당 차트 높이
        'min_height': 3.0,             # 최소 차트 높이
        'bar_height': 0.5,             # 막대 높이
        'figure_width': 12,            # 차트 너비 (텍스트 잘림 방지 위해 증가)
        'font_size': 9,                # 폰트 크기
        'text_padding': 0.1            # 텍스트 배경 상자 패딩
    }
    
    # 등급 기준
    GRADE_THRESHOLDS = {
        90: 'A',
        80: 'B',
        70: 'C',
        60: 'D',
        50: 'E',
        0: 'F'
    }

    # 사용자 제외 목록
    EXCLUDED_USERS = {"kyahnu", "kyagrd"}

    def __init__(self, repo_path: str, token: Optional[str] = None, theme: str = 'default'):
        # 테스트용 저장소나 통합 분석용 저장소 식별
        self._is_test_repo = repo_path == "dummy/repo"
        self._is_multiple_repos = repo_path == "multiple_repos"
        
        # 테스트용이나 통합 분석용이 아닌 경우에만 실제 저장소 존재 여부 확인
        if not self._is_test_repo and not self._is_multiple_repos:
            if not check_github_repo_exists(repo_path):
                logging.error(f"입력한 저장소 '{repo_path}'가 GitHub에 존재하지 않습니다.")
                sys.exit(1)
        elif self._is_test_repo:
            logging.info(f"ℹ️ [TEST MODE] '{repo_path}'는 테스트용 저장소로 간주합니다.")
        elif self._is_multiple_repos:
            logging.info(f"ℹ️ [통합 분석] 여러 저장소의 통합 분석을 수행합니다.")

        self.repo_path = repo_path
        self.participants: Dict = {}
        self.score = self.SCORE_WEIGHTS.copy()

        self.theme_manager = ThemeManager()  # 테마 매니저 초기화
        self.set_theme(theme)                # 테마 설정

        self._data_collected = True

        self.SESSION = requests.Session()
        if token:
            self.SESSION.headers.update({'Authorization': f'Bearer {token}'})

    def set_theme(self, theme_name: str) -> None:
        if theme_name in self.theme_manager.themes:
            self.theme_manager.current_theme = theme_name
        else:
            raise ValueError(f"지원하지 않는 테마입니다: {theme_name}")

    def _handle_api_error(self, status_code: int) -> bool:
        if status_code in ERROR_MESSAGES:
            logging.error(ERROR_MESSAGES[status_code])
            self._data_collected = False
            return True
        elif status_code != 200:
            logging.warning(f"⚠️ GitHub API 요청 실패: {status_code}")
            self._data_collected = False
            return True
        return False

    def collect_PRs_and_issues(self) -> None:
        """
        하나의 API 호출로 GitHub 이슈 목록을 가져오고,
        pull_request 필드가 있으면 PR로, 없으면 issue로 간주.
        PR의 경우, 실제로 병합된 경우만 점수에 반영.
        이슈는 open / reopened / completed 상태만 점수에 반영합니다.
        """
        # 테스트용 저장소나 통합 분석용인 경우 API 호출을 건너뜁니다
        if self._is_test_repo:
            logging.info(f"ℹ️ [TEST MODE] '{self.repo_path}'는 테스트용 저장소입니다. 실제 GitHub API 호출을 수행하지 않습니다.")
            return
        elif self._is_multiple_repos:
            logging.info(f"ℹ️ [통합 분석] 통합 분석을 위한 저장소입니다. API 호출을 건너뜁니다.")
            return
            
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
           
             # 🔽 에러 처리 부분 25줄 → 3줄로 리팩토링
            if self._handle_api_error(response.status_code):
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
            self.participants = {
                user: info for user, info in self.participants.items()
                if user not in self.EXCLUDED_USERS
            }
            logging.info("\n참여자별 활동 내역 (participants 딕셔너리):")
            for user, info in self.participants.items():
                logging.info(f"{user}: {info}")

    def _extract_pr_counts(self, activities: Dict) -> tuple[int, int, int, int, int]:
        """PR 관련 카운트 추출"""
        p_f = activities.get('p_enhancement', 0)
        p_b = activities.get('p_bug', 0)
        p_d = activities.get('p_documentation', 0)
        p_t = activities.get('p_typo', 0)
        p_fb = p_f + p_b
        return p_f, p_b, p_d, p_t, p_fb

    def _extract_issue_counts(self, activities: Dict) -> tuple[int, int, int, int]:
        """이슈 관련 카운트 추출"""
        i_f = activities.get('i_enhancement', 0)
        i_b = activities.get('i_bug', 0)
        i_d = activities.get('i_documentation', 0)
        i_fb = i_f + i_b
        return i_f, i_b, i_d, i_fb

    def _calculate_valid_counts(self, p_fb: int, p_d: int, i_fb: int, i_d: int) -> tuple[int, int]:
        """유효 카운트 계산"""
        p_valid = p_fb + min(p_d, 3 * max(p_fb, 1))
        i_valid = min(i_fb + i_d, 4 * p_valid)
        return p_valid, i_valid

    def _calculate_adjusted_counts(self, p_fb: int, p_valid: int, i_fb: int, i_valid: int) -> tuple[int, int, int, int]:
        """조정된 카운트 계산"""
        p_fb_at = min(p_fb, p_valid)
        p_d_at = p_valid - p_fb_at
        i_fb_at = min(i_fb, i_valid)
        i_d_at = i_valid - i_fb_at
        return p_fb_at, p_d_at, i_fb_at, i_d_at

    def _calculate_total_score(self, p_fb_at: int, p_d_at: int, p_t: int, i_fb_at: int, i_d_at: int) -> int:
        """총점 계산"""
        return (
            self.score['feat_bug_pr'] * p_fb_at +
            self.score['doc_pr'] * p_d_at +
            self.score['typo_pr'] * p_t +
            self.score['feat_bug_is'] * i_fb_at +
            self.score['doc_is'] * i_d_at
        )

    def _create_score_dict(self, p_fb_at: int, p_d_at: int, p_t: int, i_fb_at: int, i_d_at: int, total: int) -> Dict:
        """점수 딕셔너리 생성"""
        return {
            "feat/bug PR": self.score['feat_bug_pr'] * p_fb_at,
            "document PR": self.score['doc_pr'] * p_d_at,
            "typo PR": self.score['typo_pr'] * p_t,
            "feat/bug issue": self.score['feat_bug_is'] * i_fb_at,
            "document issue": self.score['doc_is'] * i_d_at,
            "total": total
        }

    def _finalize_scores(self, scores: Dict, total_score_sum: float, user_info: Optional[Dict] = None) -> Dict:
        """최종 점수 계산 및 정렬"""
        # 비율 계산
        for participant in scores:
            total = scores[participant]["total"]
            rate = (total / total_score_sum) * 100 if total_score_sum > 0 else 0
            scores[participant]["rate"] = round(rate, 1)

        # 사용자 정보 매핑 (제공된 경우)
        if user_info:
            scores = {user_info[k]: scores.pop(k) for k in list(scores.keys()) if user_info.get(k) and scores.get(k)}

        return dict(sorted(scores.items(), key=lambda x: x[1]["total"], reverse=True))

    def calculate_scores(self, user_info=None) -> Dict:
        """참여자별 점수 계산"""
        scores = {}
        total_score_sum = 0

        for participant, activities in self.participants.items():
            # PR 카운트 추출
            p_f, p_b, p_d, p_t, p_fb = self._extract_pr_counts(activities)
            
            # 이슈 카운트 추출
            i_f, i_b, i_d, i_fb = self._extract_issue_counts(activities)
            
            # 유효 카운트 계산
            p_valid, i_valid = self._calculate_valid_counts(p_fb, p_d, i_fb, i_d)
            
            # 조정된 카운트 계산
            p_fb_at, p_d_at, i_fb_at, i_d_at = self._calculate_adjusted_counts(
                p_fb, p_valid, i_fb, i_valid
            )
            
            # 총점 계산
            total = self._calculate_total_score(p_fb_at, p_d_at, p_t, i_fb_at, i_d_at)
            
            scores[participant] = self._create_score_dict(p_fb_at, p_d_at, p_t, i_fb_at, i_d_at, total)
            total_score_sum += total

        return self._finalize_scores(scores, total_score_sum, user_info)

    def calculate_averages(self, scores):
        """점수 딕셔너리에서 각 카테고리별 평균을 계산합니다."""
        if not scores:
            return {"feat/bug PR": 0, "document PR": 0, "typo PR": 0, "feat/bug issue": 0, "document issue": 0, "total": 0, "rate": 0}

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
        
    def generate_count_csv(self, scores: Dict, save_path: str = None) -> None:
        """
        점수 딕셔너리를 기반으로 각 활동 유형별 개수를 count.csv 파일로 저장합니다.
        
        Args:
            scores: 사용자별 점수 딕셔너리
            save_path: 저장할 파일 경로 (지정하지 않으면 현재 디렉토리에 count.csv로 저장)
        """
        dir_path = os.path.dirname(save_path) if save_path else '.'
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)
            
        count_csv_path = os.path.join(dir_path, "count.csv")
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
        return count_csv_path

    def generate_text(self, scores: Dict, save_path) -> None:
        # 기존 table.txt 생성
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
        current_time = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M")
        with open(save_path, 'w') as txt_file:
            txt_file.write(f"Generated on: {current_time}\n\n")
            txt_file.write(str(table))
        logging.info(f"📝 텍스트 결과 저장 완료: {save_path}")

        # score.txt 생성 (이모지 포함, grade 컬럼 제외)
        score_table = PrettyTable()
        score_table.field_names = ["name", "feat/bug PR", "document PR", "typo PR", "feat/bug issue", "document issue", "total", "rate"]

        # 평균 행 추가
        score_table.add_row([
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
            score_table.add_row([
                f"{get_emoji(score['total'])} {name}",
                score["feat/bug PR"],
                score["document PR"],
                score["typo PR"],
                score['feat/bug issue'],
                score['document issue'],
                score['total'],
                f'{score["rate"]:.1f}%'
            ])

        score_path = os.path.join(dir_path or '.', "score.txt")
        with open(score_path, 'w') as score_file:
            score_file.write(f"Generated on: {current_time}\n\n")
            score_file.write(str(score_table))
        logging.info(f"📝 점수 텍스트 결과 저장 완료: {score_path}")

    def _calculate_activity_ratios(self, participant_scores: Dict) -> tuple[float, float, float]:
        """참여자의 FEAT/BUG/DOC 활동 비율을 계산"""
        total = participant_scores["total"]
        if total == 0:
            return 0, 0, 0
            
        feat_bug_score = (
            participant_scores["feat/bug PR"] + 
            participant_scores["feat/bug issue"]
        )
        doc_score = (
            participant_scores["document PR"] + 
            participant_scores["document issue"]
        )
        typo_score = participant_scores["typo PR"]
        
        feat_bug_ratio = (feat_bug_score / total) * 100
        doc_ratio = (doc_score / total) * 100
        typo_ratio = (typo_score / total) * 100
        
        return feat_bug_ratio, doc_ratio, typo_ratio

    def generate_chart(self, scores: Dict, save_path: str, show_grade: bool = False) -> None:

      # Linux 환경에서 CJK 폰트 수동 설정
        # OSS 한글 폰트인 본고딕, 나눔고딕, 백묵 중 순서대로 하나를 선택
        for pref_name in ['Noto Sans CJK', 'NanumGothic', 'Baekmuk Dotum']:
            found_ttf = next((ttf for ttf in fm.fontManager.ttflist if pref_name in ttf.name), None)

            if found_ttf:
                plt.rcParams['font.family'] = found_ttf.name
                break
        theme = self.theme_manager.themes[self.theme_manager.current_theme]  # 테마 가져오기

        plt.rcParams['figure.facecolor'] = theme['chart']['style']['background']
        plt.rcParams['axes.facecolor'] = theme['chart']['style']['background']
        plt.rcParams['axes.edgecolor'] = theme['chart']['style']['text']
        plt.rcParams['axes.labelcolor'] = theme['chart']['style']['text']
        plt.rcParams['xtick.color'] = theme['chart']['style']['text']
        plt.rcParams['ytick.color'] = theme['chart']['style']['text']
        plt.rcParams['grid.color'] = theme['chart']['style']['grid']
        plt.rcParams['text.color'] = theme['chart']['style']['text']

        # 점수 정렬
        sorted_scores = sorted(
            [(key, value.get('total', 0)) for (key, value) in scores.items()],
            key=lambda item: item[1],
            reverse=True
        )
        participants, scores_sorted = zip(*sorted_scores) if sorted_scores else ([], [])
        num_participants = len(participants)
        
        # 클래스 상수 사용
        height = max(
            self.CHART_CONFIG['min_height'],
            num_participants * self.CHART_CONFIG['height_per_participant']
        )

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

        # 등수를 영어 서수로 변환하는 함수
        def get_ordinal_suffix(rank):
            if rank == 1:
                return "1st"
            elif rank == 2:
                return "2nd"
            elif rank == 3:
                return "3rd"
            else:
                return f"{rank}th"

        # 사용자 이름에 등수 추가
        ranked_participants = []
        for i, participant in enumerate(participants):
            rank_suffix = get_ordinal_suffix(ranks[i])
            ranked_participants.append(f"{rank_suffix} {participant}")

        plt.figure(figsize=(self.CHART_CONFIG['figure_width'], height))
        bars = plt.barh(ranked_participants, scores_sorted, height=self.CHART_CONFIG['bar_height'])

        # 색상 매핑 (기본 colormap 또는 등급별 색상)
        if show_grade:
            def get_grade_color(score):
                if score >= 90:
                    return theme['colors']['grade_colors']['A']
                elif score >= 80:
                    return theme['colors']['grade_colors']['B']
                elif score >= 70:
                    return theme['colors']['grade_colors']['C']
                elif score >= 60:
                    return theme['colors']['grade_colors']['D']
                elif score >= 50:
                    return theme['colors']['grade_colors']['E']
                else:
                    return theme['colors']['grade_colors']['F']

            for bar, score in zip(bars, scores_sorted):
                bar.set_color(get_grade_color(score))
        else:
            colormap = plt.colormaps[theme['chart']['style']['colormap']]
            norm = plt.Normalize(min(scores_sorted or [0]), max(scores_sorted or [1]))
            for bar, score in zip(bars, scores_sorted):
                bar.set_color(colormap(norm(score)))

        plt.xlabel('Participation Score')
        timestamp = datetime.now(ZoneInfo("Asia/Seoul")).strftime("Generated at %Y-%m-%d %H:%M:%S")
        plt.title(f'Repository Participation Scores\n{timestamp}')
        plt.suptitle(f"Total Participants: {num_participants}", fontsize=10, x=0.98, ha='right')
        plt.gca().invert_yaxis()

        # 동적 레이블 오프셋과 여백 계산 (텍스트 잘림 방지)
        max_score = max(scores_sorted or [100])  # 최대 점수 (최소 100으로 기본값)
        plt.xlim(0, max_score + 30)  # 가로축 범위: 최대 점수 + 20
        dynamic_offset = 0.05 * max_score  # 점수 비례 오프셋

        # 점수와 활동 비율 표시
        for i, (bar, score) in enumerate(zip(bars, scores_sorted)):
            participant = participants[i]
            feat_bug_ratio, doc_ratio, typo_ratio = self._calculate_activity_ratios(scores[participant])
            
            grade = ''
            if show_grade:
                # 상수 사용
                grade_assigned = 'F'
                for threshold, grade_letter in sorted(self.GRADE_THRESHOLDS.items(), reverse=True):
                    if score >= threshold:
                        grade_assigned = grade_letter
                        break
                grade = f" ({grade_assigned})"

            # 점수와 등급만 표시 (순위는 이름 앞에 표시되므로 제거)
            score_text = f'{int(score)}{grade}'
            
            # 활동 비율 표시 (앞글자만 사용)
            ratio_text = f'F/B: {feat_bug_ratio:.1f}% D: {doc_ratio:.1f}% T: {typo_ratio:.1f}%'
            
            # 텍스트 잘림 방지: 배경 상자 추가, 테두리 제거, 캔버스 밖 표시 허용
            plt.text(
                bar.get_width() + dynamic_offset,
                bar.get_y() + bar.get_height() / 2,
                f'{score_text}\n{ratio_text}',
                va='center',
                fontsize=self.CHART_CONFIG['font_size'],
                bbox=dict(facecolor='white', alpha=0.8, pad=self.CHART_CONFIG['text_padding'], edgecolor='none'),
                clip_on=False
            )

        # 디렉토리가 없으면 생성
        save_dir = os.path.dirname(save_path)
        if save_dir and not os.path.exists(save_dir):
            os.makedirs(save_dir, exist_ok=True)

        plt.subplots_adjust(left=0.2, right=0.98, top=0.93, bottom=0.05)
        plt.savefig(save_path)
        logging.info(f"📈 차트 저장 완료: {save_path}")
        plt.close()

    def is_cache_update_required(self, cache_path: str) -> bool:
        """캐시 데이터 업데이트 필요 여부를 확인합니다.

            지정된 캐시 파일의 존재 여부 및 최종 수정 시간을 확인하여
            캐시를 업데이트해야 하는지 여부를 결정합니다.

            Args:
                cache_path (str): 확인할 캐시 파일의 경로입니다.

            Returns:
                bool: 캐시 업데이트가 필요한 경우 True, 그렇지 않은 경우 False를 반환합니다.
                      캐시 파일이 존재하지 않거나, 마지막 수정 시간이 특정 조건(예: 만료 시간 초과)을
                      만족하는 경우 True를 반환할 수 있습니다.
        """
        url = f"https://api.github.com/repos/{self.repo_path}/issues"

        response = retry_request(self.SESSION,
                                 url,
                                 max_retries=3,
                                 params={
                                     'state': 'all',
                                     'per_page': 1,
                                 })
        if self._handle_api_error(response.status_code):
            return False

        response_json = response.json()[0]

        if 'created_at' not in response_json:
            logging.warning(f"⚠️ 요청 분석 실패")
            return False

        server_create_datetime = datetime.fromisoformat(response_json['created_at'])

        cache_stat = os.stat(cache_path)
        cache_create_datetime = datetime.fromtimestamp(cache_stat.st_ctime, tz=timezone.utc)

        return cache_create_datetime < server_create_datetime
