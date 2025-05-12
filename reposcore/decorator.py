# reposcore/decorators.py
import time
import logging
from functools import wraps
from urllib.error import URLError

logger = logging.getLogger(__name__)

def retry(max_retries: int = 3, retry_delay: float = 5):
    """
    Connection reset by peer 오류 발생 시 자동으로 재시도하고 logging을 사용하는 데코레이터입니다.

    Args:
        max_retries (int): 최대 재시도 횟수입니다. 기본값은 3입니다.
        retry_delay (float): 재시도 간의 대기 시간(초)입니다. 기본값은 5초입니다.

    Returns:
        callable: 데코레이터 처리된 함수를 반환합니다.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except URLError as e:
                    # Connection reset by peer인 경우만 재시도
                    msg = str(e)
                    if ("Connection reset by peer" in msg) or isinstance(e.reason, ConnectionResetError):
                        retries += 1
                        if retries > max_retries:
                            logger.error(f"{func.__name__} 최대 재시도 횟수({max_retries}) 초과. 연결 실패.")
                            raise
                        logger.warning(f"[{retries}/{max_retries}] {func.__name__} 호출 중 Connection reset by peer 오류 발생. "
                                       f"{retry_delay}초 후 재시도...")
                        time.sleep(retry_delay)
                        continue
                    # 그 외 예외는 그대로 올려 버림
                    raise
                except Exception:
                    # 기타 예외는 로깅 후 재발생
                    logger.exception(f"{func.__name__} 호출 중 오류 발생:")
                    raise
        return wrapper
    return decorator
