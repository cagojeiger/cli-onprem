"""S3 share 자동완성 함수 테스트."""

import tempfile
from pathlib import Path
from unittest import mock

from cli_onprem.commands.s3_share import (
    complete_bucket,
    complete_cli_onprem_paths,
    complete_prefix,
    complete_profile,
)


def test_complete_profile_with_matches() -> None:
    """매칭되는 프로파일이 있는 경우 테스트."""
    with tempfile.TemporaryDirectory() as tmpdir:
        home_dir = Path(tmpdir)
        config_dir = home_dir / ".cli-onprem"
        config_dir.mkdir()

        credential_path = config_dir / "credential.yaml"
        credential_path.write_text(
            """
profile1:
  aws_access_key: key1
profile2:
  aws_access_key: key2
production:
  aws_access_key: key3
"""
        )

        with mock.patch("pathlib.Path.home", return_value=home_dir):
            # "pro"로 시작하는 프로파일
            results = complete_profile("pro")
            assert "production" in results
            assert "profile1" in results  # profile1도 "pro"로 시작함
            assert "profile2" in results  # profile2도 "pro"로 시작함

            # 빈 문자열로 모든 프로파일
            results = complete_profile("")
            assert len(results) == 3
            assert "profile1" in results
            assert "profile2" in results
            assert "production" in results


def test_complete_profile_no_credentials() -> None:
    """credential 파일이 없는 경우 테스트."""
    with tempfile.TemporaryDirectory() as tmpdir:
        home_dir = Path(tmpdir)

        with mock.patch("pathlib.Path.home", return_value=home_dir):
            results = complete_profile("test")
            assert results == []


def test_complete_profile_exception() -> None:
    """예외 발생 시 빈 리스트 반환 테스트."""
    with mock.patch("pathlib.Path.home") as mock_home:
        mock_home.side_effect = Exception("Test error")

        results = complete_profile("test")
        assert results == []


def test_complete_bucket() -> None:
    """버킷 자동완성 테스트."""

    with tempfile.TemporaryDirectory() as tmpdir:
        home_dir = Path(tmpdir)
        config_dir = home_dir / ".cli-onprem"
        config_dir.mkdir()

        credential_path = config_dir / "credential.yaml"
        credential_path.write_text(
            """
test-profile:
  aws_access_key: key
  aws_secret_key: secret
  region: us-east-1
"""
        )

        with mock.patch("pathlib.Path.home", return_value=home_dir):
            with mock.patch("boto3.client") as mock_client:
                mock_s3 = mock.MagicMock()
                mock_client.return_value = mock_s3
                mock_s3.list_buckets.return_value = {
                    "Buckets": [
                        {"Name": "bucket1"},
                        {"Name": "bucket2"},
                        {"Name": "my-bucket"},
                    ]
                }

                # "my"로 시작하는 버킷
                results = complete_bucket("my")
                assert "my-bucket" in results
                assert "bucket1" not in results


def test_complete_bucket_no_profile() -> None:
    """프로파일이 없는 경우 버킷 자동완성 테스트."""
    with tempfile.TemporaryDirectory() as tmpdir:
        home_dir = Path(tmpdir)

        with mock.patch("pathlib.Path.home", return_value=home_dir):
            results = complete_bucket("test")
            assert results == []


def test_complete_bucket_exception() -> None:
    """버킷 목록 조회 실패 시 테스트."""

    with tempfile.TemporaryDirectory() as tmpdir:
        home_dir = Path(tmpdir)
        config_dir = home_dir / ".cli-onprem"
        config_dir.mkdir()

        credential_path = config_dir / "credential.yaml"
        credential_path.write_text(
            """
test-profile:
  aws_access_key: key
  aws_secret_key: secret
  region: us-east-1
"""
        )

        with mock.patch("pathlib.Path.home", return_value=home_dir):
            with mock.patch("boto3.client") as mock_client:
                mock_client.side_effect = Exception("Connection error")

                results = complete_bucket("test")
                assert results == []


