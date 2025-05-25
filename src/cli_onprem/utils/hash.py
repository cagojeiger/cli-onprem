"""해시 계산 관련 유틸리티 함수."""

import hashlib
from pathlib import Path
from typing import Optional

from cli_onprem.core.logging import get_logger

logger = get_logger("utils.hash")


def calculate_file_md5(file_path: Path, chunk_size: int = 8192) -> Optional[str]:
    """파일의 MD5 해시를 계산합니다.

    대용량 파일(5GB 이상)의 경우 None을 반환합니다.

    Args:
        file_path: 파일 경로
        chunk_size: 읽기 청크 크기

    Returns:
        MD5 해시 문자열 또는 None
    """
    # 5GB 이상 파일은 건너뛰기
    if file_path.stat().st_size >= 5 * 1024 * 1024 * 1024:
        logger.debug(f"{file_path} 파일이 너무 커서 MD5 계산 건너뛰기")
        return None

    try:
        md5_hash = hashlib.md5()
        with open(file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                md5_hash.update(chunk)

        result = md5_hash.hexdigest()
        logger.debug(f"{file_path} MD5: {result}")
        return result

    except Exception as e:
        logger.warning(f"{file_path} MD5 계산 실패: {e}")
        return None


def calculate_file_sha256(file_path: Path, chunk_size: int = 8192) -> Optional[str]:
    """파일의 SHA256 해시를 계산합니다.

    Args:
        file_path: 파일 경로
        chunk_size: 읽기 청크 크기

    Returns:
        SHA256 해시 문자열 또는 None
    """
    try:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                sha256_hash.update(chunk)

        result = sha256_hash.hexdigest()
        logger.debug(f"{file_path} SHA256: {result}")
        return result

    except Exception as e:
        logger.warning(f"{file_path} SHA256 계산 실패: {e}")
        return None


def verify_file_md5(file_path: Path, expected_md5: str) -> bool:
    """파일의 MD5 해시를 검증합니다.

    Args:
        file_path: 파일 경로
        expected_md5: 예상 MD5 해시

    Returns:
        검증 성공 여부
    """
    actual_md5 = calculate_file_md5(file_path)
    if actual_md5 is None:
        logger.warning(f"{file_path} MD5 계산 실패로 검증 불가")
        return False

    is_valid = actual_md5 == expected_md5
    if not is_valid:
        logger.warning(
            f"{file_path} MD5 불일치: 예상={expected_md5}, 실제={actual_md5}"
        )

    return is_valid


def verify_file_sha256(file_path: Path, expected_sha256: str) -> bool:
    """파일의 SHA256 해시를 검증합니다.

    Args:
        file_path: 파일 경로
        expected_sha256: 예상 SHA256 해시

    Returns:
        검증 성공 여부
    """
    actual_sha256 = calculate_file_sha256(file_path)
    if actual_sha256 is None:
        logger.warning(f"{file_path} SHA256 계산 실패로 검증 불가")
        return False

    is_valid = actual_sha256 == expected_sha256
    if not is_valid:
        logger.warning(
            f"{file_path} SHA256 불일치: 예상={expected_sha256}, 실제={actual_sha256}"
        )

    return is_valid
