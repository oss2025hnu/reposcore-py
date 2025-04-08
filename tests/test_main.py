import subprocess
import sys
import os

def test_main_help_runs():
    """--help 옵션이 정상 작동하는지 확인"""
    result = subprocess.run(
        [sys.executable, "-m", "reposcore", "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "도움말 표시 후 종료" in result.stdout

def test_main_repo_runs():
    """--repo 옵션이 최소한 실행되고 종료되지 않는지 확인"""
    result = subprocess.run(
        [sys.executable, "-m", "reposcore", "--repo", "oss2025hnu/reposcore-py"],
        capture_output=True,
        text=True
    )
    # 비정상적인 종료 (예: AttributeError) 가 없어야 함
    assert result.returncode == 0
    assert "저장소 분석 시작" in result.stdout or "Participation Scores Table" in result.stdout

def test_main_without_repo_option():
    """--repo 옵션 없이 실행했을 때 에러 출력 확인"""
    result = subprocess.run(
        [sys.executable, "-m", "reposcore"],
        capture_output=True,
        text=True
    )
    assert result.returncode != 0
    assert "repo 옵션은 'owner/repo' 형식으로 입력해야 함" in result.stdout or "required" in result.stderr

def test_main_invalid_repo_format():
    """잘못된 형식의 --repo 인자에 대한 처리"""
    result = subprocess.run(
        [sys.executable, "-m", "reposcore", "--repo", "invalid_repo_format"],
        capture_output=True,
        text=True
    )
    assert result.returncode != 0
    assert "repo 옵션은 'owner/repo' 형식으로 입력해야 함" in result.stdout

def test_main_nonexistent_repo():
    """존재하지 않는 저장소 입력시 경고 메시지 확인"""
    result = subprocess.run(
        [sys.executable, "-m", "reposcore", "--repo", "this/doesnotexist123"],
        capture_output=True,
        text=True
    )
    assert "가 깃허브에 존재하지 않을 수 있음" in result.stdout
