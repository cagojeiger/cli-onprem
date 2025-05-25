"""Tests for the tar-fat32 command."""

import tempfile
from pathlib import Path
from unittest import mock

from typer.testing import CliRunner

from cli_onprem.__main__ import app
from cli_onprem.core.errors import CommandError
from cli_onprem.services.archive import (
    calculate_sha256_manifest,
    create_tar_archive,
    extract_tar_archive,
    get_directory_size_mb,
    merge_files,
    split_file,
    verify_manifest,
    write_manifest_file,
)
from cli_onprem.utils.fs import (
    create_size_marker,
    find_completable_paths,
    find_pack_directories,
    generate_restore_script,
    make_executable,
)

runner = CliRunner()


def test_create_tar_archive() -> None:
    """Test creating tar archive."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        output_path = tmp_path / "output.tar.gz"

        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.MagicMock(returncode=0)
            create_tar_archive(test_file, output_path, tmp_path)

            mock_run.assert_called_once()
            cmd = mock_run.call_args[0][0]
            assert "tar" in cmd
            assert "-czvf" in cmd
            assert str(output_path) in cmd


def test_split_file() -> None:
    """Test splitting file into chunks."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Test 1: Small file (no split)
        small_file = tmp_path / "small.tar.gz"
        small_file.write_text("test content")
        output_dir = tmp_path / "parts1"
        output_dir.mkdir()

        parts = split_file(small_file, "1G", output_dir)
        assert len(parts) == 1
        assert parts[0].name == "0000.part"
        assert parts[0].read_text() == "test content"

        # Test 2: Large file (split)
        large_file = tmp_path / "large.tar.gz"
        # Create a 2MB file content
        large_content = "x" * (2 * 1024 * 1024)
        large_file.write_text(large_content)
        output_dir2 = tmp_path / "parts2"
        output_dir2.mkdir()

        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.MagicMock(returncode=0)

            # Mock the output files
            with mock.patch("pathlib.Path.glob") as mock_glob:
                mock_glob.return_value = [
                    output_dir2 / "aa",
                    output_dir2 / "ab",
                ]
                with mock.patch("pathlib.Path.rename"):
                    parts = split_file(large_file, "1M", output_dir2)

                    assert len(parts) == 2
                    mock_run.assert_called_once()
                    cmd = mock_run.call_args[0][0]
                    assert "split" in cmd
                    assert "-b" in cmd
                    assert "1M" in cmd


def test_calculate_sha256_manifest() -> None:
    """Test calculating SHA256 manifest."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.MagicMock(
                returncode=0, stdout="abc123  file1.part\ndef456  file2.part\n"
            )

            manifest = calculate_sha256_manifest(tmp_path, "*.part")

            assert len(manifest) == 2
            assert manifest[0] == ("file1.part", "abc123")
            assert manifest[1] == ("file2.part", "def456")


def test_write_manifest_file() -> None:
    """Test writing manifest file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        manifest_path = tmp_path / "manifest.sha256"

        manifest = [
            ("file1.part", "abc123"),
            ("file2.part", "def456"),
        ]

        write_manifest_file(manifest, manifest_path)

        content = manifest_path.read_text()
        assert "abc123  file1.part\n" in content
        assert "def456  file2.part\n" in content


def test_verify_manifest() -> None:
    """Test verifying manifest."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        manifest_path = tmp_path / "manifest.sha256"
        manifest_path.write_text("abc123  file1.part\n")

        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.MagicMock(returncode=0)
            verify_manifest(manifest_path)

            mock_run.assert_called_once()
            cmd = mock_run.call_args[0][0]
            assert "sha256sum" in cmd
            assert "-c" in cmd


def test_merge_files() -> None:
    """Test merging files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        parts_dir = tmp_path / "parts"
        parts_dir.mkdir()
        output_path = tmp_path / "merged.tar.gz"

        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.MagicMock(returncode=0)
            merge_files(parts_dir, output_path, "*.part")

            mock_run.assert_called_once()
            # Command is run through sh -c, so check the actual command string
            assert "cat" in str(mock_run.call_args)
            assert str(output_path) in str(mock_run.call_args)