def test_complete_prefix() -> None:
    """프리픽스 자동완성 테스트."""

    with tempfile.TemporaryDirectory() as tmpdir:
        home_dir = Path(tmpdir)
        config_dir = home_dir / ".cli-onprem"
        config_dir.mkdir()

        credential_path = config_dir / "credential.yaml"
        credential_path.write_text(
            """
test-profile:
  aws_access_key: key
  aws_secret_key: secret
  region: us-east-1
"""
        )

        with mock.patch("pathlib.Path.home", return_value=home_dir):
            with mock.patch("boto3.client") as mock_client:
                mock_s3 = mock.MagicMock()
                mock_client.return_value = mock_s3

                mock_paginator = mock.MagicMock()
                mock_s3.get_paginator.return_value = mock_paginator
                mock_paginator.paginate.return_value = [
                    {
                        "CommonPrefixes": [
                            {"Prefix": "folder1/"},
                            {"Prefix": "folder2/"},
                            {"Prefix": "my-folder/"},
                        ]
                    }
                ]

                # "my"로 시작하는 프리픽스
                results = complete_prefix("my", "test-bucket")
                assert "my-folder/" in results
                assert "folder1/" not in results


def test_complete_prefix_no_bucket() -> None:
    """버킷이 없는 경우 프리픽스 자동완성 테스트."""
    with tempfile.TemporaryDirectory() as tmpdir:
        home_dir = Path(tmpdir)
        config_dir = home_dir / ".cli-onprem"
        config_dir.mkdir()

        credential_path = config_dir / "credential.yaml"
        credential_path.write_text(
            """
test-profile:
  aws_access_key: key
  aws_secret_key: secret
  region: us-east-1
"""
        )

        with mock.patch("pathlib.Path.home", return_value=home_dir):
            results = complete_prefix("test")
            assert results == []


def test_complete_cli_onprem_paths() -> None:
    """cli-onprem 프리픽스 경로 자동완성 테스트."""
    with tempfile.TemporaryDirectory() as tmpdir:
        home_dir = Path(tmpdir)
        config_dir = home_dir / ".cli-onprem"
        config_dir.mkdir()

        credential_path = config_dir / "credential.yaml"
        credential_path.write_text(
            """
test-profile:
  aws_access_key: key
  aws_secret_key: secret
  region: us-east-1
  bucket: test-bucket
  prefix: test-prefix
"""
        )

        with mock.patch("pathlib.Path.home", return_value=home_dir):
            with mock.patch("boto3.client") as mock_client:
                mock_s3 = mock.MagicMock()
                mock_client.return_value = mock_s3

                # list_objects 모킹
                # 함수가 내부적으로 create_s3_client를 호출하므로 mock 필요
                with mock.patch(
                    "cli_onprem.commands.s3_share.create_s3_client"
                ) as mock_create:
                    mock_create.return_value = mock_s3

                    with mock.patch(
                        "cli_onprem.commands.s3_share.list_objects"
                    ) as mock_list:
                        mock_list.return_value = (
                            [
                                "test-prefix/cli-onprem-folder1/",
                                "test-prefix/cli-onprem-folder2/",
                            ],
                            [
                                {"Key": "test-prefix/cli-onprem-file1.txt"},
                                {"Key": "test-prefix/cli-onprem-file2.txt"},
                            ],
                        )

                        # "cli-onprem-f"로 시작하는 경로
                        results = complete_cli_onprem_paths("cli-onprem-f")
                        # 폴더명은 / 없이 반환됨
                        assert "cli-onprem-folder1" in results
                        assert "cli-onprem-folder2" in results
                        assert "cli-onprem-file1.txt" in results
                        assert "cli-onprem-file2.txt" in results


# complete_s3_path 함수가 존재하지 않으므로 이 테스트들은 제거
