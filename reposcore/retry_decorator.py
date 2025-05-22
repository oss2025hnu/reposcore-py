# reposcore/retry_decorator.py
import time
import logging
from functools import wraps
from urllib.error import URLError

logger = logging.getLogger(__name__)

def retry(max_retries: int = 3, retry_delay: float = 5):
    """
    Connection reset by peer 오류 발생 시 자동으로 재시도하는 데코레이터.
    Args:
        max_retries: 최대 재시도 횟수 (기본:3)
        retry_delay: 재시도 간 대기 시간(초, 기본:5)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except URLError as e:
                    is_reset = isinstance(e.reason, ConnectionResetError) \
                        or "[Errno 104] Connection reset by peer" in str(e)
                    if retries < max_retries and is_reset:
                        retries += 1
                        logger.warning(f"[{retries}/{max_retries}] {func.__name__}에서 Connection reset by peer, {retry_delay}s 후 재시도")
                        time.sleep(retry_delay)
                        continue
                    raise
                except Exception:
                    raise
        return wrapper
    return decorator

@retry(max_retries=3, retry_delay=2)
def retry_request(session, url, params=None, headers=None):
    response = session.get(url, params=params, headers=headers)
    response.raise_for_status()
    return response