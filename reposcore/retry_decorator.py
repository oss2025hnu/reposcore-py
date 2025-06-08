# reposcore/retry_decorator.py

import time
import logging
from functools import wraps
import urllib.error
import requests

logger = logging.getLogger(__name__)

def retry(
    max_retries: int = 3,
    retry_delay: float = 5,
    exceptions: tuple = (
        requests.exceptions.RequestException,
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
        requests.exceptions.HTTPError,
        urllib.error.URLError,
    )
):
    """
    다양한 네트워크 오류 발생 시 자동으로 재시도하는 데코레이터.

    Args:
        max_retries: 최대 재시도 횟수 (기본:3)
        retry_delay: 재시도 간 대기 시간(초, 기본:5)
        exceptions: 재시도할 예외 타입 튜플 (기본: requests 관련 주요 예외)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if retries < max_retries:
                        retries += 1
                        logger.warning(
                            f"[{retries}/{max_retries}] {func.__name__}에서 예외 발생: {e}. {retry_delay}s 후 재시도"
                        )
                        time.sleep(retry_delay)
                        continue
                    logger.error(
                        f"{func.__name__}에서 {max_retries}회 재시도 후에도 실패: {e}"
                    )
                    raise
        return wrapper
    return decorator

# 예시: 실제 요청 함수에 적용
@retry(max_retries=3, retry_delay=2)
def retry_request(session, url, params=None, headers=None):
    """
    requests.Session을 이용한 GET 요청을 재시도하며 수행
    """
    response = session.get(url, params=params, headers=headers)
    response.raise_for_status()  # 4xx, 5xx 발생 시 HTTPError 발생
    return response
