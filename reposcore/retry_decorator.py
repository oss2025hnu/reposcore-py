# reposcore/retry_decorator.py

import time
import logging
from functools import wraps
from urllib.error import URLError

logger = logging.getLogger(__name__)

def retry(max_retries: int = 3, retry_delay: float = 1.0):
    """
    네트워크 오류 시 자동 재시도 데코레이터.
    - max_retries: 최대 재시도 횟수
    - retry_delay: 재시도 전 대기 시간(초)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except URLError as e:
                    attempts += 1
                    if attempts <= max_retries and (
                        isinstance(e.reason, ConnectionResetError)
                        or "Connection reset by peer" in str(e)
                    ):
                        logger.warning(
                            f"[retry {attempts}/{max_retries}] "
                            f"{func.__name__} 실패: {e}. {retry_delay}s 후 재시도."
                        )
                        time.sleep(retry_delay)
                        continue
                    raise
        return wrapper
    return decorator
