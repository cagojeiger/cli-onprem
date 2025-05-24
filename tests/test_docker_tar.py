"""Tests for the docker-tar command."""

import subprocess
from unittest import mock

from typer.testing import CliRunner

from cli_onprem.__main__ import app
from cli_onprem.commands.docker_tar import pull_image

runner = CliRunner()


def test_pull_image_success() -> None:
    """Test successful image pull on first attempt."""
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=["docker", "pull", "test:image"], returncode=0, stdout=b"", stderr=b""
        )

        success, error = pull_image("test:image", quiet=True)

        assert success is True
        assert error == ""
        mock_run.assert_called_once()


def test_pull_image_retry_success() -> None:
    """Test successful image pull after retry."""
    with mock.patch("subprocess.run") as mock_run:
        mock_run.side_effect = [
            subprocess.CalledProcessError(
                returncode=1,
                cmd=["docker", "pull", "test:image"],
                stderr=b"timeout while connecting to docker hub",
            ),
            subprocess.CompletedProcess(
                args=["docker", "pull", "test:image"],
                returncode=0,
                stdout=b"",
                stderr=b"",
            ),
        ]

        with mock.patch("time.sleep") as mock_sleep:  # time.sleep 무시
            success, error = pull_image("test:image", quiet=True)

        assert success is True
        assert error == ""
        assert mock_run.call_count == 2
        mock_sleep.assert_called_once()


def test_pull_image_retry_fail() -> None:
    """Test image pull failure after all retries."""
    with mock.patch("subprocess.run") as mock_run:
        mock_run.side_effect = [
            subprocess.CalledProcessError(
                returncode=1,
                cmd=["docker", "pull", "test:image"],
                stderr=b"timeout while connecting to docker hub",
            )
        ] * 4  # max_retries(3) + 첫 시도(1) = 4

        with mock.patch("time.sleep") as mock_sleep:  # time.sleep 무시
            success, error = pull_image("test:image", quiet=True)

        assert success is False
        if isinstance(error, bytes):
            error_str = error.decode("utf-8", errors="replace")
        else:
            error_str = str(error)
        assert "timeout" in error_str.lower()
        assert mock_run.call_count == 4
        assert mock_sleep.call_count == 3


def test_docker_tar_save_with_pull_retry() -> None:
    """Test docker-tar save command with image pull retry."""
    with mock.patch("cli_onprem.commands.docker_tar.pull_image") as mock_pull:
        mock_pull.return_value = (True, "")  # 성공적으로 이미지 가져옴

        with mock.patch(
            "cli_onprem.commands.docker_tar.run_docker_command"
        ) as mock_run:
            mock_run.return_value = (True, "")  # 성공적으로 저장

            result = runner.invoke(
                app, ["docker-tar", "save", "test:image"], input="y\n"
            )

            assert result.exit_code == 0
            mock_pull.assert_called_once_with("test:image", False, arch="linux/amd64")
            assert mock_run.call_count >= 1


def test_pull_image_with_arch() -> None:
    """Test image pull with architecture parameter."""
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=["docker", "pull", "--platform", "linux/arm64", "test:image"],
            returncode=0,
            stdout=b"",
            stderr=b"",
        )

        success, error = pull_image("test:image", quiet=True, arch="linux/arm64")

        assert success is True
        assert error == ""
        mock_run.assert_called_once_with(
            ["docker", "pull", "--platform", "linux/arm64", "test:image"],
            check=True,
            stdout=None,
            stderr=subprocess.PIPE,
            text=True,
        )


def test_save_invalid_arch() -> None:
    """Invalid arch option should return an error."""
    result = runner.invoke(
        app,
        ["docker-tar", "save", "nginx", "--arch", "linux/ppc64"],
    )

    assert result.exit_code != 0
    assert "linux/amd64 또는 linux/arm64만 지원합니다." in result.stdout
