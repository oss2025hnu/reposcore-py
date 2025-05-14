#!/usr/bin/env python3

import argparse
import sys
import os
import requests
from datetime import datetime
import json
import logging

from .common_utils import *
from .github_utils import *
from .analyzer import RepoAnalyzer
from .output_handler import OutputHandler
from . import common_utils

#포맷 상수 임포
from reposcore.constants import FORMAT_TABLE, FORMAT_TEXT, FORMAT_CHART, FORMAT_ALL, VALID_FORMATS, VALID_FORMATS_DISPLAY

# 친절한 오류 메시지를 출력할 ArgumentParser 클래스
class FriendlyArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        if '--format' in message:
            # --format 옵션에서만 오류 메시지를 사용자 정의
            logging.error(f"❌ 인자 오류: {message}")
            logging.error(f"사용 가능한 --format 값: {VALID_FORMATS_DISPLAY}")
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
        nargs="+",
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
        help="API 요청 제한 해제를 위한 깃허브 개인 액세스 토큰"
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
    return parser.parse_args()

args = parse_arguments()

def handle_individual_user_mode(args):
    repo = args.repository[0]
    analyzer = RepoAnalyzer(repo, token=args.token, theme=args.theme)
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

if args.user:                        
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


def main() -> None:
    """Main execution function"""
    args = parse_arguments()
    common_utils.is_verbose = args.verbose
    github_token = args.token
    if not args.token:
        github_token = os.getenv('GITHUB_TOKEN')
    elif args.token == '-':
        github_token = sys.stdin.readline().strip()

    if github_token and len(github_token) != 0:
        validate_token(github_token)

    # --check-limit 옵션 처리: 이 옵션이 있으면 repository 인자 없이 실행됨.
    if args.check_limit:
        check_rate_limit(token=github_token)
        sys.exit(0)

    # --user-info 옵션으로 지정된 파일이 존재하는지, JSON 파싱이 가능한지 검증
    if args.user_info:
        # 1) 파일 존재 여부 확인
        if not os.path.isfile(args.user_info):
            logging.error("❌ 사용자 정보 파일을 찾을 수 없습니다.")
            sys.exit(1)
        # 2) JSON 문법 오류 확인
        try:
            with open(args.user_info, "r", encoding="utf-8") as f:
                user_info = json.load(f)
        except json.JSONDecodeError:
            logging.error("❌ 사용자 정보 파일이 올바른 JSON 형식이 아닙니다.")
            sys.exit(1)
    else:
        user_info = None

    repositories: list[str] = args.repository
    # 쉼표로 여러 저장소가 입력된 경우 분리
    final_repositories = list(dict.fromkeys(
        [r.strip() for repo in repositories for r in repo.split(",") if r.strip()]
    ))

    # 각 저장소 유효성 검사
    for repo in final_repositories:
        if not validate_repo_format(repo):
            logging.error(f"오류: 저장소 '{repo}'는 'owner/repo' 형식으로 입력해야 합니다. 예) 'oss2025hnu/reposcore-py'")
            sys.exit(1)
        if not check_github_repo_exists(repo):
            logging.warning(f"입력한 저장소 '{repo}'가 깃허브에 존재하지 않을 수 있음.")
            sys.exit(1)

    log(f"저장소 분석 시작: {', '.join(final_repositories)}", force=True)

    overall_participants = {}
    
    #저장소별로 분석 후 '개별 결과'도 저장하기
    for repo in final_repositories:
        log(f"분석 시작: {repo}", force=True)

        analyzer = RepoAnalyzer(repo, token=github_token, theme=args.theme)
        output_handler = OutputHandler(theme=args.theme)

        # 저장소별 캐시 파일 생성 (예: cache_oss2025hnu_reposcore-py.json)
        cache_file_name = f"cache_{repo.replace('/', '_')}.json"
        cache_path = os.path.join(args.output, cache_file_name)

        os.makedirs(args.output, exist_ok=True)

        cache_update_required = os.path.exists(cache_path) and analyzer.is_cache_update_required(cache_path)

        if args.use_cache and os.path.exists(cache_path) and not cache_update_required:
            log(f"✅ 캐시 파일({cache_file_name})이 존재합니다. 캐시에서 데이터를 불러옵니다.", force=True)
            with open(cache_path, "r", encoding="utf-8") as f:
                cached_json = json.load(f)
                analyzer.participants = cached_json['participants']
                analyzer.previous_create_at = cached_json['update_time']
        else:
            if args.use_cache and cache_update_required:
                log(f"🔄 리포지토리의 최근 이슈 생성 시간이 캐시파일의 생성 시간보다 최근입니다. GitHub API로 데이터를 수집합니다.", force=True)
            else:
                log(f"�� 캐시를 사용하지 않거나 캐시 파일({cache_file_name})이 없습니다. GitHub API로 데이터를 수집합니다.", force=True)
            analyzer.collect_PRs_and_issues()
            if not getattr(analyzer, "_data_collected", True):
                logging.error("❌ GitHub API 요청에 실패했습니다. 결과 파일을 생성하지 않고 종료합니다.")
                logging.error("ℹ️ 인증 없이 실행한 경우 요청 횟수 제한(403)일 수 있습니다. --token 옵션을 사용해보세요.")
                sys.exit(1)
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump({'update_time':analyzer.previous_create_at, 'participants': analyzer.participants}, f, indent=2, ensure_ascii=False)

        try:
            # 1) 사용자 정보 로드 (없으면 None)
            user_info = json.load(open(args.user_info, "r", encoding="utf-8")) \
                if args.user_info and os.path.exists(args.user_info) else None

            # 스코어 계산
            repo_scores = analyzer.calculate_scores(user_info)

            # --user 옵션이 지정된 경우 사용자 점수 및 등수 출력
            user_lookup_name = user_info.get(args.user, args.user) if args.user and user_info else args.user
            if args.user and user_lookup_name in repo_scores:
                sorted_users = list(repo_scores.keys())
                user_rank = sorted_users.index(user_lookup_name) + 1
                user_score = repo_scores[user_lookup_name]["total"]
                log(f"[INFO] 사용자: {user_lookup_name}", force=True)
                log(f"[INFO] 총점: {user_score:.2f}점", force=True)
                log(f"[INFO] 등수: {user_rank}등 (전체 {len(sorted_users)}명 중)", force=True)
            elif args.user:
                log(f"[INFO] 사용자 '{args.user}'의 점수가 계산된 결과에 없습니다.", force=True)

            # 출력 형식
            formats = set(args.format)
            if FORMAT_ALL in formats:
                formats = {FORMAT_TABLE, FORMAT_TEXT, FORMAT_CHART}

            # 저장소별 폴더 생성 (owner/repo -> owner_repo)
            repo_safe_name = repo.replace('/', '_')
            repo_output_dir = os.path.join(args.output, repo_safe_name)
            os.makedirs(repo_output_dir, exist_ok=True)

            # 1) CSV 테이블 저장
            if FORMAT_TABLE in formats:
                table_path = os.path.join(repo_output_dir, "score.csv")
                output_handler.generate_table(repo_scores, save_path=table_path)
                output_handler.generate_count_csv(repo_scores, save_path=table_path)
                log(f"CSV 파일 저장 완료: {table_path}", force=True)

            # 2) 텍스트 테이블 저장
            if FORMAT_TEXT in formats:
                txt_path = os.path.join(repo_output_dir, "score.txt")
                output_handler.generate_text(repo_scores, txt_path)
                log(f"텍스트 파일 저장 완료: {txt_path}", force=True)

            # 3) 차트 이미지 저장
            if FORMAT_CHART in formats:
                chart_filename = "chart_grade.png" if args.grade else "chart.png"
                chart_path = os.path.join(repo_output_dir, chart_filename)
                output_handler.generate_chart(repo_scores, save_path=chart_path, show_grade=args.grade)
                log(f"차트 이미지 저장 완료: {chart_path}", force=True)

            # 전체 참여자 데이터 병합
            overall_participants = merge_participants(overall_participants, analyzer.participants)

        except Exception as e:
            logging.error(f"❌ 저장소 '{repo}' 분석 중 오류 발생: {str(e)}")
            continue

    # 전체 저장소 통합 분석
    if len(final_repositories) > 1:
        log("\n=== 전체 저장소 통합 분석 ===", force=True)
        
        # 통합 분석을 위한 analyzer 생성
        overall_analyzer = RepoAnalyzer("multiple_repos", token=github_token, theme=args.theme)
        overall_analyzer.participants = overall_participants
        
        # 통합 점수 계산
        overall_scores = overall_analyzer.calculate_scores(user_info)

        # --user 옵션이 지정된 경우 통합 점수에서 출력
        user_lookup_name = user_info.get(args.user, args.user) if args.user and user_info else args.user
        if args.user and user_lookup_name in overall_scores:
            sorted_users = list(overall_scores.keys())
            user_rank = sorted_users.index(user_lookup_name) + 1
            user_score = overall_scores[user_lookup_name]["total"]
            log(f"[INFO] 사용자: {user_lookup_name}", force=True)
            log(f"[INFO] 총점: {user_score:.2f}점", force=True)
            log(f"[INFO] 등수: {user_rank}등 (전체 {len(sorted_users)}명 중)", force=True)
        elif args.user:
            log(f"[INFO] 사용자 '{args.user}'의 점수가 통합 분석 결과에 없습니다.", force=True)
        
        # 통합 결과 저장
        overall_output_dir = os.path.join(args.output, "overall")
        os.makedirs(overall_output_dir, exist_ok=True)
        
        # 1) CSV 테이블 저장
        if FORMAT_TABLE in formats:
            table_path = os.path.join(overall_output_dir, "score.csv")
            output_handler.generate_table(overall_scores, save_path=table_path)
            output_handler.generate_count_csv(overall_scores, save_path=table_path)
            log(f"[통합 저장소] CSV 파일 저장 완료: {table_path}", force=True)
        
        # 2) 텍스트 테이블 저장
        if FORMAT_TEXT in formats:
            txt_path = os.path.join(overall_output_dir, "score.txt")
            output_handler.generate_text(overall_scores, txt_path)
            log(f"[통합 저장소] 텍스트 파일 저장 완료: {txt_path}", force=True)
        
        # 3) 차트 이미지 저장
        if FORMAT_CHART in formats:
            chart_filename = "chart_grade.png" if args.grade else "chart.png"
            chart_path = os.path.join(overall_output_dir, chart_filename)
            output_handler.generate_chart(overall_scores, save_path=chart_path, show_grade=args.grade)
            log(f"[통합 저장소] 차트 이미지 저장 완료: {chart_path}", force=True)

if __name__ == "__main__":
    main()
