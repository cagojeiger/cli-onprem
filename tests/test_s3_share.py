"""S3 공유 명령어 테스트."""

import pathlib
import re
from unittest import mock

import yaml
from typer.testing import CliRunner

from cli_onprem.__main__ import app


def strip_ansi(text: str) -> str:
    """ANSI 색상 코드를 제거합니다."""
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


runner = CliRunner(mix_stderr=False)


def test_init_command_creates_credential_file(tmp_path: pathlib.Path) -> None:
    """init 명령어가 자격증명 파일을 생성하는지 테스트합니다."""
    home_dir = tmp_path / "home"
    home_dir.mkdir()

    config_dir = home_dir / ".cli-onprem"
    config_dir.mkdir()

    credential_path = config_dir / "credential.yaml"

    with mock.patch("pathlib.Path.home", return_value=home_dir):
        with mock.patch("os.chmod"):
            result1 = runner.invoke(
                app,
                ["s3-share", "init-credential", "--profile", "test_profile"],
                input="test_key\ntest_secret\ntest_region\n",
            )
            assert result1.exit_code == 0

            result2 = runner.invoke(
                app,
                ["s3-share", "init-bucket", "--profile", "test_profile"],
                input="test_bucket\ntest_prefix\n",
            )
            assert result2.exit_code == 0
            assert '자격증명 저장됨: 프로파일 "test_profile"' in strip_ansi(
                result1.stdout
            )
            assert '버킷 정보 저장됨: 프로파일 "test_profile"' in strip_ansi(
                result2.stdout
            )

            assert credential_path.exists()

            with open(credential_path) as f:
                credentials = yaml.safe_load(f)
                assert "test_profile" in credentials
                assert credentials["test_profile"]["aws_access_key"] == "test_key"
                assert credentials["test_profile"]["aws_secret_key"] == "test_secret"
                assert credentials["test_profile"]["region"] == "test_region"
                assert credentials["test_profile"]["bucket"] == "test_bucket"
                assert credentials["test_profile"]["prefix"] == "test_prefix"


def test_init_command_with_existing_profile_no_overwrite(
    tmp_path: pathlib.Path,
) -> None:
    """기존 프로파일이 있을 때 덮어쓰기 거부 테스트."""
    home_dir = tmp_path / "home"
    home_dir.mkdir()

    config_dir = home_dir / ".cli-onprem"
    config_dir.mkdir()

    credential_path = config_dir / "credential.yaml"
    existing_credentials = {
        "test_profile": {
            "aws_access_key": "existing_key",
            "aws_secret_key": "existing_secret",
            "region": "existing_region",
            "bucket": "existing_bucket",
            "prefix": "existing_prefix",
        }
    }
    with open(credential_path, "w") as f:
        yaml.dump(existing_credentials, f)

    with mock.patch("pathlib.Path.home", return_value=home_dir):
        result = runner.invoke(
            app,
            [
                "s3-share",
                "init-credential",
                "--profile",
                "test_profile",
                "--no-overwrite",
            ],
            input="n\n",  # 덮어쓰기 거부
        )

        assert result.exit_code == 0
        assert "경고: 프로파일 'test_profile'이(가) 이미 존재합니다." in strip_ansi(
            result.stdout
        )
        assert "작업이 취소되었습니다." in strip_ansi(result.stdout)

        with open(credential_path) as f:
            credentials = yaml.safe_load(f)
            assert credentials["test_profile"]["aws_access_key"] == "existing_key"


def test_init_command_with_existing_profile_overwrite(tmp_path: pathlib.Path) -> None:
    """기존 프로파일이 있을 때 덮어쓰기 테스트."""
    home_dir = tmp_path / "home"
    home_dir.mkdir()

    config_dir = home_dir / ".cli-onprem"
    config_dir.mkdir()

    credential_path = config_dir / "credential.yaml"
    existing_credentials = {
        "test_profile": {
            "aws_access_key": "existing_key",
            "aws_secret_key": "existing_secret",
            "region": "existing_region",
            "bucket": "existing_bucket",
            "prefix": "existing_prefix",
        }
    }
    with open(credential_path, "w") as f:
        yaml.dump(existing_credentials, f)

    with mock.patch("pathlib.Path.home", return_value=home_dir):
        with mock.patch("os.chmod"):
            result1 = runner.invoke(
                app,
                [
                    "s3-share",
                    "init-credential",
                    "--profile",
                    "test_profile",
                    "--overwrite",
                ],
                input="new_key\nnew_secret\nnew_region\n",
            )

            result2 = runner.invoke(
                app,
                ["s3-share", "init-bucket", "--profile", "test_profile"],
                input="new_bucket\nnew_prefix\n",
            )

            assert result1.exit_code == 0
            assert result2.exit_code == 0
            assert '자격증명 저장됨: 프로파일 "test_profile"' in strip_ansi(
                result1.stdout
            )
            assert '버킷 정보 저장됨: 프로파일 "test_profile"' in strip_ansi(
                result2.stdout
            )

            with open(credential_path) as f:
                credentials = yaml.safe_load(f)
                assert credentials["test_profile"]["aws_access_key"] == "new_key"
                assert credentials["test_profile"]["aws_secret_key"] == "new_secret"
                assert credentials["test_profile"]["region"] == "new_region"
                assert credentials["test_profile"]["bucket"] == "new_bucket"
                assert credentials["test_profile"]["prefix"] == "new_prefix"
