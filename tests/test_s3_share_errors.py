"""S3 공유 명령어 에러 케이스 테스트."""

import subprocess
import tempfile
from pathlib import Path
from typing import Any
from unittest import mock

from botocore.exceptions import (
    ClientError,
)
from typer.testing import CliRunner

from cli_onprem.__main__ import app

runner = CliRunner()


def test_upload_network_error(mock_home_dir: Path, mock_credentials: Path) -> None:
    """네트워크 에러 발생 시 업로드 테스트."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("test content")
        test_file = Path(f.name)

    try:
        # AWS CLI 존재 확인 모킹
        with mock.patch(
            "cli_onprem.utils.shell.check_command_exists", return_value=True
        ):
            # AWS CLI 실행이 네트워크 에러로 실패
            with mock.patch("cli_onprem.utils.shell.run_command") as mock_run:
                # CalledProcessError 발생
                mock_run.side_effect = subprocess.CalledProcessError(
                    1, ["aws", "s3", "sync"], stderr="Unable to connect"
                )

                result = runner.invoke(
                    app,
                    ["s3-share", "sync", str(test_file), "--profile", "default"],
                )

                # AWS CLI 에러로 인한 종료
                assert result.exit_code == 1
                assert "AWS CLI 오류" in result.stdout
    finally:
        test_file.unlink()


def test_upload_permission_denied(mock_home_dir: Path, mock_credentials: Path) -> None:
    """권한 에러 발생 시 업로드 테스트."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("test content")
        test_file = Path(f.name)

    try:
        with mock.patch("boto3.client") as mock_client:
            mock_s3 = mock.MagicMock()
            mock_client.return_value = mock_s3

            # Paginator 설정
            mock_paginator = mock.MagicMock()
            mock_s3.get_paginator.return_value = mock_paginator
            mock_paginator.paginate.return_value = []

            # AccessDenied 에러
            error_response = {
                "Error": {"Code": "AccessDenied", "Message": "Access Denied"}
            }
            mock_s3.upload_file.side_effect = ClientError(error_response, "PutObject")

            result = runner.invoke(
                app,
                ["s3-share", "sync", str(test_file), "--profile", "default"],
            )

            assert result.exit_code == 1
            assert "오류" in result.stdout
    finally:
        test_file.unlink()


# list-objects 명령어는 존재하지 않으므로 제거


def test_presign_url_generation_error(
    mock_home_dir: Path, mock_credentials: Path
) -> None:
    """Presigned URL 생성 시 에러 테스트."""
    with mock.patch("boto3.client") as mock_client:
        mock_s3 = mock.MagicMock()
        mock_client.return_value = mock_s3

        # head_object는 성공
        mock_s3.head_object.return_value = {"ContentLength": 1024, "ETag": '"abc123"'}

        # generate_presigned_url 실패
        error_response = {
            "Error": {"Code": "InvalidRequest", "Message": "Invalid request"}
        }
        mock_s3.generate_presigned_url.side_effect = ClientError(
            error_response, "GeneratePresignedUrl"
        )

        result = runner.invoke(
            app,
            [
                "s3-share",
                "presign",
                "--select-path",
                "test.txt",
                "--profile",
                "default",
            ],
        )

        # presign은 에러가 발생해도 경고만 표시하고 계속 진행
        assert result.exit_code == 0
        assert "경고" in result.stdout


