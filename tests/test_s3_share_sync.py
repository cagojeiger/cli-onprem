"""S3 공유 sync 명령어 테스트."""

import pathlib
from unittest import mock

import yaml
from typer.testing import CliRunner

from cli_onprem.__main__ import app
from cli_onprem.utils.hash import calculate_file_md5

runner = CliRunner()


def test_calculate_file_md5(tmp_path: pathlib.Path) -> None:
    """calculate_file_md5 함수 테스트."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")

    md5 = calculate_file_md5(test_file)
    assert md5 == "9473fdd0d880a43c21b7778d34872157"


def test_sync_command_local_path_not_exist() -> None:
    """존재하지 않는 로컬 경로로 sync 명령 테스트."""
    with mock.patch("pathlib.Path.exists", return_value=False):
        result = runner.invoke(app, ["s3-share", "sync", "/not/exist/path"])

        assert result.exit_code == 1
        assert "오류: 소스 경로 '/not/exist/path'가 존재하지 않습니다." in result.stdout


def test_sync_command_profile_not_exist(tmp_path: pathlib.Path) -> None:
    """존재하지 않는 프로파일로 sync 명령 테스트."""
    home_dir = tmp_path / "home"
    home_dir.mkdir()

    config_dir = home_dir / ".cli-onprem"
    config_dir.mkdir()

    credential_path = config_dir / "credential.yaml"
    with open(credential_path, "w") as f:
        yaml.dump({"other_profile": {}}, f)

    with mock.patch("pathlib.Path.home", return_value=home_dir):
        with mock.patch("pathlib.Path.exists", return_value=True):
            with mock.patch("pathlib.Path.is_dir", return_value=True):
                result = runner.invoke(
                    app, ["s3-share", "sync", "/test/path", "--profile", "test_profile"]
                )

                assert result.exit_code == 1
                assert "오류: 프로파일 'test_profile'이(가) 존재하지" in result.stdout
                assert "않습니다." in result.stdout


def test_sync_command_success(tmp_path: pathlib.Path) -> None:
    """성공적인 sync 명령 테스트."""
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    test_file1 = src_dir / "file1.txt"
    test_file1.write_text("test content 1")

    test_file2 = src_dir / "file2.txt"
    test_file2.write_text("test content 2")

    home_dir = tmp_path / "home"
    home_dir.mkdir()

    config_dir = home_dir / ".cli-onprem"
    config_dir.mkdir()

    credential_path = config_dir / "credential.yaml"
    credentials = {
        "test_profile": {
            "aws_access_key": "test_key",
            "aws_secret_key": "test_secret",
            "region": "us-east-1",
            "bucket": "test-bucket",
            "prefix": "test-prefix",
        }
    }
    with open(credential_path, "w") as f:
        yaml.dump(credentials, f)

    with mock.patch("pathlib.Path.home", return_value=home_dir):
        with mock.patch("pathlib.Path.exists", return_value=True):
            with mock.patch("pathlib.Path.is_dir", return_value=True):
                # Mock AWS CLI 존재 확인
                with mock.patch(
                    "cli_onprem.utils.shell.check_command_exists", return_value=True
                ):
                    # Mock AWS CLI 실행
                    with mock.patch("cli_onprem.utils.shell.run_command") as mock_run:
                        # AWS CLI 실행이 성공했다고 가정
                        mock_run.return_value = mock.MagicMock(returncode=0)

                        result = runner.invoke(
                            app,
                            [
                                "s3-share",
                                "sync",
                                str(src_dir),
                                "--profile",
                                "test_profile",
                            ],
                        )

                        assert result.exit_code == 0
                        assert "동기화 완료" in result.stdout

                        # AWS CLI가 올바른 인자로 호출되었는지 확인
                        mock_run.assert_called_once()
                        call_args = mock_run.call_args[0][0]
                        assert call_args[0] == "aws"
                        assert call_args[1] == "s3"
                        assert call_args[2] == "sync"
                        assert str(src_dir) in call_args[3]
                        assert "s3://test-bucket/test-prefix/" in call_args[4]
