#!/usr/bin/env python3
import json
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import pandas as pd
from prettytable import PrettyTable
import numpy as np
from datetime import datetime, timezone, date
from zoneinfo import ZoneInfo
from prettytable import PrettyTable


from .common_utils import log
from .theme_manager import ThemeManager

import sys
import os

class OutputHandler:
    """Class to handle output generation for repository analysis results"""
    
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

    def __init__(self, theme: str = 'default'):
        self.theme_manager = ThemeManager()  # 테마 매니저 초기화
        self.set_theme(theme)                # 테마 설정

    def set_theme(self, theme_name: str) -> None:
        if theme_name in self.theme_manager.themes:
            self.theme_manager.current_theme = theme_name
        else:
            raise ValueError(f"지원하지 않는 테마입니다: {theme_name}")
            

    def _calculate_grade(self, total_score: float) -> str:
        """점수에 따른 등급 계산"""
        for threshold, grade in self.GRADE_THRESHOLDS.items():
            if total_score >= threshold:
                return grade
        return 'F'
    
    @staticmethod
    def get_kst_timestamp() -> str:
        """현재 KST(한국 시간) 기준 타임스탬프 반환"""
        kst = ZoneInfo("Asia/Seoul")
        return datetime.now(tz=kst).strftime("%Y-%m-%d %H:%M:%S (KST)")

    def generate_table(self, scores: dict[str, dict[str, float]], save_path) -> None:
        """결과를 테이블 형태로 출력"""
        timestamp = self.get_kst_timestamp()
        table = PrettyTable()
        table.field_names = ["참여자", "총점", "등급", "PR(기능/버그)", "PR(문서)", "PR(오타)", "이슈(기능/버그)", "이슈(문서)"]
        
        for name, score in scores.items():
            # 등급 계산
            grade = self._calculate_grade(score['total'])
            row = [
                name,
                f"{score['total']:.1f}",
                grade,
                f"{score['feat/bug PR']:.1f}",
                f"{score['document PR']:.1f}",
                f"{score['typo PR']:.1f}",
                f"{score['feat/bug issue']:.1f}",
                f"{score['document issue']:.1f}"
            ]
            table.add_row(row)
        
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(f"=== 참여자별 점수 (분석 기준 시각: {timestamp}) ===\n\n")
            f.write(str(table))

    def generate_count_csv(self, scores: dict, save_path: str = None) -> None:
        """결과를 CSV 파일로 출력"""
        timestamp = self.get_kst_timestamp()
        df = pd.DataFrame.from_dict(scores, orient='index')
        # grade 컬럼 제거
        df = df.drop('grade', axis=1, errors='ignore')
        df = df.round(1)
        df.index.name = 'name'  # 인덱스 이름을 'name'으로 설정

        df.to_csv(save_path, encoding='utf-8')


    def generate_text(self, scores: dict[str, dict[str, float]], save_path: str) -> None:
        """PrettyTable을 사용해 참여자 점수를 표 형식으로 출력"""
        timestamp = self.get_kst_timestamp()

        table = PrettyTable()
        table.field_names = [
            "Name", "Total Score", "Grade",
            "PR (Feature/Bug)", "PR (Docs)", "PR (Typos)",
            "Issue (Feature/Bug)", "Issue (Docs)"
        ]

        for name, score in scores.items():
            grade = self._calculate_grade(score["total"])
            table.add_row([
                name,
                f"{score['total']:.1f}",
                grade,
                f"{score['feat/bug PR']:.1f}",
                f"{score['document PR']:.1f}",
                f"{score['typo PR']:.1f}",
                f"{score['feat/bug issue']:.1f}",
                f"{score['document issue']:.1f}",
            ])

        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(f"=== 참여자별 점수 (분석 기준 시각: {timestamp}) ===\n\n")
            f.write(table.get_string())


    def _calculate_activity_ratios(self, participant_scores: dict) -> tuple[float, float, float]:
        """활동 비율 계산"""
        total_pr = sum(score['feat/bug PR'] + score['document PR'] + score['typo PR'] for score in participant_scores.values())
        total_issue = sum(score['feat/bug issue'] + score['document issue'] for score in participant_scores.values())
        total = total_pr + total_issue

        if total == 0:
            return 0.0, 0.0, 0.0

        pr_ratio = total_pr / total
        issue_ratio = total_issue / total
        code_ratio = (sum(score['feat/bug PR'] for score in participant_scores.values()) + 
                    sum(score['feat/bug issue'] for score in participant_scores.values())) / total

        return pr_ratio, issue_ratio, code_ratio

    def generate_chart(self, scores: dict[str, dict[str, float]], save_path: str, show_grade: bool = False) -> None:
        """결과를 차트로 출력: PR과 이슈를 단일 스택형 막대 그래프로 통합"""
        # Linux 환경에서 CJK 폰트 수동 설정
        # OSS 한글 폰트인 본고딕, 나눔고딕, 백묵 중 순서대로 하나를 선택
        font_paths = [
            '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',  # 나눔고딕
            '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',  # 본고딕
            '/usr/share/fonts/truetype/baekmuk/baekmuk.ttf'  # 백묵
        ]

        timestamp = self.get_kst_timestamp()

        # 등수를 영어 서수로 변환하는 함수
        def get_ordinal_suffix(rank: int) -> str:
            if rank == 1:
                return "1st"
            elif rank == 2:
                return "2nd"
            elif rank == 3:
                return "3rd"
            else:
                return f"{rank}th"

        # 정렬된 참여자 리스트 만들기
        sorted_scores = sorted(scores.items(), key=lambda x: x[1]["total"], reverse=True)
        participants = [user for user, _ in sorted_scores]
        total_scores = [score_data["total"] for _, score_data in sorted_scores]
        pr_scores = [score_data["feat/bug PR"] + score_data["document PR"] + score_data["typo PR"] for _, score_data in sorted_scores]
        issue_scores = [score_data["feat/bug issue"] + score_data["document issue"] for _, score_data in sorted_scores]

        # ✅ 서수 등수 붙이기
        ranked_participants = [f"{user} ({get_ordinal_suffix(i+1)})" for i, user in enumerate(participants)]

        for font_path in font_paths:
            if os.path.exists(font_path):
                fm.fontManager.addfont(font_path)
                plt.rcParams['font.family'] = 'sans-serif'
                plt.rcParams['font.sans-serif'] = ['NanumGothic', 'Noto Sans CJK JP', 'Baekmuk']
                break

        # 참여자 수에 따라 차트 높이 조정
        num_participants = len(scores)
        chart_height = max(self.CHART_CONFIG['min_height'], 
                         num_participants * self.CHART_CONFIG['height_per_participant'])

        # 차트 생성
        fig, ax = plt.subplots(figsize=(self.CHART_CONFIG['figure_width'], chart_height))
        
        # 데이터 준비
        participants = list(scores.keys())
        pr_scores = [scores[p]['feat/bug PR'] + scores[p]['document PR'] + scores[p]['typo PR'] for p in participants]
        issue_scores = [scores[p]['feat/bug issue'] + scores[p]['document issue'] for p in participants]
        total_scores = [scores[p]['total'] for p in participants]

        # 막대 위치 설정
        y_pos = range(len(participants))
        bar_height = self.CHART_CONFIG['bar_height']

        # 테마에서 색상 가져오기 (기본값 유지)
        theme_colors = self.theme_manager.themes[self.theme_manager.current_theme]
        pr_color = theme_colors.get("pr_color", "skyblue")  # 기본: skyblue
        issue_color = theme_colors.get("issue_color", "lightgreen")  # 기본: lightgreen

        # 단일 스택형 막대 그리기
        ax.barh(y_pos, pr_scores, height=bar_height, label='PR', color=pr_color, edgecolor='none')
        ax.barh(y_pos, issue_scores, left=pr_scores, height=bar_height, label='Issue', color=issue_color, edgecolor='none')

        # 점수 표시
        for i, total in enumerate(total_scores):
            if show_grade:
                grade = self._calculate_grade(total)
                ax.text(total + 1, i, f'{total:.1f} ({grade})', 
                    va='center', fontsize=self.CHART_CONFIG['font_size'])
            else:
                ax.text(total + 1, i, f'{total:.1f}', 
                    va='center', fontsize=self.CHART_CONFIG['font_size'])

        # 축 설정
        ax.set_yticks(range(len(ranked_participants)))
        ax.set_yticklabels(ranked_participants)
        ax.set_xlabel('Score')
        ax.set_title(
            f'Repository Contribution Scores\n(분석 기준 시각: {timestamp})',
            fontsize=14,
            loc='center',  # 또는 'left', 'right'
            color='black'
        )
        ax.invert_yaxis()

        # 범례 추가 (테두리 없음)
        ax.legend(loc='upper right', frameon=False)

        # 가로축 여백 조정 (텍스트 잘림 방지)
        max_score = max(total_scores) if total_scores else 100
        ax.set_xlim(0, max_score + max_score * self.CHART_CONFIG['text_padding'])

        # 여백 조정
        plt.tight_layout()

        # 저장
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close() 

    def generate_repository_stacked_chart(self, scores: dict, save_path: str):
        if not scores:
            return

        # ✅ 모든 사용자 기준으로 저장소 키 수집
        repo_keys = set()
        for user_data in scores.values():
            repo_keys.update([k for k in user_data.keys() if k not in ["total", "grade"]])
        repo_keys = sorted(repo_keys)  # 보기 좋게 정렬해도 OK

        # 총점 기준 내림차순 정렬
        sorted_users = sorted(scores.items(), key=lambda x: x[1].get("total", 0), reverse=True)
        usernames = [user for user, _ in sorted_users]

        # 서수 붙이기 (1st, 2nd, 3rd ...)
        def get_ordinal_suffix(rank: int) -> str:
            if rank == 1:
                return "1st"
            elif rank == 2:
                return "2nd"
            elif rank == 3:
                return "3rd"
            else:
                return f"{rank}th"

        ranked_usernames = [f"{user} ({get_ordinal_suffix(i+1)})" for i, user in enumerate(usernames)]

        usernames = usernames[::-1]
        ranked_usernames = ranked_usernames[::-1]

        # 저장소별 점수 추출
        scores_by_repo = {
            repo: [scores[user].get(repo, 0) for user in usernames]
            for repo in repo_keys
        }

        # 저장소별 색상 지정
        color_map = {
            "oss2025hnu_reposcore-py": "#6baed6",   # 파랑
            "oss2025hnu_reposcore-js": "#74c476",   # 연초록
            "oss2025hnu_reposcore-cs": "#fd8d3c"    # 주황
        }

        bottom = [0] * len(usernames)
        plt.figure(figsize=(12, max(4, len(usernames) * 0.35)))

        for repo in repo_keys:
            color = color_map.get(repo.lower(), "#bbbbbb")
            plt.barh(usernames, scores_by_repo[repo], left=bottom, label=repo.upper(), color=color)
            bottom = [b + s for b, s in zip(bottom, scores_by_repo[repo])]

        plt.xlabel("점수")
        plt.title("사용자별 저장소 기여도 (py/js/cs)")
        plt.legend(loc="upper right")
        plt.tight_layout()
        plt.yticks(range(len(ranked_usernames)), ranked_usernames)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()

    def generate_weekly_chart(self, weekly_data: dict[int, dict[str, int]], semester_start_date: date, save_path: str) -> None:
        """주차별 PR/이슈 활동량을 막대그래프로 시각화하여 저장"""

        weeks = sorted(weekly_data.keys())
        pr_counts = [weekly_data[w]["pr"] for w in weeks]
        issue_counts = [weekly_data[w]["issue"] for w in weeks]

        x = np.arange(len(weeks))
        width = 0.35  # 막대 너비

        plt.figure(figsize=(10, 4))
        plt.bar(x - width/2, pr_counts, width, label="PR", color='skyblue')
        plt.bar(x + width/2, issue_counts, width, label="Issue", color='lightgreen')

        plt.xlabel("주차")
        plt.ylabel("건수")
        plt.title("주차별 GitHub 활동량 (PR/Issue)")
        plt.xticks(x, [f"Week {w}" for w in weeks])
        plt.legend()
        plt.tight_layout()
        plt.savefig(save_path)
        plt.close()
