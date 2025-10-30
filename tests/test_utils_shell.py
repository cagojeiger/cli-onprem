"""Tests for utils/shell.py - shell command execution utilities."""

import os
import subprocess
from unittest.mock import patch

import pytest

from cli_onprem.core.errors import CommandError
from cli_onprem.utils.shell import (
    DEFAULT_TIMEOUT,
    LONG_TIMEOUT,
    MEDIUM_TIMEOUT,
    QUICK_TIMEOUT,
    VERY_LONG_TIMEOUT,
    check_command_exists,
    run_command,
)


def test_timeout_constants_default_values():
    """Test that timeout constants have expected default values."""
    # These values should match the defaults in shell.py
    assert QUICK_TIMEOUT == int(os.getenv("CLI_ONPREM_QUICK_TIMEOUT", "30"))
    assert DEFAULT_TIMEOUT == int(os.getenv("CLI_ONPREM_TIMEOUT", "300"))
    assert MEDIUM_TIMEOUT == int(os.getenv("CLI_ONPREM_MEDIUM_TIMEOUT", "600"))
    assert LONG_TIMEOUT == int(os.getenv("CLI_ONPREM_LONG_TIMEOUT", "1800"))
    assert VERY_LONG_TIMEOUT == int(
        os.getenv("CLI_ONPREM_VERY_LONG_TIMEOUT", "3600")
    )


def test_run_command_success():
    """Test successful command execution."""
    result = run_command(["echo", "test"], capture_output=True)

    assert result.returncode == 0
    assert "test" in result.stdout


def test_run_command_with_capture_output():
    """Test command execution with output capture."""
    result = run_command(["echo", "hello world"], capture_output=True)

    assert result.returncode == 0
    assert result.stdout.strip() == "hello world"


def test_run_command_with_custom_timeout():
    """Test command execution with custom timeout."""
    # 빠른 명령은 짧은 타임아웃에도 성공
    result = run_command(["echo", "test"], capture_output=True, timeout=1)

    assert result.returncode == 0


def test_run_command_timeout_expired():
    """Test that timeout raises CommandError with helpful message."""
    with pytest.raises(CommandError) as exc_info:
        # sleep 명령으로 타임아웃 발생
        run_command(["sleep", "10"], timeout=1)

    error_msg = str(exc_info.value)
    assert "타임아웃" in error_msg
    assert "1초" in error_msg or "1초 후" in error_msg
    assert "CLI_ONPREM_LONG_TIMEOUT" in error_msg


def test_run_command_timeout_none():
    """Test command execution with no timeout (None)."""
    result = run_command(["echo", "no timeout"], capture_output=True, timeout=None)

    assert result.returncode == 0


def test_run_command_check_false_on_error():
    """Test that check=False doesn't raise exception on command failure."""
    # 존재하지 않는 명령어 실행 (실패 예상)
    result = run_command(
        ["false"], check=False, capture_output=True, timeout=5  # 항상 실패하는 명령
    )

    assert result.returncode != 0
    # 예외가 발생하지 않아야 함


def test_run_command_check_true_on_error():
    """Test that check=True raises CalledProcessError on command failure."""
    with pytest.raises(subprocess.CalledProcessError):
        run_command(["false"], check=True, timeout=5)  # 항상 실패하는 명령


def test_run_command_with_env_variables():
    """Test command execution with custom environment variables."""
    result = run_command(
        ["sh", "-c", "echo $TEST_VAR"],
        capture_output=True,
        env={"TEST_VAR": "test_value"},
    )

    assert "test_value" in result.stdout


def test_run_command_with_cwd():
    """Test command execution with custom working directory."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        result = run_command(["pwd"], capture_output=True, cwd=tmpdir)

        assert tmpdir in result.stdout


def test_check_command_exists_for_existing_command():
    """Test that check_command_exists returns True for existing commands."""
    # 'echo'는 모든 시스템에 존재
    assert check_command_exists("echo") is True
    assert check_command_exists("ls") is True


def test_check_command_exists_for_nonexistent_command():
    """Test that check_command_exists returns False for non-existent commands."""
    # 존재하지 않을 것 같은 명령어
    assert check_command_exists("nonexistent_command_xyz") is False


def test_check_command_exists_with_path():
    """Test that check_command_exists works with absolute paths."""
    # /bin/sh는 대부분의 Unix 시스템에 존재
    assert check_command_exists("/bin/sh") is True


@patch("shutil.which")
def test_check_command_exists_uses_shutil_which(mock_which):
    """Test that check_command_exists uses shutil.which internally."""
    mock_which.return_value = "/usr/bin/test"

    result = check_command_exists("test")

    assert result is True
    mock_which.assert_called_once_with("test")


@patch("shutil.which")
def test_check_command_exists_returns_false_when_which_none(mock_which):
    """Test that check_command_exists returns False when which returns None."""
    mock_which.return_value = None

    result = check_command_exists("nonexistent")

    assert result is False
    mock_which.assert_called_once_with("nonexistent")