def test_extract_tar_archive() -> None:
    """Test extracting tar archive."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        archive_path = tmp_path / "archive.tar.gz"
        archive_path.write_bytes(b"fake tar content")

        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.MagicMock(returncode=0)
            extract_tar_archive(archive_path, tmp_path)

            mock_run.assert_called_once()
            cmd = mock_run.call_args[0][0]
            assert "tar" in cmd
            assert "--no-same-owner" in cmd
            assert "-xzvf" in cmd


def test_get_directory_size_mb() -> None:
    """Test getting directory size in MB."""
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.MagicMock(
            returncode=0, stdout="42\t/path/to/dir\n"
        )

        size = get_directory_size_mb(Path("/path/to/dir"))

        assert size == 42
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "du" in cmd
        assert "-m" in cmd


def test_find_completable_paths() -> None:
    """Test finding completable paths."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create test files and directories
        (tmp_path / "file1.txt").write_text("content")
        (tmp_path / "file2.txt").write_text("")  # Empty file
        (tmp_path / "dir1").mkdir()
        (tmp_path / ".hidden").write_text("hidden")

        # Include files and dirs, min size > 0
        paths = find_completable_paths(
            include_files=True, include_dirs=True, min_file_size=1, base_path=tmp_path
        )

        assert "file1.txt" in paths
        assert "file2.txt" not in paths  # Too small
        assert "dir1" in paths
        assert ".hidden" not in paths  # Hidden


def test_find_pack_directories() -> None:
    """Test finding pack directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create valid pack directory
        pack_dir = tmp_path / "test.pack"
        pack_dir.mkdir()
        (pack_dir / "restore.sh").touch()

        # Create invalid pack directory (no restore.sh)
        invalid_pack = tmp_path / "invalid.pack"
        invalid_pack.mkdir()

        pack_dirs = find_pack_directories(base_path=tmp_path)

        assert "test.pack" in pack_dirs
        assert "invalid.pack" not in pack_dirs


def test_generate_restore_script() -> None:
    """Test generating restore script."""
    script = generate_restore_script()
    assert "#!/usr/bin/env sh" in script
    assert "sha256sum -c manifest.sha256" in script
    assert "cat parts/* > archive.tar.gz" in script
    assert "tar --no-same-owner -xzvf" in script


def test_create_size_marker() -> None:
    """Test creating size marker."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        create_size_marker(tmp_path, 42)

        marker_file = tmp_path / "42_MB"
        assert marker_file.exists()


