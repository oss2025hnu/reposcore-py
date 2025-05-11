import re
import sys
import time
import requests
import logging

def validate_repo_format(repo: str) -> bool:
    pattern = r'^[\w\-]+/[\w\-]+$'
    if re.fullmatch(pattern, repo):
        return True
    else:
        print("저장소 형식이 올바르지 않습니다. 'owner/repo' 형식으로 입력해주세요.")
        return False

def validate_token(github_token: str) -> None:
    headers = {}
    if github_token:
        headers["Authorization"] = f"token {github_token}"
    response = requests.get("https://api.github.com/user", headers=headers)
    if response.status_code != 200:
        logging.error('❌ 인증 실패: 잘못된 GitHub 토큰입니다. 토큰 값을 확인해 주세요.')
        sys.exit(1)

def check_github_repo_exists(repo: str) -> bool:
    """
    GitHub 저장소 존재 여부를 확인하는 함수.
    
    API 요청을 통해 저장소가 실제로 존재하는지 확인합니다.
    """
    url = f"https://api.github.com/repos/{repo}"
    response = requests.get(url)

    if response.status_code == 200:
        return True
    elif response.status_code == 403:
        logging.warning("⚠️ GitHub API 요청 실패: 403 (요청 횟수 초과 또는 인증 오류)")
        logging.info("ℹ️ 해결 방법: --token 옵션 또는 GITHUB_TOKEN 환경 변수 사용")
    elif response.status_code == 404:
        logging.warning(f"⚠️ 저장소 '{repo}'가 존재하지 않습니다.")
    else:
        logging.warning(f"⚠️ 요청 실패: HTTP 상태 코드 {response.status_code}")

    return False


def check_rate_limit(token: str | None = None) -> None:
    """현재 GitHub API 요청 가능 횟수와 전체 한도를 확인하고 출력하는 함수"""
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"
    response = requests.get("https://api.github.com/rate_limit", headers=headers)
    if response.status_code == 200:
        data = response.json()
        core = data.get("resources", {}).get("core", {})
        remaining = core.get("remaining", "N/A")
        limit = core.get("limit", "N/A")
        logging.info(f"GitHub API 요청 가능 횟수: {remaining} / {limit}")
    else:
        logging.error(f"API 요청 제한 정보를 가져오는데 실패했습니다 (status code: {response.status_code}).")


def retry_request(
    session: requests.Session,
    url: str,
    max_retries: int = 3,
    retry_delay: float = 1,
    params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None
) -> requests.Response:
    """
    주어진 URL에 대해 최대 max_retries 횟수만큼 요청을 재시도합니다.
    """
    response = None
    for i in range(max_retries):
        response = session.get(url, params=params, headers=headers)
        if response.status_code == 200:
            return response
        elif i < max_retries - 1:
            time.sleep(retry_delay)

    return response

