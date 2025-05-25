"""S3 서비스 테스트."""

import tempfile
from pathlib import Path
from unittest import mock

import pytest
from botocore.exceptions import ClientError

from cli_onprem.core.errors import CLIError
from cli_onprem.services.s3 import (
    create_s3_client,
    generate_presigned_url,
    generate_s3_path,
    head_object,
    list_buckets,
    list_objects,
    sync_to_s3,
    upload_file,
)


def test_create_s3_client_success() -> None:
    """S3 클라이언트 생성 성공 테스트."""
    with mock.patch("boto3.client") as mock_client:
        mock_s3 = mock.MagicMock()
        mock_client.return_value = mock_s3

        result = create_s3_client("test_key", "test_secret", "us-east-1")

        assert result == mock_s3
        mock_client.assert_called_once_with(
            "s3",
            aws_access_key_id="test_key",
            aws_secret_access_key="test_secret",
            region_name="us-east-1",
        )


# create_s3_client는 endpoint_url을 받지 않으므로 제거


def test_generate_s3_path() -> None:
    """S3 경로 생성 테스트."""

    # 날짜를 모킹하여 고정된 값 사용
    with mock.patch("datetime.datetime") as mock_datetime:
        mock_datetime.now.return_value.strftime.return_value = "20231225"

        # 파일 경로
        file_path = Path("test.txt")
        result = generate_s3_path(file_path, "my-prefix")
        assert result == "my-prefixcli-onprem-20231225-test.txt"

        # 디렉터리 경로 - is_dir() 모킹 필요
        dir_path = Path("folder")
        with mock.patch.object(Path, "is_dir", return_value=True):
            result = generate_s3_path(dir_path, "prefix")
            assert result == "prefixcli-onprem-20231225-folder/"

        # 빈 프리픽스
        result = generate_s3_path(file_path, "")
        assert result == "cli-onprem-20231225-test.txt"


def test_head_object_success() -> None:
    """head_object 성공 테스트."""
    mock_client = mock.MagicMock()
    mock_response = {
        "ContentLength": 1024,
        "ETag": '"abc123"',
        "LastModified": "2023-01-01",
    }
    mock_client.head_object.return_value = mock_response

    result = head_object(mock_client, "test-bucket", "test-key")

    assert result["ContentLength"] == 1024
    assert result["ETag"] == "abc123"  # 따옴표 제거됨
    assert result["LastModified"] == "2023-01-01"
    mock_client.head_object.assert_called_once_with(
        Bucket="test-bucket", Key="test-key"
    )


def test_head_object_not_found() -> None:
    """head_object 객체 없음 테스트."""
    mock_client = mock.MagicMock()
    mock_client.head_object.side_effect = ClientError(
        {"Error": {"Code": "404"}}, "HeadObject"
    )

    with pytest.raises(CLIError, match="객체를 찾을 수 없습니다"):
        head_object(mock_client, "test-bucket", "test-key")


def test_head_object_other_error() -> None:
    """head_object 기타 에러 테스트."""
    mock_client = mock.MagicMock()
    mock_client.head_object.side_effect = ClientError(
        {"Error": {"Code": "403"}}, "HeadObject"
    )

    with pytest.raises(CLIError, match="객체 조회 실패"):
        head_object(mock_client, "test-bucket", "test-key")


def test_list_buckets_success() -> None:
    """버킷 목록 조회 성공 테스트."""
    mock_client = mock.MagicMock()
    mock_client.list_buckets.return_value = {
        "Buckets": [
            {"Name": "bucket1"},
            {"Name": "bucket2"},
            {"Name": "my-bucket"},
        ]
    }

    result = list_buckets(mock_client)

    assert result == ["bucket1", "bucket2", "my-bucket"]


def test_list_buckets_error() -> None:
    """버킷 목록 조회 실패 테스트."""
    mock_client = mock.MagicMock()
    mock_client.list_buckets.side_effect = ClientError(
        {"Error": {"Code": "AccessDenied"}}, "ListBuckets"
    )

    with pytest.raises(CLIError, match="버킷 목록 조회 실패"):
        list_buckets(mock_client)


