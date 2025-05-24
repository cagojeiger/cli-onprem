"""Tests for the docker-tar command."""

import subprocess
from unittest import mock

from typer.testing import CliRunner

from cli_onprem.__main__ import app
from cli_onprem.services.docker import pull_image

runner = CliRunner()


def test_pull_image_success() -> None:
    """Test successful image pull on first attempt."""
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=["docker", "pull", "--platform", "linux/amd64", "test:image"],
            returncode=0,
            stdout="",
            stderr="",
        )

        # pull_image now returns None on success
        pull_image("test:image")

        mock_run.assert_called_once()


def test_pull_image_retry_success() -> None:
    """Test successful image pull after retry."""
    with mock.patch("subprocess.run") as mock_run:
        mock_run.side_effect = [
            subprocess.CalledProcessError(
                returncode=1,
                cmd=["docker", "pull", "--platform", "linux/amd64", "test:image"],
                stderr="timeout while connecting to docker hub",
            ),
            subprocess.CompletedProcess(
                args=["docker", "pull", "--platform", "linux/amd64", "test:image"],
                returncode=0,
                stdout="",
                stderr="",
            ),
        ]

        with mock.patch("time.sleep") as mock_sleep:  # time.sleep 무시
            # pull_image now returns None on success
            pull_image("test:image")

        assert mock_run.call_count == 2
        mock_sleep.assert_called_once()


def test_pull_image_retry_fail() -> None:
    """Test image pull failure after all retries."""
    from cli_onprem.core.errors import CommandError

    with mock.patch("subprocess.run") as mock_run:
        mock_run.side_effect = [
            subprocess.CalledProcessError(
                returncode=1,
                cmd=["docker", "pull", "--platform", "linux/amd64", "test:image"],
                stderr="timeout while connecting to docker hub",
            )
        ] * 4  # max_retries(3) + 첫 시도(1) = 4

        with mock.patch("time.sleep") as mock_sleep:  # time.sleep 무시
            try:
                pull_image("test:image")
                raise AssertionError("Expected CommandError")
            except CommandError as e:
                assert "timeout" in str(e).lower()

        assert mock_run.call_count == 4
        assert mock_sleep.call_count == 3


def test_docker_tar_save_with_pull_retry() -> None:
    """Test docker-tar save command with image pull retry."""
    # Mock subprocess to prevent real Docker calls
    with mock.patch("subprocess.run") as mock_subprocess:
        mock_subprocess.return_value = mock.Mock(returncode=0, stdout="", stderr="")

        with mock.patch(
            "cli_onprem.utils.shell.check_command_exists"
        ) as mock_check_cmd:
            mock_check_cmd.return_value = True  # Docker가 설치되어 있다고 가정

            result = runner.invoke(
                app, ["docker-tar", "save", "test:image"], input="y\n"
            )

            assert result.exit_code == 0
            # 실제로 Docker pull과 save가 호출되었는지 확인
            assert any("pull" in str(call) for call in mock_subprocess.call_args_list)
            assert any("save" in str(call) for call in mock_subprocess.call_args_list)


def test_pull_image_with_arch() -> None:
    """Test image pull with architecture parameter."""
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=["docker", "pull", "--platform", "linux/arm64", "test:image"],
            returncode=0,
            stdout="",
            stderr="",
        )

        # pull_image now returns None on success
        pull_image("test:image", arch="linux/arm64")

        mock_run.assert_called_once_with(
            ["docker", "pull", "--platform", "linux/arm64", "test:image"],
            check=True,
            capture_output=True,
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
