#!/usr/bin/env python3

import argparse
import json
from collections import defaultdict
from datetime import datetime

import pandas as pd

from .analyzer import RepoAnalyzer
from .github_utils import *
from .output_handler import OutputHandler

import logging

# logging 모듈 기본 설정 (analyzer.py와 동일한 설정)
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 포맷 상수
FORMAT_TABLE = "table"
FORMAT_TEXT = "text"
FORMAT_CHART = "chart"
FORMAT_HTML = "html"
FORMAT_ALL = "all"

VALID_FORMATS = [FORMAT_TABLE, FORMAT_TEXT, FORMAT_CHART, FORMAT_HTML, FORMAT_ALL]
VALID_FORMATS_DISPLAY = ", ".join(VALID_FORMATS)

# 친절한 오류 메시지를 출력할 ArgumentParser 클래스
class FriendlyArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        if '--format' in message:
            # --format 옵션에서만 오류 메시지를 사용자 정의
            logger.error(f"❌ 인자 오류: {message}")
            logger.error(f"사용 가능한 --format 값: {VALID_FORMATS_DISPLAY}")
        else:
            super().error(message)
        sys.exit(2)

def parse_arguments() -> argparse.Namespace:
    """커맨드라인 인자를 파싱하는 함수"""
    parser = FriendlyArgumentParser(
        prog="python -m reposcore",
        usage=(
            "python -m reposcore [-h] [-v] [owner/repo ...] "
            "[--output dir_name] "
            f"[--format {{{VALID_FORMATS_DISPLAY}}}] "
            "[--check-limit] "
            "[--user-info path]"
        ),
        description="오픈 소스 수업용 레포지토리의 기여도를 분석하는 CLI 도구",
        add_help=False
    )
    # 저장소 인자를 하나 이상 받도록 nargs="+"로 변경
    parser.add_argument(
        "repository",
        type=str,
        nargs="*",
        metavar="owner/repo",
        help="분석할 GitHub 저장소들 (형식: '소유자/저장소'). 여러 저장소의 경우 공백 혹은 쉼표로 구분하여 입력"
    )
    parser.add_argument(
        "-h", "--help",
        action="help",
        help="도움말 표시 후 종료"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="자세한 로그를 출력합니다."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results",
        metavar="dir_name",
        help="분석 결과를 저장할 출력 디렉토리 (기본값: 'results')"
    )
    parser.add_argument(
        "--format",
        choices=VALID_FORMATS,
        nargs='+',
        default=[FORMAT_ALL],
        metavar=f"{{{VALID_FORMATS_DISPLAY}}}",
        help =  f"결과 출력 형식 선택 (복수 선택 가능, 예: --format {FORMAT_TABLE} {FORMAT_CHART}) (기본값:'{FORMAT_ALL}')"
    )
    parser.add_argument(
        "--grade",
        action="store_true",
        help="차트에 등급 표시"
    )
    parser.add_argument(
        "--use-cache",
        action="store_true",
        help="participants 데이터를 캐시에서 불러올지 여부 (기본: API를 통해 새로 수집)"
    )
    parser.add_argument(
        "--token",
        type=str,
        help="API 요청 제한 해제를 위한 깃허브 개인 액세스 토큰 (환경변수 GITHUB_TOKEN으로도 설정 가능)"
    )   
    parser.add_argument(
        "--check-limit",
        action="store_true",
        help="현재 GitHub API 요청 가능 횟수와 전체 한도를 확인합니다."
    )
    parser.add_argument(
        "--user-info",
        type=str,
        help="사용자 정보 파일의 경로"
    )
    parser.add_argument(
        "--user",
        type=str,
        metavar="username",
        help="특정 사용자의 점수와 등수를 출력합니다 (GitHub 사용자명)"
    )
    parser.add_argument(
        "--theme", "-t",
        choices=["default", "dark"],
        default="default",
        help="테마 선택 (default 또는 dark)"
    )
    parser.add_argument(
    "--weekly-chart",
    action="store_true",
    help="주차별 PR/이슈 활동량 차트를 생성합니다."
    )
    parser.add_argument(
        "--semester-start",
        type=str,
        help="학기 시작일 (형식: YYYY-MM-DD, 예: 2025-03-04)"
    )
    parser.add_argument(
        "--min-contributions",
        type=int,
        default=1,
        help="최소 기여 점수가 지정 값 이상인 사용자만 결과에 포함합니다.(기본값 : 1)"
    )
    parser.add_argument(
    "--dry-run",
    action="store_true",
    help="실제 작업 없이 시뮬레이션 정보만 출력합니다."
    )
    return parser.parse_args()

