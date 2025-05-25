"""tar_fat32 통합 테스트를 위한 새로운 파일."""

import tempfile
from pathlib import Path
from unittest import mock

from typer.testing import CliRunner

from cli_onprem.__main__ import app

runner = CliRunner()


def test_pack_command_with_mocked_functions() -> None:
    """Pack 명령 통합 테스트 - 모든 외부 의존성을 모킹."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        test_file = tmp_path / "testfile.txt"
        test_file.write_text("test content")

        # 모든 필요한 함수를 한 번에 모킹
        with mock.patch.multiple(
            "cli_onprem.commands.tar_fat32",
            shutil=mock.DEFAULT,
            create_tar_archive=mock.DEFAULT,
            split_file=mock.DEFAULT,
            calculate_sha256_manifest=mock.DEFAULT,
            write_manifest_file=mock.DEFAULT,
            get_directory_size_mb=mock.DEFAULT,
            generate_restore_script=mock.DEFAULT,
            create_size_marker=mock.DEFAULT,
            make_executable=mock.DEFAULT,
        ) as mocks:
            # 필요한 반환값 설정
            mocks["split_file"].return_value = [Path("parts/0000.part")]
            mocks["calculate_sha256_manifest"].return_value = [
                ("parts/0000.part", "abc123")
            ]
            mocks["get_directory_size_mb"].return_value = 10
            mocks["generate_restore_script"].return_value = "#!/bin/sh\necho test"

            # pathlib.Path.unlink 모킹
            with mock.patch("pathlib.Path.unlink"):
                result = runner.invoke(
                    app,
                    ["tar-fat32", "pack", str(test_file)],
                )

                assert result.exit_code == 0
                assert "압축 완료" in result.stdout

                # 함수 호출 확인
                mocks["create_tar_archive"].assert_called_once()
                mocks["split_file"].assert_called_once()
                mocks["calculate_sha256_manifest"].assert_called_once()
                mocks["write_manifest_file"].assert_called_once()


def test_restore_command_with_mocked_functions() -> None:
    """Restore 명령 통합 테스트 - 모든 외부 의존성을 모킹."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        pack_dir = tmp_path / "test.pack"
        pack_dir.mkdir()

        # 필요한 파일 생성
        (pack_dir / "restore.sh").write_text("#!/bin/sh\necho test")
        (pack_dir / "manifest.sha256").write_text("abc123  parts/0000.part\n")
        parts_dir = pack_dir / "parts"
        parts_dir.mkdir()
        (parts_dir / "0000.part").write_bytes(b"test content")

        # 모든 필요한 함수를 한 번에 모킹
        with mock.patch.multiple(
            "cli_onprem.commands.tar_fat32",
            verify_manifest=mock.DEFAULT,
            merge_files=mock.DEFAULT,
            extract_tar_archive=mock.DEFAULT,
        ) as mocks:
            # pathlib.Path.unlink 모킹
            with mock.patch("pathlib.Path.unlink"):
                result = runner.invoke(
                    app,
                    ["tar-fat32", "restore", str(pack_dir)],
                )

                assert result.exit_code == 0
                assert "복원 완료" in result.stdout

                # 함수 호출 확인
                mocks["verify_manifest"].assert_called_once()
                mocks["merge_files"].assert_called_once()
                mocks["extract_tar_archive"].assert_called_once()
