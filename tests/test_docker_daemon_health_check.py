"""Docker daemon health check 테스트."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from cli_onprem.core.errors import DependencyError
from cli_onprem.services.docker import check_docker_daemon


def test_check_docker_daemon_success():
    """Docker daemon이 정상 작동할 때."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)

        # 예외 발생하지 않아야 함
        check_docker_daemon()

        # docker info 명령이 호출되었는지 확인
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args == ["docker", "info"]


def test_check_docker_daemon_not_running():
    """Docker daemon이 실행되지 않았을 때."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["docker", "info"],
            stderr="Cannot connect to the Docker daemon",
        )

        with pytest.raises(DependencyError) as exc_info:
            check_docker_daemon()

        assert "실행되지 않았습니다" in str(exc_info.value)
        assert "Docker Desktop을 시작하세요" in str(exc_info.value)


def test_check_docker_daemon_timeout():
    """Docker daemon이 응답하지 않을 때."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd=["docker", "info"],
            timeout=30,
        )

        with pytest.raises(DependencyError) as exc_info:
            check_docker_daemon()

        assert "응답하지 않습니다" in str(exc_info.value)
        assert "재시작하세요" in str(exc_info.value)


def test_check_docker_daemon_cli_not_installed():
    """Docker CLI가 설치되지 않았을 때."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError()

        with pytest.raises(DependencyError) as exc_info:
            check_docker_daemon()

        assert "설치되어 있지 않습니다" in str(exc_info.value)
        assert "https://docs.docker.com" in str(exc_info.value)


def test_check_docker_daemon_uses_quick_timeout():
    """QUICK_TIMEOUT을 사용하는지 확인."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)

        check_docker_daemon()

        # timeout 파라미터가 전달되었는지 확인
        call_kwargs = mock_run.call_args[1]
        assert "timeout" in call_kwargs
        # QUICK_TIMEOUT은 30초
        assert call_kwargs["timeout"] == 30
