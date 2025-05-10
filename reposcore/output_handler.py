#!/usr/bin/env python3
import json
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import pandas as pd
from prettytable import PrettyTable
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from .common_utils import log
from .theme_manager import ThemeManager

import sys
import os

class OutputHandler:
    """Class to handle output generation for repository analysis results"""
    
    # 차트 설정
    CHART_CONFIG = {
        'height_per_participant': 0.4,  # 참여자당 차트 높이
        'min_height': 3.0,              # 최소 차트 높이
        'bar_height': 0.5,              # 막대 높이
        'figure_width': 12,             # 차트 너비 (텍스트 잘림 방지 위해 증가)
        'font_size': 9,                 # 폰트 크기
        'text_padding': 0.1             # 텍스트 배경 상자 패딩
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
        # 등수 컬럼 추가
        table.field_names = ["등수", "참여자", "총점", "등급", "PR(기능/버그)", "PR(문서)", "PR(오타)", "이슈(기능/버그)", "이슈(문서)"]
        
        # 등수 카운터 초기화
        rank = 1
        for name, score in scores.items():
            # 등급 계산
            grade = self._calculate_grade(score['total'])
            row = [
                rank, # 등수 추가
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
            rank += 1 # 등수 증가
        
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(f"=== 참여자별 점수 (분석 기준 시각: {timestamp}) ===\n\n")
            f.write(str(table))

    def generate_count_csv(self, scores: dict, save_path: str = None) -> None:
        """결과를 CSV 파일로 출력"""
        timestamp = self.get_kst_timestamp()
        df = pd.DataFrame.from_dict(scores, orient='index')
        # grade 컬럼 제거 (기존 코드 유지 - 불필요 시 제거 가능)
        df = df.drop('grade', axis=1, errors='ignore')
        df = df.round(1)
        df.index.name = 'name'  # 인덱스 이름을 'name'으로 설정

        df.to_csv(save_path, encoding='utf-8')

    def generate_text(self, scores: dict[str, dict[str, float]], save_path) -> None:
        """결과를 텍스트 파일로 출력"""
        timestamp = self.get_kst_timestamp()
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(f"=== 참여자별 점수 (분석 기준 시각: {timestamp}) ===\n\n")
            
            # 등수 카운터 초기화
            rank = 1
            for name, score in scores.items():
                # 등급 계산
                grade = self._calculate_grade(score['total'])
                # 등수 추가하여 출력
                f.write(f"📊 {rank}위 - {name}\n")
                f.write(f"    총점: {score['total']:.1f} ({grade})\n")
                f.write(f"    PR(기능/버그): {score['feat/bug PR']:.1f}\n")
                f.write(f"    PR(문서): {score['document PR']:.1f}\n")
                f.write(f"    PR(오타): {score['typo PR']:.1f}\n")
                f.write(f"    이슈(기능/버그): {score['feat/bug issue']:.1f}\n")
                f.write(f"    이슈(문서): {score['document issue']:.1f}\n\n")
                rank += 1 # 등수 증가

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
            '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',  # 본고딕 (NotoSansCJK-Regular.ttc 또는 NotoSansKR-Regular.otf 등)
            '/usr/share/fonts/truetype/baekmuk/baekmuk.ttf'  # 백묵
        ]

        timestamp = self.get_kst_timestamp()

        for font_path in font_paths:
            if os.path.exists(font_path):
                fm.fontManager.addfont(font_path)
                # matplotlib의 기본 폰트 설정을 업데이트하여 한글 지원
                plt.rcParams['font.family'] = 'sans-serif'
                plt.rcParams['font.sans-serif'] = ['NanumGothic', 'Noto Sans CJK JP', 'Baekmuk'] # 리스트 순서대로 찾음
                plt.rcParams['axes.unicode_minus'] = False # 마이너스 부호 깨짐 방지 - 추가된 라인
                break

        # 참여자 수에 따라 차트 높이 조정
        num_participants = len(scores)
        chart_height = max(self.CHART_CONFIG['min_height'], 
                           num_participants * self.CHART_CONFIG['height_per_participant'])

        # 차트 생성
        fig, ax = plt.subplots(figsize=(self.CHART_CONFIG['figure_width'], chart_height))
        
        # 데이터 준비 (참여자 이름은 등수와 함께 사용)
        participants = list(scores.keys())
        pr_scores = [scores[p]['feat/bug PR'] + scores[p]['document PR'] + scores[p]['typo PR'] for p in participants]
        issue_scores = [scores[p]['feat/bug issue'] + scores[p]['document issue'] for p in participants]
        total_scores = [scores[p]['total'] for p in participants]

        # y축 레이블에 등수 추가
        ranked_labels = [f"{i+1}위 - {name}" for i, name in enumerate(participants)] # 등수 포함 레이블 생성

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

        # 점수 표시 (텍스트에 등수 포함 여부는 선택 사항 - 여기서는 총점만 표시)
        for i, total in enumerate(total_scores):
            # 등수 정보를 y축 레이블에서 이미 제공하므로, 여기서는 총점과 등급만 표시하도록 유지
            # 만약 텍스트 옆에도 등수를 함께 표시하고 싶다면 f'{i+1}위 {total:.1f}' 등으로 수정
            if show_grade:
                grade = self._calculate_grade(total)
                ax.text(total + 1, i, f'{total:.1f} ({grade})', 
                        va='center', fontsize=self.CHART_CONFIG['font_size'])
            else:
                ax.text(total + 1, i, f'{total:.1f}', 
                        va='center', fontsize=self.CHART_CONFIG['font_size'])

        # 축 설정
        ax.set_yticks(y_pos)
        ax.set_yticklabels(ranked_labels) # 등수 포함 레이블 사용
        ax.set_xlabel('Score')
        ax.set_title('Repository Contribution Scores')
        ax.invert_yaxis()

        # 범례 추가 (테두리 없음)
        ax.legend(loc='upper right', frameon=False)

        # 가로축 여백 조정 (텍스트 잘림 방지)
        max_score = max(total_scores) if total_scores else 100
        ax.set_xlim(0, max_score + max_score * self.CHART_CONFIG['text_padding'])

        plt.gcf().text(
            0.95, 0.01,
            f"분석 기준 시각: {timestamp}",
            ha='right',
            va='bottom',
            fontsize=8,
            color='gray'
        )

        # 여백 조정
        plt.tight_layout()

        # 저장
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()