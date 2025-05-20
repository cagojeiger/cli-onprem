"""Tests for the scan command."""

from pathlib import Path

from typer.testing import CliRunner

from cli_onprem.__main__ import app

runner = CliRunner()


def test_scan_directory_command() -> None:
    """Test the scan directory command with a valid path."""
    with runner.isolated_filesystem():
        Path("test_dir").mkdir()
        Path("test_dir/file1.txt").touch()
        Path("test_dir/file2.txt").touch()
        Path("test_dir/subdir").mkdir()
        Path("test_dir/subdir/file3.txt").touch()

        result = runner.invoke(app, ["scan", "directory", "test_dir"])
        assert result.exit_code == 0
        assert "Scan Report" in result.stdout
        assert "Files" in result.stdout
        assert "Directories" in result.stdout


def test_scan_directory_nonexistent_path() -> None:
    """Test the scan directory command with a nonexistent path."""
    result = runner.invoke(app, ["scan", "directory", "nonexistent_dir"])
    assert result.exit_code == 1
    assert "Error: Path nonexistent_dir does not exist" in result.stdout


def test_scan_directory_file_path() -> None:
    """Test the scan directory command with a file path instead of a directory."""
    with runner.isolated_filesystem():
        Path("test_file.txt").touch()
        result = runner.invoke(app, ["scan", "directory", "test_file.txt"])
        assert result.exit_code == 1
        assert "Error: test_file.txt is not a directory" in result.stdout
