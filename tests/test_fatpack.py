"""Tests for the fatpack command."""

import subprocess
import tempfile
from pathlib import Path
from unittest import mock

from typer.testing import CliRunner

from cli_onprem.__main__ import app
from cli_onprem.commands.fatpack import (
    generate_restore_script,
    get_file_size_mb,
    run_command,
)

runner = CliRunner()


def test_run_command_success() -> None:
    """Test successful command execution."""
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.MagicMock(returncode=0)
        result = run_command(["echo", "test"])
        assert result is True
        mock_run.assert_called_once_with(["echo", "test"], check=True, cwd=None)


def test_run_command_failure() -> None:
    """Test command execution failure."""
    with mock.patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, ["bad", "command"])
        result = run_command(["bad", "command"])
        assert result is False
        mock_run.assert_called_once_with(["bad", "command"], check=True, cwd=None)


def test_get_file_size_mb() -> None:
    """Test getting file size in MB."""
    with mock.patch("subprocess.check_output") as mock_output:
        mock_output.return_value = "42\t/path/to/file\n"
        size = get_file_size_mb("/path/to/file")
        assert size == 42
        mock_output.assert_called_once_with(["du", "-m", "/path/to/file"], text=True)


def test_generate_restore_script() -> None:
    """Test generating restore script."""
    script = generate_restore_script()
    assert "#!/usr/bin/env sh" in script
    assert "sha256sum -c manifest.sha256" in script
    assert "cat parts/* > archive.tar.gz" in script
    assert "tar --no-same-owner -xzvf" in script


def test_generate_restore_script_with_purge() -> None:
    """Test generating restore script with purge option."""
    script = generate_restore_script(purge=True)
    assert "#!/usr/bin/env sh" in script
    assert 'rm -rf "$PACK_DIR"' in script
    assert '[ "${1:-}" = "--purge" ] && PURGE=1' in script


def test_pack_command() -> None:
    """Test the pack command."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        test_file = tmp_path / "testfile"
        test_file.write_text("test content")

        with mock.patch("cli_onprem.commands.fatpack.run_command") as mock_run:
            mock_run.return_value = True

            with mock.patch("os.path.exists") as mock_exists:
                mock_exists.return_value = False

                with mock.patch("os.makedirs"):
                    with mock.patch("builtins.open", mock.mock_open()):
                        with mock.patch("os.chmod"):
                            with mock.patch("glob.glob") as mock_glob:
                                mock_glob.return_value = [
                                    "testfile.pack/parts/0000.part"
                                ]

                                with mock.patch("os.rename"):
                                    with mock.patch("os.remove"):
                                        with mock.patch(
                                            "cli_onprem.commands.fatpack.get_file_size_mb"
                                        ) as mock_size:
                                            mock_size.return_value = 10

                                            result = runner.invoke(
                                                app,
                                                ["fatpack", "pack", str(test_file)],
                                            )

                                            assert result.exit_code == 0


def test_pack_command_directory() -> None:
    """Test the pack command with directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()

        with mock.patch("cli_onprem.commands.fatpack.run_command") as mock_run:
            mock_run.return_value = True

            with mock.patch("os.path.exists") as mock_exists:
                mock_exists.return_value = False

                with mock.patch("pathlib.Path.is_dir") as mock_is_dir:
                    mock_is_dir.return_value = True

                    with mock.patch("os.makedirs"):
                        with mock.patch("builtins.open", mock.mock_open()):
                            with mock.patch("os.chmod"):
                                with mock.patch("glob.glob") as mock_glob:
                                    mock_glob.return_value = [
                                        "testdir.pack/parts/0000.part"
                                    ]

                                    with mock.patch("os.rename"):
                                        with mock.patch("os.remove"):
                                            with mock.patch(
                                                "cli_onprem.commands.fatpack.get_file_size_mb"
                                            ) as mock_size:
                                                mock_size.return_value = 10

                                                result = runner.invoke(
                                                    app,
                                                    ["fatpack", "pack", str(test_dir)],
                                                )

                                                assert result.exit_code == 0


def test_restore_command() -> None:
    """Test the restore command."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        pack_dir = tmp_path / "testdir.pack"
        pack_dir.mkdir()
        restore_script = pack_dir / "restore.sh"
        restore_script.write_text("#!/bin/sh\necho test")

        with mock.patch("cli_onprem.commands.fatpack.run_command") as mock_run:
            mock_run.return_value = True

            result = runner.invoke(app, ["fatpack", "restore", str(pack_dir)])

            assert result.exit_code == 0
            mock_run.assert_called_once_with(["./restore.sh"], cwd=str(pack_dir))


def test_restore_command_with_purge() -> None:
    """Test the restore command with purge option."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        pack_dir = tmp_path / "testdir.pack"
        pack_dir.mkdir()
        restore_script = pack_dir / "restore.sh"
        restore_script.write_text("#!/bin/sh\necho test")

        with mock.patch("cli_onprem.commands.fatpack.run_command") as mock_run:
            mock_run.return_value = True

            result = runner.invoke(
                app, ["fatpack", "restore", str(pack_dir), "--purge"]
            )

            assert result.exit_code == 0
            mock_run.assert_called_once_with(
                ["./restore.sh", "--purge"], cwd=str(pack_dir)
            )


def test_restore_command_invalid_directory() -> None:
    """Test the restore command with invalid directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        non_existent_dir = tmp_path / "nonexistent"

        result = runner.invoke(app, ["fatpack", "restore", str(non_existent_dir)])

        assert result.exit_code == 1
        assert "존재하지 않거나" in result.stdout


def test_restore_command_missing_script() -> None:
    """Test the restore command with missing restore script."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        empty_dir = tmp_path / "empty_dir"
        empty_dir.mkdir()

        result = runner.invoke(app, ["fatpack", "restore", str(empty_dir)])

        assert result.exit_code == 1
        assert "restore.sh가 없습니다" in result.stdout
