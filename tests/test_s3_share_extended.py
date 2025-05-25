"""S3 share 명령어 확장 테스트."""

import tempfile
from pathlib import Path
from unittest import mock

from typer.testing import CliRunner

runner = CliRunner()


# list 명령어는 존재하지 않으므로 제거


# upload 명령어는 존재하지 않으므로 제거


def test_complete_profile_function_duplicate() -> None:
    """프로파일 자동완성 함수 테스트 (중복)."""
    from cli_onprem.commands.s3_share import complete_profile

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
            # "pro"로 시작하는 프로파일 찾기
            results = complete_profile("pro")
            assert "production" in results
            assert "profile1" in results  # profile1도 "pro"로 시작

            # 빈 문자열로 모든 프로파일 찾기
            results = complete_profile("")
            assert len(results) == 3
            assert "profile1" in results
            assert "profile2" in results
            assert "production" in results


# complete_s3_path 함수는 존재하지 않으므로 테스트 제거


def test_bucket_option_validation() -> None:
    """버킷 옵션 검증 테스트."""
    from cli_onprem.commands.s3_share import BUCKET_OPTION

    # BUCKET_OPTION이 올바른 타입인지 확인
    assert hasattr(BUCKET_OPTION, "default")
    assert BUCKET_OPTION.default is None
