#!/usr/bin/env python3
import json
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import pandas as pd
from prettytable import PrettyTable
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from .common_utils import *
from .theme_manager import ThemeManager 

import logging
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

    def generate_table(self, scores: dict[str, dict[str, float]], save_path) -> None:
        """결과를 테이블 형태로 출력"""
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
            f.write(str(table))

    def generate_count_csv(self, scores: dict, save_path: str = None) -> None:
        """결과를 CSV 파일로 출력"""
        df = pd.DataFrame.from_dict(scores, orient='index')
        # grade 컬럼 제거
        df = df.drop('grade', axis=1, errors='ignore')
        df = df.round(1)
        df.index.name = 'name'  # 인덱스 이름을 'name'으로 설정
        df.to_csv(save_path, encoding='utf-8')

    def generate_text(self, scores: dict[str, dict[str, float]], save_path) -> None:
        """결과를 텍스트 파일로 출력"""
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write("=== 참여자별 점수 ===\n\n")
            
            for name, score in scores.items():
                # 등급 계산
                grade = self._calculate_grade(score['total'])
                f.write(f"📊 {name}\n")
                f.write(f"   총점: {score['total']:.1f} ({grade})\n")
                f.write(f"   PR(기능/버그): {score['feat/bug PR']:.1f}\n")
                f.write(f"   PR(문서): {score['document PR']:.1f}\n")
                f.write(f"   PR(오타): {score['typo PR']:.1f}\n")
                f.write(f"   이슈(기능/버그): {score['feat/bug issue']:.1f}\n")
                f.write(f"   이슈(문서): {score['document issue']:.1f}\n\n")

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
        """결과를 차트로 출력"""
        # Linux 환경에서 CJK 폰트 수동 설정
        # OSS 한글 폰트인 본고딕, 나눔고딕, 백묵 중 순서대로 하나를 선택
        font_paths = [
            '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',  # 나눔고딕
            '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',  # 본고딕
            '/usr/share/fonts/truetype/baekmuk/baekmuk.ttf'  # 백묵
        ]
        
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

        # 막대 그리기
        pr_bars = ax.barh([y - bar_height/2 for y in y_pos], pr_scores, 
                         height=bar_height, label='PR', color='skyblue')
        issue_bars = ax.barh([y + bar_height/2 for y in y_pos], issue_scores, 
                            height=bar_height, label='이슈', color='lightgreen')

        # 점수 표시
        for i, (pr, issue, total) in enumerate(zip(pr_scores, issue_scores, total_scores)):
            if show_grade:
                grade = self._calculate_grade(total)
                ax.text(total + 1, i, f'{total:.1f} ({grade})', 
                       va='center', fontsize=self.CHART_CONFIG['font_size'])
            else:
                ax.text(total + 1, i, f'{total:.1f}', 
                       va='center', fontsize=self.CHART_CONFIG['font_size'])

        # 축 설정
        ax.set_yticks(y_pos)
        ax.set_yticklabels(participants)
        ax.set_xlabel('점수')
        ax.set_title('참여자별 활동 점수')
        ax.invert_yaxis()

        # 범례 추가
        ax.legend()

        # 여백 조정
        plt.tight_layout()

        # 저장
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close() 
