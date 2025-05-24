"""Tests for the refactored docker-tar command."""

import subprocess
from unittest import mock

import pytest
from typer.testing import CliRunner

from cli_onprem.__main__ import app
from cli_onprem.commands.docker_tar import pull_image


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def mock_run_command(mocker):
    """Mock the run_command function."""
    return mocker.patch("cli_onprem.commands.docker_tar.run_command")


@pytest.fixture  
def mock_console(mocker):
    """Mock the console."""
    return mocker.Mock()


def test_pull_image_success(mock_run_command, mock_console):
    """Test successful image pull on first attempt."""
    mock_run_command.return_value = None  # No exception means success
    
    success, error = pull_image("test:image", quiet=True)
    
    assert success is True
    assert error == ""
    mock_run_command.assert_called_once()


def test_pull_image_retry_success(mock_run_command, mock_console):
    """Test successful image pull after retry."""
    # First call raises exception (timeout), second succeeds
    mock_run_command.side_effect = [
        Exception("timeout while connecting to docker hub"),
        None  # Success on retry
    ]
    
    with mock.patch("time.sleep"):  # Mock sleep to speed up test
        success, error = pull_image("test:image", quiet=True)
    
    assert success is True
    assert error == ""
    assert mock_run_command.call_count == 2


def test_pull_image_retry_fail(mock_run_command, mock_console):
    """Test image pull failure after all retries."""
    # All attempts fail with timeout
    mock_run_command.side_effect = [
        Exception("timeout while connecting to docker hub")
    ] * 4  # max_retries(3) + first attempt(1) = 4
    
    with mock.patch("time.sleep"):  # Mock sleep to speed up test
        success, error = pull_image("test:image", quiet=True)
    
    assert success is False
    assert "timeout" in error.lower()
    assert mock_run_command.call_count == 4


def test_pull_image_with_arch(mock_run_command, mock_console):
    """Test image pull with architecture parameter."""
    mock_run_command.return_value = None  # Success
    
    success, error = pull_image("test:image", quiet=True, arch="linux/arm64")
    
    assert success is True
    assert error == ""
    
    # Verify the command was called with correct architecture
    args = mock_run_command.call_args[0][0]
    assert "linux/arm64" in args


def test_docker_tar_save_integration(runner):
    """Integration test for docker-tar save command."""
    with mock.patch("cli_onprem.commands.docker_tar.check_cli_tool"):
        with mock.patch("cli_onprem.commands.docker_tar.pull_image") as mock_pull:
            mock_pull.return_value = (True, "")
            
            with mock.patch("cli_onprem.commands.docker_tar.run_docker_command") as mock_docker:
                mock_docker.return_value = (True, "")
                
                result = runner.invoke(
                    app,
                    ["docker-tar", "save", "alpine:latest", "--dry-run"]
                )
                
                assert result.exit_code == 0


def test_save_invalid_arch(runner):
    """Test save command with invalid architecture."""
    result = runner.invoke(
        app,
        ["docker-tar", "save", "alpine:latest", "--arch", "invalid/arch"]
    )
    
    assert result.exit_code != 0
    assert "linux/amd64 또는 linux/arm64만 지원합니다" in result.stdout