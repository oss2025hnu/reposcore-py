import re
import requests

def validate_repo_format(repo: str) -> bool:
    """
    저장소 이름이 'owner/repo' 형식인지 확인합니다.

    Args:
        repo (str): 검사할 GitHub 저장소 이름입니다. 예: 'octocat/Hello-World'

    Returns:
        bool: 형식이 올바르면 True, 그렇지 않으면 False를 반환합니다.
              형식이 잘못된 경우 경고 메시지를 출력합니다.
    """    
    pattern = r'^[\w\-]+/[\w\-]+$'
    if re.fullmatch(pattern, repo):
        return True
    else:
        print("저장소 형식이 올바르지 않습니다. 'owner/repo' 형식으로 입력해주세요.")
        return False

def check_github_repo_exists(repo: str) -> bool:
    """
    GitHub API를 통해 해당 저장소가 실제로 존재하는지 확인합니다.

    Args:
        repo (str): 확인할 GitHub 저장소 이름입니다. 예: 'octocat/Hello-World'

    Returns:
        bool: 저장소가 존재하면 True, 존재하지 않거나 오류가 발생하면 False를 반환합니다.
              오류 또는 404 응답 시 관련 메시지를 출력합니다.
    """    
    url = f"https://api.github.com/repos/{repo}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return True
        else:
            print(f"GitHub 저장소 '{repo}'를 찾을 수 없습니다. (응답 코드: {response.status_code})")
            return False
    except requests.exceptions.RequestException as e:
        print(f"GitHub API 요청 중 오류가 발생했습니다: {e}")
        return False