args = parse_arguments()

def handle_individual_user_mode(args):
    repo = args.repository[0]
    if not validate_repo_format(repo):
        logger.error(f"오류: 저장소 '{repo}'는 'owner/repo' 형식으로 입력해야 합니다. 예) 'oss2025hnu/reposcore-py'")
        sys.exit(1)
    if not check_github_repo_exists(repo):
        logger.warning(f"입력한 저장소 '{repo}'가 깃허브에 존재하지 않을 수 있음.")
        sys.exit(1)
    analyzer = RepoAnalyzer(repo, theme=args.theme)
    analyzer.collect_PRs_and_issues()

    user_info = None
    if args.user_info and os.path.exists(args.user_info):
        with open(args.user_info, "r", encoding="utf-8") as f:
            user_info = json.load(f)

    repo_scores = analyzer.calculate_scores(user_info)
    user_lookup_name = user_info.get(args.user, args.user) if user_info else args.user

    if user_lookup_name in repo_scores:
        sorted_users = list(repo_scores.keys())
        rank = sorted_users.index(user_lookup_name) + 1
        score = repo_scores[user_lookup_name]["total"]
        print(f"[INFO] 사용자: {user_lookup_name}")
        print(f"[INFO] 총점: {score:.2f}점")
        print(f"[INFO] 등수: {rank}등 (전체 {len(sorted_users)}명 중)")
    else:
        print(f"[INFO] 사용자 '{args.user}'의 점수를 찾을 수 없습니다.")

if args.user and len(args.repository) == 1:
    handle_individual_user_mode(args)
    sys.exit(0)

def merge_participants(
    overall: dict[str, dict[str, int]],
    new_data: dict[str, dict[str, int]]
) -> dict[str, dict[str, int]]:
    """두 participants 딕셔너리를 병합합니다."""
    for user, activities in new_data.items():
        if user not in overall:
            overall[user] = activities.copy()
        else:
            # 각 항목별로 활동수를 누적합산합니다.
            for key, value in activities.items():
                overall[user][key] = overall[user].get(key, 0) + value
    return overall

def save_cli_args(args, output_dir="results"):
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "settings.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(vars(args), f, indent=2, ensure_ascii=False)

