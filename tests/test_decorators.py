from .retry_decorator import retry
import pytest
from urllib.error import URLError


class Dummy:
    def __init__(self):
        self.count = 0

    @retry(max_retries=2, retry_delay=0)
    def flaky(self):
        self.count += 1
        if self.count < 2:
            raise URLError(ConnectionResetError())
        return "ok"

def test_retry_decorator_succeeds_on_second_try():
    d = Dummy()
    result = d.flaky()
    assert result == "ok"
    assert d.count == 2

def test_retry_decorator_gives_up_after_max():
    d = Dummy()
    # 최대 2번 시도, 세 번째 호출도 실패하게끔
    @retry(max_retries=1, retry_delay=0)
    def always_fail():
        raise URLError(ConnectionResetError())
    with pytest.raises(URLError):
        always_fail()