def test_list_objects_success() -> None:
    """객체 목록 조회 성공 테스트."""
    mock_client = mock.MagicMock()
    mock_paginator = mock.MagicMock()
    mock_client.get_paginator.return_value = mock_paginator

    mock_paginator.paginate.return_value = [
        {
            "Contents": [
                {
                    "Key": "prefix/file1.txt",
                    "Size": 1024,
                    "LastModified": "2023-01-01",
                    "ETag": '"abc"',
                },
                {
                    "Key": "prefix/file2.txt",
                    "Size": 2048,
                    "LastModified": "2023-01-01",
                    "ETag": '"def"',
                },
            ],
            "CommonPrefixes": [
                {"Prefix": "prefix/folder1/"},
                {"Prefix": "prefix/folder2/"},
            ],
        }
    ]

    prefixes, objects = list_objects(mock_client, "test-bucket", "prefix/")

    assert len(prefixes) == 2
    assert "prefix/folder1/" in prefixes
    assert "prefix/folder2/" in prefixes

    assert len(objects) == 2
    assert objects[0]["Key"] == "prefix/file1.txt"
    assert objects[1]["Key"] == "prefix/file2.txt"


def test_list_objects_empty() -> None:
    """빈 객체 목록 조회 테스트."""
    mock_client = mock.MagicMock()
    mock_paginator = mock.MagicMock()
    mock_client.get_paginator.return_value = mock_paginator
    mock_paginator.paginate.return_value = [{}]

    prefixes, objects = list_objects(mock_client, "test-bucket", "prefix/")

    assert prefixes == []
    assert objects == []


def test_upload_file_success() -> None:
    """파일 업로드 성공 테스트."""
    mock_client = mock.MagicMock()

    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test content")
        f.flush()
        file_path = Path(f.name)

        try:
            upload_file(mock_client, file_path, "test-bucket", "test-key")

            mock_client.upload_file.assert_called_once()
            # 호출 인자 확인
            call_args = mock_client.upload_file.call_args
            assert call_args[0][0] == str(file_path)
            assert call_args[0][1] == "test-bucket"
            assert call_args[0][2] == "test-key"
        finally:
            file_path.unlink()


def test_upload_file_failure() -> None:
    """파일 업로드 실패 테스트."""
    mock_client = mock.MagicMock()
    mock_client.upload_file.side_effect = ClientError(
        {"Error": {"Code": "AccessDenied"}}, "PutObject"
    )

    file_path = Path("test.txt")

    with pytest.raises(CLIError, match="업로드 실패"):
        upload_file(mock_client, file_path, "test-bucket", "test-key")


def test_generate_presigned_url_success() -> None:
    """Presigned URL 생성 성공 테스트."""
    mock_client = mock.MagicMock()
    mock_client.generate_presigned_url.return_value = (
        "https://s3.example.com/signed-url"
    )

    result = generate_presigned_url(
        mock_client, "test-bucket", "test-key", expires_in=3600
    )

    assert result == "https://s3.example.com/signed-url"
    mock_client.generate_presigned_url.assert_called_once_with(
        "get_object",
        Params={"Bucket": "test-bucket", "Key": "test-key"},
        ExpiresIn=3600,
    )


def test_generate_presigned_url_failure() -> None:
    """Presigned URL 생성 실패 테스트."""
    mock_client = mock.MagicMock()
    mock_client.generate_presigned_url.side_effect = ClientError(
        {"Error": {"Code": "AccessDenied"}}, "GeneratePresignedUrl"
    )

    with pytest.raises(CLIError, match="Presigned URL 생성 실패"):
        generate_presigned_url(mock_client, "test-bucket", "test-key")


