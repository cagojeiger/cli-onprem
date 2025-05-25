"""해시 유틸리티 함수 테스트."""

import hashlib
import tempfile
from pathlib import Path
from unittest import mock

from cli_onprem.utils.hash import (
    calculate_file_md5,
    calculate_file_sha256,
    verify_file_md5,
    verify_file_sha256,
)


def test_calculate_file_md5_success() -> None:
    """MD5 해시 계산 성공 테스트."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("test content")
        f.flush()

        file_path = Path(f.name)
        try:
            result = calculate_file_md5(file_path)
            expected = hashlib.md5(b"test content").hexdigest()
            assert result == expected
        finally:
            file_path.unlink()


def test_calculate_file_md5_large_file() -> None:
    """5GB 이상 파일은 None 반환 테스트."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        file_path = Path(f.name)

        # stat을 모킹하여 큰 파일로 가장
        with mock.patch("pathlib.Path.stat") as mock_stat:
            mock_stat.return_value.st_size = 6 * 1024 * 1024 * 1024  # 6GB

            result = calculate_file_md5(file_path)
            assert result is None

        file_path.unlink()


def test_calculate_file_md5_exception() -> None:
    """파일 읽기 실패 시 None 반환 테스트."""
    # stat()을 모킹하여 파일이 존재하는 것처럼 보이게 하고
    # open()에서 예외 발생시키기
    file_path = Path("/nonexistent/file.txt")

    with mock.patch("pathlib.Path.stat") as mock_stat:
        mock_stat.return_value.st_size = 1024  # 작은 파일

        with mock.patch("builtins.open", side_effect=FileNotFoundError()):
            result = calculate_file_md5(file_path)
            assert result is None


def test_calculate_file_sha256_success() -> None:
    """SHA256 해시 계산 성공 테스트."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("test content")
        f.flush()

        file_path = Path(f.name)
        try:
            result = calculate_file_sha256(file_path)
            expected = hashlib.sha256(b"test content").hexdigest()
            assert result == expected
        finally:
            file_path.unlink()


def test_calculate_file_sha256_exception() -> None:
    """파일 읽기 실패 시 None 반환 테스트."""
    # 존재하지 않는 파일
    file_path = Path("/nonexistent/file.txt")
    result = calculate_file_sha256(file_path)
    assert result is None


def test_verify_file_md5_success() -> None:
    """MD5 해시 검증 성공 테스트."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("test content")
        f.flush()

        file_path = Path(f.name)
        try:
            expected = hashlib.md5(b"test content").hexdigest()
            result = verify_file_md5(file_path, expected)
            assert result is True
        finally:
            file_path.unlink()


def test_verify_file_md5_failure() -> None:
    """MD5 해시 검증 실패 테스트."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("test content")
        f.flush()

        file_path = Path(f.name)
        try:
            wrong_hash = "wronghash123"
            result = verify_file_md5(file_path, wrong_hash)
            assert result is False
        finally:
            file_path.unlink()


def test_verify_file_md5_large_file() -> None:
    """큰 파일에 대한 MD5 검증 테스트."""
    file_path = Path("large_file.txt")

    # 큰 파일로 모킹
    with mock.patch("cli_onprem.utils.hash.calculate_file_md5") as mock_calc:
        mock_calc.return_value = None  # 큰 파일은 None 반환

        result = verify_file_md5(file_path, "anyhash")
        assert result is False


def test_verify_file_sha256_success() -> None:
    """SHA256 해시 검증 성공 테스트."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("test content")
        f.flush()

        file_path = Path(f.name)
        try:
            expected = hashlib.sha256(b"test content").hexdigest()
            result = verify_file_sha256(file_path, expected)
            assert result is True
        finally:
            file_path.unlink()


def test_verify_file_sha256_failure() -> None:
    """SHA256 해시 검증 실패 테스트."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("test content")
        f.flush()

        file_path = Path(f.name)
        try:
            wrong_hash = "wronghash123"
            result = verify_file_sha256(file_path, wrong_hash)
            assert result is False
        finally:
            file_path.unlink()
