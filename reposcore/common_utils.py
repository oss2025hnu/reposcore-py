import sys
import logging

from datetime import datetime

is_verbose = False

# logging 모듈 기본 설정 (analyzer.py와 동일한 설정)
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 등수를 영어 서수로 변환하는 함수
def get_ordinal_suffix(rank):
    if 11 <= rank <= 13:
        return f"{rank}th"
    elif rank == 1 or (rank >= 21 and rank % 10 == 1):
        return f"{rank}st"
    elif rank == 2 or (rank >= 22 and rank % 10 == 2):
        return f"{rank}nd"
    elif rank == 3 or (rank >= 23 and rank % 10 == 3):
        return f"{rank}rd"
    else:
        return f"{rank}th"

# -v or --vebose 옵션에 따라 로그를 다르게 출력하는 함수
def log(message: str, force: bool = False):
    if is_verbose or force:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")