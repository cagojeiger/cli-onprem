"""pytest 공통 픽스처 및 설정."""

import tempfile
from pathlib import Path
from typing import Generator
from unittest import mock

import pytest
import yaml


@pytest.fixture
def mock_home_dir() -> Generator[Path, None, None]:
    """홈 디렉터리를 모킹하는 픽스처.

    Yields:
        임시 홈 디렉터리 경로
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        home_dir = Path(tmpdir) / "home"
        home_dir.mkdir(parents=True)

        with mock.patch("pathlib.Path.home", return_value=home_dir):
            yield home_dir


@pytest.fixture
def mock_credentials(mock_home_dir: Path) -> Generator[Path, None, None]:
    """자격증명 파일을 생성하는 픽스처.

    Args:
        mock_home_dir: 모킹된 홈 디렉터리

    Yields:
        자격증명 파일 경로
    """
    config_dir = mock_home_dir / ".cli-onprem"
    config_dir.mkdir(parents=True)
    credential_path = config_dir / "credential.yaml"

    credentials = {
        "default": {
            "aws_access_key": "test_key",
            "aws_secret_key": "test_secret",
            "region": "us-east-1",
            "bucket": "test-bucket",
            "prefix": "test-prefix/",
        },
        "profile1": {
            "aws_access_key": "key1",
            "aws_secret_key": "secret1",
            "region": "ap-northeast-2",
        },
    }

    credential_path.write_text(yaml.dump(credentials))
    yield credential_path


@pytest.fixture
def mock_s3_client() -> Generator[mock.MagicMock, None, None]:
    """S3 클라이언트를 모킹하는 픽스처.

    Yields:
        모킹된 S3 클라이언트
    """
    with mock.patch("boto3.client") as mock_boto3_client:
        mock_client = mock.MagicMock()
        mock_boto3_client.return_value = mock_client

        # 기본 응답 설정
        mock_client.head_object.return_value = {
            "ContentLength": 1024,
            "ETag": '"abc123"',
            "LastModified": "2023-01-01",
        }

        mock_client.generate_presigned_url.return_value = (
            "https://example.com/presigned"
        )

        # Paginator 설정
        mock_paginator = mock.MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = []

        yield mock_client


@pytest.fixture
def mock_s3_error_client() -> Generator[mock.MagicMock, None, None]:
    """에러를 발생시키는 S3 클라이언트를 모킹하는 픽스처.

    Yields:
        에러를 발생시키는 모킹된 S3 클라이언트
    """
    from botocore.exceptions import ClientError

    with mock.patch("boto3.client") as mock_boto3_client:
        mock_client = mock.MagicMock()
        mock_boto3_client.return_value = mock_client

        # 에러 응답 설정
        error_response = {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}}
        mock_client.head_object.side_effect = ClientError(error_response, "HeadObject")
        mock_client.upload_file.side_effect = ClientError(error_response, "UploadFile")
        mock_client.list_objects_v2.side_effect = ClientError(
            error_response, "ListObjects"
        )

        yield mock_client
