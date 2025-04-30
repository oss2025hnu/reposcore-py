# 디버깅 및 로깅 가이드

이 가이드는 프로젝트에 처음 참여하는 개발자와 기존 기여자들이 문제 발생 시 로그를 효과적으로 분석하고 디버깅하는 데 큰 도움을 주기 위해 작성되었습니다.

---

## 1. 기본 로깅 설정 방법과 예시

Python의 `logging` 모듈을 통해 간단한 설정으로 로그를 남길 수 있습니다.

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.info("로깅이 설정되었습니다.")
```

- **level**: 출력할 로그의 최소 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **format**: 로그 메시지 포맷 (시간, 모듈명, 로그레벨, 메시지 등 포함)

---

## 2. 디버깅 모드 활성화 방법

### (1) 코드 내에서 직접 설정
```python
logging.basicConfig(level=logging.DEBUG)
```

### (2) 환경 변수로 로그 레벨 설정
환경 변수 예시: `LOG_LEVEL=DEBUG`

```python
import os

log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(level=getattr(logging, log_level, logging.INFO))
```

---

## 3. 오류 발생 시 로그를 통한 문제 추적 및 해결 방법

예외 상황을 감지하여 traceback까지 함께 출력하려면 `logger.exception()`을 사용합니다.

```python
try:
    risky_function()
except Exception as e:
    logger.exception("에러 발생: %s", e)
```

- `.exception()`은 DEBUG 또는 INFO 수준보다 높은 레벨에서도 traceback을 출력합니다.
- 발생 위치, 예외 메시지, 호출 스택까지 로그로 남겨 문제를 빠르게 파악할 수 있습니다.

---

## 4. 일반적인 디버깅 팁 및 주의사항

- print 대신 logging 사용 (출력 제어 및 로그 기록 가능)
- 로그 레벨을 조절하여 필요한 정보만 확인
- 조건부로 특정 모듈 또는 기능의 로그만 남기도록 설정
- logger 이름은 `__name__`으로 지정해 모듈별 로깅 가능하게 구성
- 디버깅 시 trace level 로그까지 보고 싶다면 `setLevel(logging.DEBUG)` 적극 활용
- 협업 시 로그 포맷 및 로그 레벨 정책을 문서화하여 공유

---

## 5. 예제 코드와 함께 알아두면 좋은 팁

```python
import logging
import os

def setup_logger():
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format='%(asctime)s | %(levelname)s | %(message)s'
    )
    return logging.getLogger("project_logger")

logger = setup_logger()

def divide(x, y):
    try:
        result = x / y
        logger.debug(f"{x} / {y} = {result}")
        return result
    except ZeroDivisionError:
        logger.exception("0으로 나누려 했습니다.")
        return None

divide(10, 0)
```

---

이 문서는 신규 개발자들이 문제를 쉽게 파악하고 효과적으로 디버깅할 수 있도록 도와주며, 전체적인 코드 유지보수성과 협업 효율을 높이는 데 기여할 수 있습니다.
