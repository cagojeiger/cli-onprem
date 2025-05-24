"""로깅 설정 함수."""

import logging

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