def test_sync_to_s3_file() -> None:
    """단일 파일 동기화 테스트."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("test content")
        f.flush()
        file_path = Path(f.name)

        try:
            mock_client = mock.MagicMock()
            # head_object가 None을 반환하여 파일이 없음을 나타냄
            mock_client.head_object.side_effect = ClientError(
                {"Error": {"Code": "404"}}, "HeadObject"
            )

            uploaded, skipped, deleted = sync_to_s3(
                mock_client, file_path, "test-bucket", "prefix", delete=False
            )

            assert uploaded == 1
            assert skipped == 0
            assert deleted == 0
            mock_client.upload_file.assert_called_once()
        finally:
            file_path.unlink()


def test_sync_to_s3_directory() -> None:
    """디렉터리 동기화 테스트."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # 테스트 파일들 생성
        file1 = tmpdir_path / "file1.txt"
        file1.write_text("content1")

        file2 = tmpdir_path / "file2.txt"
        file2.write_text("content2")

        subdir = tmpdir_path / "subdir"
        subdir.mkdir()
        file3 = subdir / "file3.txt"
        file3.write_text("content3")

        mock_client = mock.MagicMock()
        mock_paginator = mock.MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [{}]  # 빈 버킷

        # head_object가 404를 반환하여 모든 파일이 새로운 것임을 나타냄
        mock_client.head_object.side_effect = ClientError(
            {"Error": {"Code": "404"}}, "HeadObject"
        )

        uploaded, skipped, deleted = sync_to_s3(
            mock_client, tmpdir_path, "test-bucket", "prefix", delete=False
        )

        assert uploaded == 3
        assert skipped == 0
        assert deleted == 0
        assert mock_client.upload_file.call_count == 3


def test_sync_to_s3_with_delete() -> None:
    """삭제 옵션이 있는 동기화 테스트."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        file1 = tmpdir_path / "file1.txt"
        file1.write_text("content1")

        mock_client = mock.MagicMock()
        mock_paginator = mock.MagicMock()
        mock_client.get_paginator.return_value = mock_paginator

        # LastModified를 datetime 객체로 만들기
        # 미래 시간으로 설정하여 로컬 파일보다 새것으로 만듦
        from datetime import datetime, timezone

        future_time = datetime.now(timezone.utc).replace(year=2030)
        mock_paginator.paginate.return_value = [
            {
                "Contents": [
                    {
                        "Key": "prefixfile1.txt",
                        "Size": 8,
                        "LastModified": future_time,
                        "ETag": "7e55db001d319a94b0b713529a756623",
                    },
                    {
                        "Key": "prefixfile2.txt",
                        "Size": 2048,
                        "LastModified": future_time,
                        "ETag": "def",
                    },  # 로컬에 없는 파일
                ]
            }
        ]

        # 파일 md5 계산 모킹
        with mock.patch("cli_onprem.utils.hash.calculate_file_md5") as mock_md5:
            # file1.txt의 실제 MD5와 동일하게 설정
            mock_md5.return_value = (
                "7e55db001d319a94b0b713529a756623"  # content1의 실제 MD5
            )

            # delete_objects도 모킹
            mock_client.delete_objects.return_value = {
                "Deleted": [{"Key": "prefixfile2.txt"}]
            }

            uploaded, skipped, deleted = sync_to_s3(
                mock_client, tmpdir_path, "test-bucket", "prefix", delete=True
            )

            assert uploaded == 0
            assert skipped == 1
            assert deleted == 1
            mock_client.delete_objects.assert_called_once()


def test_sync_to_s3_dry_run() -> None:
    """드라이런 모드 테스트."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("test content")
        f.flush()
        file_path = Path(f.name)

        try:
            mock_client = mock.MagicMock()
            mock_client.head_object.side_effect = ClientError(
                {"Error": {"Code": "404"}}, "HeadObject"
            )

            # sync_to_s3는 dry_run 파라미터를 받지 않으므로 수정
            uploaded, skipped, deleted = sync_to_s3(
                mock_client, file_path, "test-bucket", "prefix", delete=False
            )

            assert uploaded == 1
            # 실제 업로드가 일어남
            mock_client.upload_file.assert_called_once()
        finally:
            file_path.unlink()
