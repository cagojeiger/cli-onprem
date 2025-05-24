"""로깅 설정 함수."""

import logging
import sys

# 로거 설정
logger = logging.getLogger("cli-onprem")


def set_log_level(level: str) -> None:
    """로그 레벨을 설정합니다.

    Args:
        level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR)
    """
    logging.getLogger().setLevel(getattr(logging, level))


def get_logger(name: str) -> logging.Logger:
    """모듈별 로거를 반환합니다.

    Args:
        name: 모듈 이름

    Returns:
        설정된 로거
    """
    return logging.getLogger(f"cli-onprem.{name}")


def init_logging(level: str = "INFO") -> None:
    """로깅 시스템을 초기화합니다.

    Args:
        level: 기본 로그 레벨
    """
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stderr,
    )