def main() -> None:
    """Main execution function"""
    args = parse_arguments()
    save_cli_args(args, args.output)

    # repository가 없으면 에러
    if not args.repository:
        logger.error("❌ 저장소를 지정해주세요.")
        sys.exit(1)

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 토큰 처리 단순화
    if args.token:
        if args.token == '-':
            # 표준 입력에서 토큰 읽기
            github_token = sys.stdin.readline().strip()
            os.environ['GITHUB_TOKEN'] = github_token
        else:
            # 명령행 인자로 받은 토큰 설정
            os.environ['GITHUB_TOKEN'] = args.token
    
    # 토큰 검증 (환경변수에서 읽어서)
    github_token = os.getenv('GITHUB_TOKEN')
    if github_token and len(github_token) > 0:
        validate_token()

    # --check-limit 옵션 처리: 이 옵션이 있으면 repository 인자 없이 실행됨.
    if args.check_limit:
        check_rate_limit() 
        sys.exit(0)

    # --user-info 옵션으로 지정된 파일이 존재하는지, JSON 파싱이 가능한지 검증
    if args.user_info:
        # 1) 파일 존재 여부 확인
        if not os.path.isfile(args.user_info):
            logger.error("❌ 사용자 정보 파일을 찾을 수 없습니다.")
            sys.exit(1)
        # 2) JSON 문법 오류 확인
        try:
            with open(args.user_info, "r", encoding="utf-8") as f:
                user_info = json.load(f)
        except json.JSONDecodeError:
            logger.error("❌ 사용자 정보 파일이 올바른 JSON 형식이 아닙니다.")
            sys.exit(1)
    else:
        user_info = None

    repositories: list[str] = args.repository
    # 쉼표로 여러 저장소가 입력된 경우 분리
    final_repositories = list(dict.fromkeys(
        [r.strip() for repo in repositories for r in repo.split(",") if r.strip()]
    ))

    # 각 저장소 유효성 검사 (먼저 다 검사)
    for repo in final_repositories:
        if not validate_repo_format(repo):
            logger.error(f"오류: 저장소 '{repo}'는 'owner/repo' 형식으로 입력해야 합니다. 예) 'oss2025hnu/reposcore-py'")
            sys.exit(1)
        if not check_github_repo_exists(repo):
            logger.warning(f"입력한 저장소 '{repo}'가 깃허브에 존재하지 않을 수 있음.")
            sys.exit(1)

    logger.info(f"저장소 분석 시작: {', '.join(final_repositories)}")

    overall_participants = {}
    all_repo_scores = {}
    all_repo_html_data = {}  # HTML 보고서 생성을 위한 데이터 저장

    #저장소별로 분석 후 '개별 결과'도 저장하기
    try:
        from tqdm import tqdm
    except ImportError:
        print("[오류] tqdm 라이브러리가 설치되어 있지 않습니다.")
        print("다음 명령어로 설치 후 다시 실행하세요:")
        print("pip install tqdm")
        exit(1)

    # 학기 시작일 미리 처리
    semester_start_date = None
    if args.weekly_chart:
        if not args.semester_start:
            logger.error("❌ --weekly-chart 사용 시 --semester-start 날짜를 반드시 지정해야 합니다.")
            sys.exit(1)
        try:
            semester_start_date = datetime.strptime(args.semester_start, "%Y-%m-%d").date()
        except ValueError:
            logger.error("❌ 학기 시작일 형식이 잘못되었습니다. YYYY-MM-DD 형식으로 입력해 주세요.")
            sys.exit(1)

    for repo in tqdm(final_repositories, desc="저장소 분석 진행"):

        analyzer = RepoAnalyzer(repo, theme=args.theme)
        output_handler = OutputHandler(theme=args.theme)

        if args.weekly_chart:
            if not args.semester_start:
                logger.error("❌ --weekly-chart 사용 시 --semester-start 날짜를 반드시 지정해야 합니다.")
                sys.exit(1)
            try:
                semester_start_date = datetime.strptime(args.semester_start, "%Y-%m-%d").date()
                analyzer.set_semester_start_date(semester_start_date)
            except ValueError:
                logger.error("❌ 학기 시작일 형식이 잘못되었습니다. YYYY-MM-DD 형식으로 입력해 주세요.")
                sys.exit(1)

        # 저장소별 캐시 파일 생성 (예: cache_oss2025hnu_reposcore-py.json)
        cache_file_name = f"cache_{repo.replace('/', '_')}.json"
        cache_path = os.path.join(args.output, cache_file_name)

        os.makedirs(args.output, exist_ok=True)

        cache_update_required = os.path.exists(cache_path) and analyzer.is_cache_update_required(cache_path)

        if args.use_cache and os.path.exists(cache_path) and not cache_update_required:
            logger.info(f"✅ 캐시 파일({cache_file_name})이 존재합니다. 캐시에서 데이터를 불러옵니다.")
            with open(cache_path, "r", encoding="utf-8") as f:
                cached_json = json.load(f)
                analyzer.participants = cached_json['participants']
                analyzer.previous_create_at = cached_json['update_time']
        else:
            if args.use_cache and cache_update_required:
                if args.verbose:
                    logger.info(f"🔄 리포지토리의 최근 이슈 생성 시간이 캐시파일의 생성 시간보다 최근입니다. GitHub API로 데이터를 수집합니다.")
            else:
                if args.verbose:
                    logger.info(f"�� 캐시를 사용하지 않거나 캐시 파일({cache_file_name})이 없습니다. GitHub API로 데이터를 수집합니다.")
            analyzer.collect_PRs_and_issues()
            if not getattr(analyzer, "_data_collected", True):
                logger.error("❌ GitHub API 요청에 실패했습니다. 결과 파일을 생성하지 않고 종료합니다.")
                logger.error("ℹ️ 인증 없이 실행한 경우 요청 횟수 제한(403)일 수 있습니다. --token 옵션을 사용해보세요.")
                sys.exit(1)
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump({'update_time':analyzer.previous_create_at, 'participants': analyzer.participants, 'weekly_activity': dict(analyzer.weekly_activity)}, f, indent=2, ensure_ascii=False)

        try:
            # 1) 사용자 정보 로드 (없으면 None)
            user_info = json.load(open(args.user_info, "r", encoding="utf-8")) \
                if args.user_info and os.path.exists(args.user_info) else None

            # 스코어 계산
            repo_scores = analyzer.calculate_scores(user_info, min_contributions=args.min_contributions)

            # --user 옵션이 지정된 경우 사용자 점수 및 등수 출력
            user_lookup_name = user_info.get(args.user, args.user) if args.user and user_info else args.user
            if args.user and len(final_repositories) == 1 and user_lookup_name in repo_scores:
                sorted_users = list(repo_scores.keys())
                user_rank = sorted_users.index(user_lookup_name) + 1
                user_score = repo_scores[user_lookup_name]["total"]
                logger.info(f"[INFO] 사용자: {user_lookup_name}")
                logger.info(f"[INFO] 총점: {user_score:.2f}점")
                logger.info(f"[INFO] 등수: {user_rank}등 (전체 {len(sorted_users)}명 중)")
            elif args.user and len(final_repositories) == 1:
                logger.info(f"[INFO] 사용자 '{args.user}'의 점수가 계산된 결과에 없습니다.")

            # 출력 형식
            formats = set(args.format)
            if FORMAT_ALL in formats:
                formats = {FORMAT_TABLE, FORMAT_TEXT, FORMAT_CHART, FORMAT_HTML}

            # dry-run option
            if args.dry_run:
                print(f"[DRY-RUN] 저장소: {repo}")
                print(f"[DRY-RUN] 캐시 사용 여부: {'예' if args.use_cache else '아니오'}")
                print(f"[DRY-RUN] API 호출 여부: {'예정' if not args.use_cache else '스킵 가능'}")
                print(f"[DRY-RUN] 캐시 경로: {cache_path}")
                print(f"[DRY-RUN] 예상 출력 디렉토리: {os.path.join(args.output, repo.replace('/', '_'))}")
                continue

            # 저장소별 폴더 생성 (owner/repo -> owner_repo)
            repo_safe_name = repo.replace('/', '_')
            repo_output_dir = os.path.join(args.output, repo_safe_name)
            os.makedirs(repo_output_dir, exist_ok=True)
            all_repo_scores[repo_safe_name] = repo_scores

            results_saved = []

            # 1) CSV 테이블 저장
            if FORMAT_TABLE in formats or FORMAT_HTML in formats:
                table_path = os.path.join(repo_output_dir, "score.csv")
                output_handler.generate_table(repo_scores, save_path=table_path)
                output_handler.generate_count_csv(repo_scores, save_path=table_path)
                if args.verbose:
                    logger.info(f"CSV 파일 저장 완료: {table_path}")
                results_saved.append("CSV")

            # 2) 텍스트 테이블 저장
            if FORMAT_TEXT in formats:
                txt_path = os.path.join(repo_output_dir, "score.txt")
                output_handler.generate_text(repo_scores, txt_path)
                if args.verbose:
                    logger.info(f"텍스트 파일 저장 완료: {txt_path}")
                results_saved.append("TXT")

            # 3) 차트 이미지 저장
            if FORMAT_CHART in formats or FORMAT_HTML in formats:
                chart_filename = "chart_grade.png" if args.grade else "chart.png"
                chart_path = os.path.join(repo_output_dir, chart_filename)
                output_handler.generate_chart(repo_scores, save_path=chart_path, show_grade=args.grade)
                if args.verbose:
                    logger.info(f"차트 이미지 저장 완료: {chart_path}")
                results_saved.append("Chart")

            # HTML 보고서 생성을 위한 데이터 준비 (나중에 통합 HTML 생성을 위해)
            if FORMAT_HTML in formats:
                # 차트 이미지 경로 준비
                chart_filename = "chart_grade.png" if args.grade else "chart.png"
                chart_path = os.path.join(repo_output_dir, chart_filename)
                
                # 주간 차트 경로 준비
                weekly_chart_path = os.path.join(repo_output_dir, "weekly_activity.png") if args.weekly_chart else ''
                
                # 저장소별 데이터 저장
                all_repo_html_data[repo_safe_name] = {
                    'scores': repo_scores,
                    'chart_path': chart_path,
                    'weekly_chart_path': weekly_chart_path if args.weekly_chart else ''
                }

            # 최종 통합 로그 출력
            logger.info(f"{repo} 분석 결과({', '.join(results_saved)}) 저장 완료: {repo_output_dir}")
            
            # HTML 보고서는 모든 저장소 처리 후에 한 번만 생성할 예정이므로 여기서는 생성하지 않음

            # 주차별 활동 차트생성
            if args.weekly_chart:
                analyzer.set_semester_start_date(semester_start_date)
                weekly_chart_path = os.path.join(repo_output_dir, "weekly_activity.png")
                output_handler.generate_weekly_chart(analyzer.weekly_activity, semester_start_date, weekly_chart_path)

            # 전체 참여자 데이터 병합
            overall_participants = merge_participants(overall_participants, analyzer.participants)

        except Exception as e:
            logger.error(f"❌ 저장소 '{repo}' 분석 중 오류 발생: {str(e)}")
            continue

    # 전체 저장소 통합 분석
    if len(final_repositories) > 1:
        if args.weekly_chart:
            overall_weekly_activity = defaultdict(lambda: {"pr": 0, "issue": 0})
            for repo in final_repositories:
                logger.info(f"분석 시작: {repo}")

                analyzer = RepoAnalyzer(repo, theme=args.theme)
                if args.weekly_chart:
                    analyzer.set_semester_start_date(semester_start_date)

                cache_file = f"cache_{repo.replace('/', '_')}.json"
                cache_path = os.path.join(args.output, cache_file)
                if os.path.exists(cache_path):
                    with open(cache_path, "r", encoding="utf-8") as f:
                        cache_data = json.load(f)
                        repo_weekly = cache_data.get("weekly_activity", {})
                        for week_str, data in repo_weekly.items():
                            week = int(week_str)
                            overall_weekly_activity[week]["pr"] += data.get("pr", 0)
                            overall_weekly_activity[week]["issue"] += data.get("issue", 0)

            overall_output_dir = os.path.join(args.output, "overall")
            os.makedirs(overall_output_dir, exist_ok=True)

            weekly_chart_path = os.path.join(overall_output_dir, "weekly_activity.png")
            output_handler.generate_weekly_chart(overall_weekly_activity, semester_start_date, weekly_chart_path)

        logger.info("\n=== 전체 저장소 통합 분석 ===")

        # 통합 분석을 위한 analyzer 생성
        overall_analyzer = RepoAnalyzer("multiple_repos", theme=args.theme)
        overall_analyzer.participants = overall_participants

        # 통합 점수 계산
        overall_scores = overall_analyzer.calculate_scores(user_info, min_contributions=args.min_contributions)

        # 저장소별 사용자 점수 통합 데이터
        user_scores = defaultdict(dict)
        for repo_name, repo_scores in all_repo_scores.items():
            for username, score_dict in repo_scores.items():
                user_scores[username][repo_name] = score_dict["total"]
        for username in user_scores:
            user_scores[username]["total"] = sum(user_scores[username].values())

        # 정렬
        user_scores = defaultdict(dict, sorted(user_scores.items(), key=lambda x: x[1]['total'], reverse=True))
        # rank 추가
        current_rank = 1
        prev_score = None

        for i, (username, scores) in enumerate(user_scores.items()):
            current_score = scores['total']
            
            # 동점자 처리
            if prev_score is not None and current_score != prev_score:
                current_rank = i + 1
            
            user_scores[username]['rank'] = current_rank
            prev_score = current_score

        # 통합 결과 저장
        overall_output_dir = os.path.join(args.output, "overall")
        os.makedirs(overall_output_dir, exist_ok=True)

        # 결과를 HTML 데이터에 추가 (순서 수정)
        if FORMAT_HTML in formats:
            all_repo_html_data["overall"] = {
                'scores': overall_scores,
                'chart_path': os.path.join(overall_output_dir, "ratio_chart.png")
            }
            all_repo_html_data["overall_repository"] = {
                'scores': user_scores,
                'chart_path': os.path.join(overall_output_dir, "overall_chart.png")
            }

        results_saved = []
        # CSV 저장
        if FORMAT_TABLE in formats or FORMAT_HTML in formats:
            table_path = os.path.join(overall_output_dir, "ratio_score.csv")
            output_handler.generate_table(overall_scores, save_path=table_path)
            output_handler.generate_count_csv(overall_scores, save_path=table_path)
            if args.verbose:
                logger.info(f"[통합 저장소] CSV 파일 저장 완료: {table_path}")
            results_saved.append("CSV")

        # 텍스트 저장
        if FORMAT_TEXT in formats:
            txt_path = os.path.join(overall_output_dir, "ratio_score.txt")
            output_handler.generate_text(overall_scores, txt_path)
            if args.verbose:
                logger.info(f"[통합 저장소] 텍스트 파일 저장 완료: {txt_path}")
            results_saved.append("TXT")

        # 차트 이미지 저장
        if FORMAT_CHART in formats or FORMAT_HTML in formats:
            chart_filename = "chart_grade.png" if args.grade else "ratio_chart.png"
            chart_path = os.path.join(overall_output_dir, chart_filename)
            output_handler.generate_chart(overall_scores, save_path=chart_path, show_grade=args.grade)
            if args.verbose:
                logger.info(f"[통합 저장소] 차트 이미지 저장 완료: {chart_path}")
            results_saved.append("Chart")

        logger.info(f"[통합 저장소] 분석 결과({', '.join(results_saved)}) 저장 완료: {overall_output_dir}")


    # 사용자별 저장소별 점수 CSV 만드는 함수
    def generate_overall_repository_csv(all_repo_scores, output_path):
        user_scores = defaultdict(dict)

        for repo_name, repo_scores in all_repo_scores.items():
            for username, score_dict in repo_scores.items():
                user_scores[username][repo_name] = score_dict["total"]

        for username in user_scores:
            user_scores[username]["total"] = sum(user_scores[username].values())

        df = pd.DataFrame.from_dict(user_scores, orient='index').fillna(0)
        df.index.name = "name"
        column_order = [
            "oss2025hnu_reposcore-py",
            "oss2025hnu_reposcore-js",
            "oss2025hnu_reposcore-cs",
            "total"
        ]
        existing_columns = [col for col in column_order if col in df.columns]
        df = df[existing_columns]
        df = df.astype(int)
        df.reset_index(inplace=True)
        df = df[["name"] + existing_columns]
        df['rank'] = df['total'].rank(method='min', ascending=False).astype(int)
        for _, row in df.iterrows():
            username = row['name']
            user_scores[username]['rank'] = int(row['rank'])
        df = df.sort_values(by='rank')
        cols = ['rank'] + [col for col in df.columns if col != 'rank']
        df = df[cols]
        df.to_csv(output_path, encoding="utf-8", index=False)
        return user_scores
    
    if len(final_repositories) > 1:
        # 저장 경로 지정하고 생성
        overall_repo_dir = os.path.join(args.output, "overall")

        results_saved = []

        overall_csv_path = os.path.join(overall_repo_dir, "overall_scores.csv")
        user_scores = generate_overall_repository_csv(all_repo_scores, overall_csv_path)
        if args.verbose:
            logger.info(f"[📊 overall_repository] 저장소별 사용자 점수 CSV 저장 완료: {overall_csv_path}")
        results_saved.append("CSV")

        # 🔽 텍스트 파일 저장: overall_scores.txt
        from prettytable import PrettyTable

        overall_txt_path = os.path.join(overall_repo_dir, "overall_scores.txt")
        table = PrettyTable()
        table.field_names = ["Rank", "Name"] + [repo.replace("/", "_") for repo in final_repositories] + ["Total"]

        sorted_users = sorted(user_scores.items(), key=lambda x: x[1]["total"], reverse=True)

        for username, score_dict in sorted_users:
            row = [score_dict['rank'], username]
            for repo in final_repositories:
                repo_key = repo.replace("/", "_")
                row.append(score_dict.get(repo_key, 0))
            row.append(score_dict["total"])
            table.add_row(row)

        with open(overall_txt_path, "w", encoding="utf-8") as f:
            f.write(table.get_string())
        if args.verbose:
            logger.info(f"[📊 overall_repository] 저장소별 사용자 점수 TXT 저장 완료: {overall_txt_path}")
        results_saved.append("TXT")

        # 📈 통합 차트 이미지 저장
        chart_path = os.path.join(overall_repo_dir, "overall_chart.png")
        output_handler.generate_repository_stacked_chart(user_scores, save_path=chart_path)
        if args.verbose:
            logger.info(f"[📊 overall_repository] 누적 기여도 차트 저장 완료: {chart_path}")
        results_saved.append("Chart")

        logger.info(f"[📊 overall_repository] 분석 결과({', '.join(results_saved)}) 저장 완료: {overall_repo_dir}")
        logger.info(f"[📊 overall_repository] 통합 저장소 기준 사용자별 기여도는 '{overall_repo_dir}' 폴더 내 결과 파일에서 확인할 수 있습니다.")

        # --user 옵션이 지정된 경우 통합 점수에서 출력
        user_lookup_name = user_info.get(args.user, args.user) if args.user and user_info else args.user
        if args.user and user_lookup_name in overall_scores:
            sorted_users = list(overall_scores.keys())
            user_rank = sorted_users.index(user_lookup_name) + 1
            user_score = overall_scores[user_lookup_name]["total"]
            print()
            logger.info(f"[INFO] 사용자: {user_lookup_name}")
            logger.info(f"[INFO] 총점: {user_score:.2f}점")
            logger.info(f"[INFO] 등수: {user_rank}등 (전체 {len(sorted_users)}명 중)")
            print()
        elif args.user:
            logger.info(f"[INFO] 사용자 '{args.user}'의 점수가 통합 분석 결과에 없습니다.")
    
    # HTML 보고서 생성 (모든 저장소 처리 후 한 번만 실행)
    if not args.dry_run and FORMAT_HTML in formats and all_repo_html_data:
        logger.info("HTML 보고서 생성 중...")
        output_handler.generate_html_report(all_repo_html_data, args.output)
        logger.info("HTML 보고서 생성 완료")



if __name__ == "__main__":
    main()
