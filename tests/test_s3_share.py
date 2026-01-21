"""S3 공유 명령어 테스트."""

import re
from pathlib import Path
from unittest import mock

import yaml
from typer.testing import CliRunner

from cli_onprem.__main__ import app


def strip_ansi(text: str) -> str:
    """ANSI 색상 코드를 제거합니다."""
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


runner = CliRunner(mix_stderr=False)


def test_init_command_creates_credential_file(mock_home_dir: Path) -> None:
    """init 명령어가 자격증명 파일을 생성하는지 테스트합니다."""
    config_dir = mock_home_dir / ".cli-onprem"
    config_dir.mkdir()
    credential_path = config_dir / "credential.yaml"

    with (
        mock.patch("os.chmod"),
        mock.patch("cli_onprem.commands.s3_share.Prompt") as mock_prompt,
    ):
        # init-credential에서 사용하는 Prompt.ask 호출들을 순서대로 모킹
        mock_prompt.ask.side_effect = ["test_key", "test_secret", "test_region"]

        result1 = runner.invoke(
            app,
            ["s3-share", "init-credential", "--profile", "test_profile"],
        )
        assert result1.exit_code == 0

        # init-bucket에서 사용하는 Prompt.ask 호출들을 순서대로 모킹
        mock_prompt.ask.side_effect = ["test_bucket", "test_prefix"]

        result2 = runner.invoke(
            app,
            ["s3-share", "init-bucket", "--profile", "test_profile"],
        )
        assert result2.exit_code == 0
        assert '자격증명 저장됨: 프로파일 "test_profile"' in strip_ansi(result1.stdout)
        assert '버킷 정보 저장됨: 프로파일 "test_profile"' in strip_ansi(result2.stdout)

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
    mock_home_dir: Path,
) -> None:
    """기존 프로파일이 있을 때 덮어쓰기 거부 테스트."""
    config_dir = mock_home_dir / ".cli-onprem"
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

    with mock.patch("cli_onprem.commands.s3_share.Confirm") as mock_confirm:
        # Confirm.ask가 False를 반환하도록 설정 (덮어쓰기 거부)
        mock_confirm.ask.return_value = False

        result = runner.invoke(
            app,
            [
                "s3-share",
                "init-credential",
                "--profile",
                "test_profile",
                "--no-overwrite",
            ],
        )

        assert result.exit_code == 0
        assert "경고: 프로파일 'test_profile'이(가) 이미 존재합니다." in strip_ansi(
            result.stdout
        )
        assert "작업이 취소되었습니다." in strip_ansi(result.stdout)

        with open(credential_path) as f:
            credentials = yaml.safe_load(f)
            assert credentials["test_profile"]["aws_access_key"] == "existing_key"


def test_sync_command_uses_long_timeout(
    mock_home_dir: Path,
    mock_credentials: Path,
    tmp_path: Path,
) -> None:
    """sync 명령어가 LONG_TIMEOUT을 사용하는지 테스트합니다."""
    # 테스트용 파일 생성
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")

    with (
        mock.patch("cli_onprem.utils.shell.check_command_exists", return_value=True),
        mock.patch("cli_onprem.utils.shell.run_command") as mock_run_command,
    ):
        runner.invoke(
            app,
            ["s3-share", "sync", str(test_file), "--profile", "default"],
        )

        # run_command가 호출되었는지 확인
        assert mock_run_command.called
        # timeout 파라미터가 전달되었는지 확인
        call_kwargs = mock_run_command.call_args.kwargs
        assert "timeout" in call_kwargs
        # LONG_TIMEOUT (기본값 1800) 이 전달되어야 함
        assert call_kwargs["timeout"] == 1800


def test_init_command_with_existing_profile_overwrite(mock_home_dir: Path) -> None:
    """기존 프로파일이 있을 때 덮어쓰기 테스트."""
    config_dir = mock_home_dir / ".cli-onprem"
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

    with (
        mock.patch("os.chmod"),
        mock.patch("cli_onprem.commands.s3_share.Prompt") as mock_prompt,
    ):
        # init-credential에서 사용하는 Prompt.ask 호출들을 순서대로 모킹
        mock_prompt.ask.side_effect = ["new_key", "new_secret", "new_region"]

        result1 = runner.invoke(
            app,
            [
                "s3-share",
                "init-credential",
                "--profile",
                "test_profile",
                "--overwrite",
            ],
        )

        # init-bucket에서 사용하는 Prompt.ask 호출들을 순서대로 모킹
        mock_prompt.ask.side_effect = ["new_bucket", "new_prefix"]

        result2 = runner.invoke(
            app,
            ["s3-share", "init-bucket", "--profile", "test_profile"],
        )

        assert result1.exit_code == 0
        assert result2.exit_code == 0
        assert '자격증명 저장됨: 프로파일 "test_profile"' in strip_ansi(result1.stdout)
        assert '버킷 정보 저장됨: 프로파일 "test_profile"' in strip_ansi(result2.stdout)

        with open(credential_path) as f:
            credentials = yaml.safe_load(f)
            assert credentials["test_profile"]["aws_access_key"] == "new_key"
            assert credentials["test_profile"]["aws_secret_key"] == "new_secret"
            assert credentials["test_profile"]["region"] == "new_region"
            assert credentials["test_profile"]["bucket"] == "new_bucket"
            assert credentials["test_profile"]["prefix"] == "new_prefix"