def test_sync_partial_failure(mock_home_dir: Path, mock_credentials: Path) -> None:
    """동기화 중 일부 파일 업로드 실패 테스트."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 여러 파일 생성
        tmpdir_path = Path(tmpdir)
        file1 = tmpdir_path / "file1.txt"
        file1.write_text("content1")
        file2 = tmpdir_path / "file2.txt"
        file2.write_text("content2")

        with mock.patch("boto3.client") as mock_client:
            mock_s3 = mock.MagicMock()
            mock_client.return_value = mock_s3

            # 빈 버킷으로 모킹
            mock_paginator = mock.MagicMock()
            mock_s3.get_paginator.return_value = mock_paginator
            mock_paginator.paginate.return_value = []

            # 첫 번째 파일은 성공, 두 번째 파일은 실패
            call_count = 0

            def upload_side_effect(*args: Any, **kwargs: Any) -> None:
                nonlocal call_count
                call_count += 1
                if call_count == 2:
                    error_response = {
                        "Error": {"Code": "InternalError", "Message": "Internal Error"}
                    }
                    raise ClientError(error_response, "PutObject")

            mock_s3.upload_file.side_effect = upload_side_effect

            result = runner.invoke(
                app,
                ["s3-share", "sync", str(tmpdir_path), "--profile", "default"],
            )

            # sync는 개별 파일 실패를 처리하는 방식에 따라 다를 수 있음
            # 현재 구현에서는 에러가 발생하면 전체가 실패
            assert result.exit_code == 1


def test_invalid_bucket_name(mock_home_dir: Path) -> None:
    """잘못된 버킷 이름으로 init-bucket 테스트."""
    # 자격증명 생성
    config_dir = mock_home_dir / ".cli-onprem"
    config_dir.mkdir()

    with (
        mock.patch("os.chmod"),
        mock.patch("cli_onprem.commands.s3_share.Prompt") as mock_prompt,
    ):
        # 먼저 자격증명 생성
        mock_prompt.ask.side_effect = ["key", "secret", "us-east-1"]

        result = runner.invoke(
            app,
            ["s3-share", "init-credential", "--profile", "test"],
        )
        assert result.exit_code == 0

        # 잘못된 버킷 이름 (대문자 포함)
        mock_prompt.ask.side_effect = ["Invalid-Bucket-Name", "prefix/"]

        result = runner.invoke(
            app,
            ["s3-share", "init-bucket", "--profile", "test"],
        )

        # 버킷 이름 검증은 S3 서비스에서 하므로 여기서는 저장됨
        assert result.exit_code == 0


def test_expired_credentials(mock_home_dir: Path, mock_credentials: Path) -> None:
    """만료된 자격증명으로 작업 시도 테스트."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("test content")
        test_file = Path(f.name)

    try:
        with mock.patch("boto3.client") as mock_client:
            mock_s3 = mock.MagicMock()
            mock_client.return_value = mock_s3

            # Paginator 설정
            mock_paginator = mock.MagicMock()
            mock_s3.get_paginator.return_value = mock_paginator
            mock_paginator.paginate.return_value = []

            # ExpiredToken 에러
            error_response = {
                "Error": {
                    "Code": "ExpiredToken",
                    "Message": "The provided token has expired.",
                }
            }
            mock_s3.upload_file.side_effect = ClientError(error_response, "PutObject")

            result = runner.invoke(
                app,
                ["s3-share", "sync", str(test_file), "--profile", "default"],
            )

            assert result.exit_code == 1
            assert "오류" in result.stdout
    finally:
        test_file.unlink()


def test_bucket_not_found(mock_home_dir: Path, mock_credentials: Path) -> None:
    """존재하지 않는 버킷에 업로드 시도 테스트."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("test content")
        test_file = Path(f.name)

    try:
        with mock.patch("boto3.client") as mock_client:
            mock_s3 = mock.MagicMock()
            mock_client.return_value = mock_s3

            # Paginator 설정
            mock_paginator = mock.MagicMock()
            mock_s3.get_paginator.return_value = mock_paginator
            mock_paginator.paginate.return_value = []

            # NoSuchBucket 에러
            error_response = {
                "Error": {
                    "Code": "NoSuchBucket",
                    "Message": "The specified bucket does not exist",
                }
            }
            mock_s3.upload_file.side_effect = ClientError(error_response, "PutObject")

            result = runner.invoke(
                app,
                ["s3-share", "sync", str(test_file), "--profile", "default"],
            )

            assert result.exit_code == 1
            assert "오류" in result.stdout
    finally:
        test_file.unlink()


# list-objects를 사용하는 throttling 테스트도 제거
