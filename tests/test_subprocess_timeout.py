"""Subprocess 타임아웃 기능 테스트."""

import os
import subprocess
from unittest import mock

import pytest

from cli_onprem.core.errors import CommandError
from cli_onprem.utils import shell


def test_default_timeout_value():
    """DEFAULT_TIMEOUT이 300초(5분)로 설정되어 있는지 확인."""
    # 환경 변수가 없으면 기본값 사용
    with mock.patch.dict(os.environ, {}, clear=True):
        # 모듈 리로드하여 환경 변수 반영
        import importlib

        importlib.reload(shell)
        assert shell.DEFAULT_TIMEOUT == 300


def test_long_timeout_value():
    """LONG_TIMEOUT이 1800초(30분)로 설정되어 있는지 확인."""
    with mock.patch.dict(os.environ, {}, clear=True):
        import importlib

        importlib.reload(shell)
        assert shell.LONG_TIMEOUT == 1800


def test_very_long_timeout_value():
    """VERY_LONG_TIMEOUT이 3600초(60분)로 설정되어 있는지 확인."""
    with mock.patch.dict(os.environ, {}, clear=True):
        import importlib

        importlib.reload(shell)
        assert shell.VERY_LONG_TIMEOUT == 3600


def test_timeout_env_var_override():
    """환경 변수로 타임아웃을 재정의할 수 있는지 확인."""
    with mock.patch.dict(os.environ, {"CLI_ONPREM_TIMEOUT": "600"}):
        import importlib

        importlib.reload(shell)
        assert shell.DEFAULT_TIMEOUT == 600


def test_long_timeout_env_var_override():
    """환경 변수로 LONG_TIMEOUT을 재정의할 수 있는지 확인."""
    with mock.patch.dict(os.environ, {"CLI_ONPREM_LONG_TIMEOUT": "7200"}):
        import importlib

        importlib.reload(shell)
        assert shell.LONG_TIMEOUT == 7200


def test_run_command_with_default_timeout():
    """run_command가 기본 타임아웃을 사용하는지 확인."""
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.MagicMock(returncode=0, stdout="", stderr="")

        shell.run_command(["echo", "test"])

        # subprocess.run이 timeout 파라미터와 함께 호출되었는지 확인
        assert mock_run.called
        call_kwargs = mock_run.call_args[1]
        assert "timeout" in call_kwargs
        # 기본값이 전달되었는지 확인 (환경 변수에 따라 달라질 수 있음)
        assert call_kwargs["timeout"] > 0


def test_run_command_with_custom_timeout():
    """run_command에 커스텀 타임아웃을 지정할 수 있는지 확인."""
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.MagicMock(returncode=0, stdout="", stderr="")

        shell.run_command(["echo", "test"], timeout=1800)

        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["timeout"] == 1800


def test_run_command_with_none_timeout():
    """timeout=None으로 무제한 대기가 가능한지 확인."""
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.MagicMock(returncode=0, stdout="", stderr="")

        shell.run_command(["echo", "test"], timeout=None)

        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["timeout"] is None


def test_timeout_expired_raises_command_error():
    """타임아웃 발생 시 CommandError로 변환되는지 확인."""
    with mock.patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["sleep", "10"], timeout=1)

        with pytest.raises(CommandError, match="타임아웃"):
            shell.run_command(["sleep", "10"], timeout=1)


def test_timeout_error_message_includes_hint():
    """타임아웃 에러 메시지에 해결 방법 힌트가 포함되는지 확인."""
    with mock.patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["sleep", "10"], timeout=1)

        with pytest.raises(CommandError, match="CLI_ONPREM_LONG_TIMEOUT"):
            shell.run_command(["sleep", "10"], timeout=1)


def test_timeout_error_message_truncates_long_commands():
    """긴 명령어가 에러 메시지에서 잘리는지 확인."""
    long_cmd = ["command", "arg1", "arg2", "arg3", "arg4", "arg5"]

    with mock.patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=long_cmd, timeout=1)

        with pytest.raises(CommandError) as exc_info:
            shell.run_command(long_cmd, timeout=1)

        # 에러 메시지에 "..."가 포함되어 있는지 확인 (명령어가 잘렸다는 표시)
        assert "..." in str(exc_info.value)


def test_other_exceptions_not_caught():
    """타임아웃 외의 예외는 그대로 전파되는지 확인."""
    with mock.patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd=["false"], stderr="command failed"
        )

        with pytest.raises(subprocess.CalledProcessError):
            shell.run_command(["false"])


def test_check_command_exists_not_affected():
    """check_command_exists 함수는 영향받지 않는지 확인."""
    # 이 함수는 타임아웃 관련 수정과 무관해야 함
    result = shell.check_command_exists("echo")
    assert isinstance(result, bool)