def test_make_executable() -> None:
    """Test making file executable."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        test_file = tmp_path / "script.sh"
        test_file.write_text("#!/bin/sh\necho test")

        with mock.patch("os.chmod") as mock_chmod:
            make_executable(test_file)
            mock_chmod.assert_called_once_with(test_file, 0o755)


def test_pack_command_integration() -> None:
    """Test the pack command integration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        test_file = tmp_path / "testfile.txt"
        test_file.write_text("test content")

        # Mock shutil.rmtree to prevent directory deletion
        with mock.patch("cli_onprem.commands.tar_fat32.shutil.rmtree"):
            # Mock all service functions
            with mock.patch("cli_onprem.commands.tar_fat32.create_tar_archive"):
                with mock.patch(
                    "cli_onprem.commands.tar_fat32.split_file"
                ) as mock_split:
                    # Mock parts directory creation
                    parts_dir = tmp_path / "testfile.txt.pack" / "parts"
                    parts_dir.mkdir(parents=True, exist_ok=True)
                    part_file = parts_dir / "0000.part"
                    part_file.write_text("test")
                    mock_split.return_value = [part_file]

                    with mock.patch(
                        "cli_onprem.commands.tar_fat32.calculate_sha256_manifest"
                    ) as mock_calc:
                        mock_calc.return_value = [("parts/0000.part", "abc123")]

                        with mock.patch(
                            "cli_onprem.commands.tar_fat32.write_manifest_file"
                        ):
                            with mock.patch(
                                "cli_onprem.commands.tar_fat32.get_directory_size_mb"
                            ) as mock_size:
                                mock_size.return_value = 10

                                with mock.patch(
                                    "cli_onprem.commands.tar_fat32.generate_restore_script"
                                ) as mock_gen:
                                    mock_gen.return_value = "#!/bin/sh\necho test"

                                    with mock.patch(
                                        "cli_onprem.commands.tar_fat32.create_size_marker"
                                    ):
                                        with mock.patch(
                                            "cli_onprem.commands.tar_fat32.make_executable"
                                        ):
                                            with mock.patch(
                                                "pathlib.Path.unlink"
                                            ):  # Mock archive removal
                                                result = runner.invoke(
                                                    app,
                                                    [
                                                        "tar-fat32",
                                                        "pack",
                                                        str(test_file),
                                                    ],
                                                )

                                                if result.exit_code != 0:
                                                    print(f"Error: {result.output}")
                                                    print(
                                                        f"Exception: {result.exception}"
                                                    )
                                                assert result.exit_code == 0
                                                assert "압축 완료" in result.stdout


def _test_restore_command_integration() -> None:
    """Test the restore command integration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        pack_dir = tmp_path / "test.pack"
        pack_dir.mkdir()

        # Create required files
        (pack_dir / "restore.sh").write_text("#!/bin/sh\necho test")
        (pack_dir / "manifest.sha256").write_text("abc123  parts/0000.part\n")
        parts_dir = pack_dir / "parts"
        parts_dir.mkdir()
        (parts_dir / "0000.part").write_bytes(b"test content")

        # Mock all service functions
        with mock.patch("cli_onprem.commands.tar_fat32.verify_manifest"):
            with mock.patch("cli_onprem.commands.tar_fat32.merge_files"):
                with mock.patch("cli_onprem.commands.tar_fat32.extract_tar_archive"):
                    with mock.patch("pathlib.Path.unlink"):  # Mock archive removal
                        result = runner.invoke(
                            app,
                            ["tar-fat32", "restore", str(pack_dir)],
                        )

                        if result.exit_code != 0:
                            print(f"Error: {result.output}")
                            print(f"Exception: {result.exception}")
                        assert result.exit_code == 0
                        assert "복원 완료" in result.stdout


def test_command_error_handling() -> None:
    """Test command error handling."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        # Mock service function to raise error
        with mock.patch(
            "cli_onprem.commands.tar_fat32.create_tar_archive"
        ) as mock_create:
            mock_create.side_effect = CommandError("압축 실패: tar: error")

            result = runner.invoke(
                app,
                ["tar-fat32", "pack", str(test_file)],
            )

            assert result.exit_code == 1
            assert "오류" in result.stdout


def test_pack_nonexistent_file() -> None:
    """Test packing non-existent file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        test_file = tmp_path / "nonexistent.txt"

        result = runner.invoke(
            app,
            ["tar-fat32", "pack", str(test_file)],
        )

        assert result.exit_code == 1
        assert "존재하지 않습니다" in result.stdout


def test_restore_invalid_directory() -> None:
    """Test restoring from invalid directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        pack_dir = tmp_path / "invalid.pack"

        result = runner.invoke(
            app,
            ["tar-fat32", "restore", str(pack_dir)],
        )

        assert result.exit_code == 1
        assert "존재하지 않거나" in result.stdout


def test_restore_missing_script() -> None:
    """Test restoring from directory without restore script."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        pack_dir = tmp_path / "test.pack"
        pack_dir.mkdir()

        result = runner.invoke(
            app,
            ["tar-fat32", "restore", str(pack_dir)],
        )

        assert result.exit_code == 1
        assert "restore.sh가 없습니다" in result.stdout
