import sys
import logging

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