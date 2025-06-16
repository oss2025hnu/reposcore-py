#!/usr/bin/env python3
import logging
logging.getLogger('matplotlib').setLevel(logging.WARNING)

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime, date
from zoneinfo import ZoneInfo
from prettytable import PrettyTable


from .theme_manager import ThemeManager

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

    def __init__(self, theme: str = 'default', dry_run: bool = False):
        self.theme_manager = ThemeManager()  # 테마 매니저 초기화
        self.set_theme(theme)                # 테마 설정
        self.dry_run = dry_run              

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
    

    def _summarize_scores(self, scores: dict[str, dict[str, float]]) -> tuple[float, float, float]:
        """점수 딕셔너리에서 평균, 최고점, 최저점을 계산해서 반환"""
        total_scores = [score["total"] for score in scores.values()]
        
        if not total_scores:
            return 0.0, 0.0, 0.0  # 점수가 없는 경우 방어 처리

        avg_score = sum(total_scores) / len(total_scores)
        max_score = max(total_scores)
        min_score = min(total_scores)

        return avg_score, max_score, min_score


    @staticmethod
    def get_kst_timestamp() -> str:
        """현재 KST(한국 시간) 기준 타임스탬프 반환"""
        kst = ZoneInfo("Asia/Seoul")
        return datetime.now(tz=kst).strftime("%Y-%m-%d %H:%M:%S (KST)")

    def generate_table(self, scores: dict[str, dict[str, float]], save_path) -> None:
        """결과를 테이블 형태로 출력"""
        if self.dry_run:
            print(f"[DRY-RUN] 테이블 저장 생략 (예상 경로: {save_path})")
            return
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

        # 평균, 최고점, 최저점
        avg_score, max_score, min_score = self._summarize_scores(scores)
        
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(f"=== 참여자별 점수 (분석 기준 시각: {timestamp}) ===\n\n")
            f.write("[요약 통계]\n")
            f.write(f"- 평균 점수: {avg_score:.1f}\n")
            f.write(f"- 최고 점수: {max_score:.1f}\n")
            f.write(f"- 최저 점수: {min_score:.1f}\n\n")
            f.write(str(table))

    def generate_count_csv(self, scores: dict, save_path: str = None) -> None:
        """결과를 CSV 파일로 출력"""
        timestamp = self.get_kst_timestamp()
        df = pd.DataFrame.from_dict(scores, orient='index')
        if 'rank' in df.columns:
            df.insert(0, 'rank', df.pop('rank'))
            df = df.sort_values('rank')
        df = df.drop('grade', axis=1, errors='ignore')
        df = df.round(1)
        df.index.name = 'name'  # 인덱스 이름을 'name'으로 설정
        df.to_csv(save_path, encoding='utf-8')


    def generate_text(self, scores: dict[str, dict[str, float]], save_path: str) -> None:
        """PrettyTable을 사용해 참여자 점수를 표 형식으로 출력"""
        timestamp = self.get_kst_timestamp()

        sorted_scores = dict(sorted(scores.items(), key=lambda x: x[1].get('rank', 0)))

        table = PrettyTable()
        table.field_names = [
            "Rank","Name", "Total Score", "Grade",
            "PR (Feature/Bug)", "PR (Docs)", "PR (Typos)",
            "Issue (Feature/Bug)", "Issue (Docs)"
        ]

        for rank, (name, score) in enumerate(scores.items(), start=1):
            grade = self._calculate_grade(score["total"])
            table.add_row([
                int(score['rank']),
                name,
                int(score['total']),
                grade,
                int(score['feat/bug PR']),
                int(score['document PR']),
                int(score['typo PR']),
                int(score['feat/bug issue']),
                int(score['document issue']),
            ])
        
        # 평균, 최고점, 최저점
        avg_score, max_score, min_score = self._summarize_scores(scores)

        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(f"=== 참여자별 점수 (분석 기준 시각: {timestamp}) ===\n\n")
            f.write("[요약 통계]\n")
            f.write(f"- 평균 점수: {avg_score:.1f}\n")
            f.write(f"- 최고 점수: {max_score:.1f}\n")
            f.write(f"- 최저 점수: {min_score:.1f}\n\n")
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

        theme_colors = self.theme_manager.themes[self.theme_manager.current_theme]
        chart_style = theme_colors.get("chart", {}).get("style", {})
        pr_color = chart_style.get("primary", "#4e79a7")
        issue_color = chart_style.get("secondary", "#f28e2c")
        text_color = chart_style.get("text", "#212529")
        bg_color = chart_style.get("background", "#ffffff")
        grid_color = chart_style.get("grid", "#e9ecef")

        # Linux 환경에서 CJK 폰트 수동 설정
        # OSS 한글 폰트인 본고딕, 나눔고딕, 백묵 중 순서대로 하나를 선택
        font_paths = [
            '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',  # 나눔고딕
            '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',  # 본고딕
            '/usr/share/fonts/truetype/baekmuk/baekmuk.ttf'  # 백묵
        ]

        sorted_items = sorted(scores.items(), key=lambda x: x[1].get("rank", 0))
        sorted_scores = dict(sorted_items)

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

        participants = list(sorted_scores.keys())
        pr_scores = [sorted_scores[p]['feat/bug PR'] + sorted_scores[p]['document PR'] + sorted_scores[p]['typo PR'] for p in participants]
        issue_scores = [sorted_scores[p]['feat/bug issue'] + sorted_scores[p]['document issue'] for p in participants]
        total_scores = [sorted_scores[p]['total'] for p in participants]
        
        ranked_participants = [f"{user} ({get_ordinal_suffix(int(sorted_scores[user].get("rank", 0)))})" for user in participants]

        timestamp = self.get_kst_timestamp()

        # 정렬된 참여자 리스트 만들기
        sorted_scores = sorted(scores.items(), key=lambda x: x[1]["total"], reverse=True)
        participants = [user for user, _ in sorted_scores]
        total_scores = [score_data["total"] for _, score_data in sorted_scores]
        pr_scores = [score_data["feat/bug PR"] + score_data["document PR"] + score_data["typo PR"] for _, score_data in sorted_scores]
        issue_scores = [score_data["feat/bug issue"] + score_data["document issue"] for _, score_data in sorted_scores]

        # 등수 붙이기
        ranked_participants = [f"{user} ({get_ordinal_suffix(int(scores[user].get('rank', 0)))})" for user in participants]

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

        fig.patch.set_facecolor(bg_color)        
        ax.set_facecolor(bg_color)               
        ax.tick_params(colors=text_color)        
        ax.xaxis.label.set_color(text_color)    
        ax.yaxis.label.set_color(text_color)    
        ax.title.set_color(text_color)           
        ax.spines['bottom'].set_color(grid_color)
        ax.spines['top'].set_color(grid_color)
        ax.spines['left'].set_color(grid_color)
        ax.spines['right'].set_color(grid_color)
        
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

        pr_ratio, issue_ratio, _ = self._calculate_activity_ratios(scores)
        
        x_offset = max(total_scores) * 0.02  # 전체 점수의 2%만큼 오른쪽으로

        # 점수 및 PR/Issue 비율 표시
        for i, user in enumerate(participants):
            total = total_scores[i]
            grade = self._calculate_grade(total)

            pr_score = pr_scores[i]
            issue_score = issue_scores[i]
            total_contrib = pr_score + issue_score
            pr_ratio = pr_score / total_contrib if total_contrib else 0
            issue_ratio = issue_score / total_contrib if total_contrib else 0

            # 두 줄로 출력 (줄바꿈)
            label = f'{total:.1f} ({grade})\nP:{int(pr_ratio*100)}% I:{int(issue_ratio*100)}%'

            # 위치 조정 (짧은 막대 보호)
            x_offset = max(total_scores) * 0.02
            text_x = total + x_offset if total > 3 else total + 2.0

            # 폰트 크기 조절
            ax.text(text_x, i, label, va='center', fontsize=8, color=text_color)

        # 평균, 최고점, 최저점
        avg_score, max_score, min_score = self._summarize_scores(scores)

        # 축 설정
        ax.set_yticks(range(len(ranked_participants)))
        ax.set_yticklabels(ranked_participants)
        ax.set_xlabel('Score')
    if self.theme == "dark":
        ax.tick_params(colors='white')
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_color('white')
        title_color = 'white'
    else:
        title_color = 'title_color'

        ax.set_title(
            f'Repository Contribution Scores\n(Generated at {timestamp})',
            fontsize=14,
            loc='center',  # 또는 'left', 'right'
            color='black'
        )
        ax.text(
            1.0,
            1.0,
            f"avg_score: {avg_score:.1f} / max_score: {max_score:.1f} / min_score: {min_score:.1f}",
            transform=ax.transAxes,
            ha='right',
            va='top',
            fontsize=10,
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
        plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
        plt.close() 

    def generate_repository_stacked_chart(self, scores: dict, save_path: str):
        if not scores:
            return

        # ✅ 모든 사용자 기준으로 저장소 키 수집
        repo_keys = set()
        for user_data in scores.values():
            repo_keys.update([k for k in user_data.keys() if k not in ["total", "grade", "rank"]])
        repo_keys = sorted(repo_keys)  # 보기 좋게 정렬해도 OK

        # 총점 기준 내림차순 정렬
        sorted_users = sorted(scores.items(), key=lambda x: x[1].get("rank", float('inf')))
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

        ranked_usernames = [f"{user} ({get_ordinal_suffix(score.get('rank', 0))})" for user, score in sorted_users]

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

        # 막대 옆에 총점 수치 표시
        for i, user in enumerate(usernames):
            total_score = sum(scores[user].get(repo, 0) for repo in repo_keys)
            plt.text(
                bottom[i] + 1,  # 막대 끝에서 오른쪽으로 1만큼 띄움
                i,              # y 좌표 (사용자 위치)
                f"{total_score:.1f}",  # 소수점 1자리로 점수 표시
                va='center',
                fontsize=9,
                color='black'
            )


        plt.xlabel("Score")
        plt.title("Repository Contribution Scores (py/js/cs)")
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

        plt.xlabel("Week")
        plt.ylabel("Count")
        plt.title("GitHub Activity per Week (PR/Issue)")
        plt.xticks(x, [f"Week {w}" for w in weeks])
        plt.legend()
        plt.tight_layout()
        plt.savefig(save_path)
        plt.close()

    def _get_chart_base64(self, chart_path: str) -> str:
        """차트 이미지를 HTML에 삽입하기 위해 base64로 변환"""
        import base64
        with open(chart_path, 'rb') as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')

    def _generate_score_table_html(self, scores: dict, repo_name: str) -> str:
        """점수 테이블 HTML 생성"""
        # 총점 기준으로 사용자 정렬
        sorted_scores = dict(sorted(scores.items(), key=lambda x: x[1].get('rank', 0)))
        
        html = f"""
        <div class="table-responsive">
            <h3>{repo_name} 참여자 점수</h3>
            <table class="table table-striped table-hover">
                <thead class="table-dark">
                    <tr>
                        <th>순위</th>
                        <th>이름</th>
                        <th>총점</th>
                        <th>등급</th>
                    </tr>
                </thead>
                <tbody>
        """.format(repo_name=repo_name)
        
        sorted_scores = dict(sorted(scores.items(), key=lambda x: x[1].get('rank', 0)))
        for user, score_data in sorted_scores.items():
            total_score = score_data.get('total', 0)
            grade = self._calculate_grade(total_score)
            html += f"""
                    <tr>
                        <td>{score_data.get('rank', '-')}</td>
                        <td>{user}</td>
                        <td>{total_score:.1f}</td>
                        <td>{grade}</td>
                    </tr>        
            """

        html += """
                </tbody>
            </table>
        </div>
        """
        return html

    def generate_html_report(self, all_repo_data: dict, output_dir: str) -> str:
        """
        모든 저장소에 대한 단일 HTML 보고서 생성
        """
        import os

        # 출력 디렉토리 생성
        os.makedirs(output_dir, exist_ok=True)

        # HTML 파일 경로 (항상 index.html로 고정)
        html_path = os.path.join(output_dir, "index.html")

        # 탭 헤더와 콘텐츠 초기화
        tabs_header = []
        tabs_content = []

        # 중복 추가 방지용 집합
        added_tabs = set()
                
        # overall이 존재할 경우 맨 앞의 순서로 변경
        sorted_items = sorted(all_repo_data.items(), key=lambda x: (x[0] != 'overall', x[0]))

        # 각 저장소별로 탭과 콘텐츠 생성
        for i, (repo_name, repo_data) in enumerate(sorted_items):
            if repo_name in added_tabs:
                continue  # 중복 방지

            scores = repo_data.get('scores', {})
            chart_path = repo_data.get('chart_path', '')
            weekly_chart_path = repo_data.get('weekly_chart_path', '')

            # 상대 경로로 변환 (HTML에서의 경로)
            if repo_name == "overall_repository":
                rel_chart_path = os.path.join("overall", os.path.basename(chart_path)) if chart_path else ''
            else:
                rel_chart_path = os.path.join(repo_name, os.path.basename(chart_path)) if chart_path else ''
            rel_weekly_chart_path = os.path.join(repo_name, os.path.basename(weekly_chart_path)) if weekly_chart_path else ''

            # CSV 다운로드 버튼 추가
            if repo_name == "overall":
                csv_path = "overall/ratio_score.csv"
            elif repo_name == "overall_repository":
                csv_path = "overall/overall_scores.csv"
            else:
                csv_path = f"{repo_name}/score.csv"

            download_button = f"""
            <div class="text-end mt-2 mb-3">
                <a href="{csv_path}" download class="btn btn-outline-primary">Download Score CSV</a>
            </div>
            """

            # 탭 활성화 상태 설정 (첫 번째 탭만 활성화)
            active_class = "active" if not tabs_header else ""

            # 탭 헤더 추가
            tabs_header.append(f"""
            <li class="nav-item">
                <a class="nav-link {active_class}" id="tab-{repo_name}" data-bs-toggle="tab" href="#content-{repo_name}" role="tab">
                    {repo_name.replace('_', ' ').title().lower()}
                </a>
            </li>
            """)

            # 차트 이미지 태그 생성
            chart_img = f'<img src="{rel_chart_path}" class="img-fluid" alt="{repo_name} 차트">' if rel_chart_path else '<p>차트를 사용할 수 없습니다.</p>'

            # 주간 차트 이미지 태그 생성 (있을 경우)
            weekly_chart_section = ''
            if rel_weekly_chart_path:
                weekly_chart_section = f"""
                <div class="mt-4">
                    <h4>주간 활동량</h4>
                    <img src="{rel_weekly_chart_path}" class="img-fluid" alt="{repo_name} 주간 활동량 차트">
                </div>
                """

            # 점수 테이블 생성
            score_table = self._generate_score_table_html(scores, repo_name)

            # 탭 콘텐츠 추가
            tabs_content.append(f"""
            <div class="tab-pane fade show {active_class}" id="content-{repo_name}" role="tabpanel">
                <div class="row">
                    {download_button}
                    <div class="col-lg-6">
                        <h4>기여도 차트</h4>
                        {chart_img}
                        {weekly_chart_section}
                    </div>
                    <div class="col-lg-6">
                        {score_table}
                    </div>
                </div>
            </div>
            """)

            # 중복 추가 방지용으로 집합에 추가
            added_tabs.add(repo_name)

        # HTML 템플릿
        timestamp = self.get_kst_timestamp()

        # HTML 생성
        html = f"""
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>GitHub 저장소 분석 보고서</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container">
                <div class="report-header text-center">
                    <h1>GitHub 저장소 분석 보고서</h1>
                    <p class="text-muted">생성 일시: {timestamp}</p>
                </div>
                
                <ul class="nav nav-tabs" id="repoTabs" role="tablist">
                    {"".join(tabs_header)}
                </ul>
                
                <div class="tab-content" id="repoTabsContent">
                    {"".join(tabs_content)}
                </div>
            </div>
            
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        </body>
        </html>
        """

        # HTML 파일 저장
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)

        return html_path
