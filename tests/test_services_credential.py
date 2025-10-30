"""Tests for services/credential.py - AWS credential management."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from cli_onprem.core.errors import CLIError
from cli_onprem.services.credential import (
    DEFAULT_CONFIG_DIR_NAME,
    DEFAULT_PROFILE,
    create_or_update_profile,
    ensure_config_directory,
    get_config_dir,
    get_credential_path,
    get_profile_credentials,
    list_profiles,
    load_credentials,
    profile_exists,
    save_credentials,
)


@pytest.fixture
def temp_config_dir():
    """Temporary config directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch.dict(os.environ, {"CLI_ONPREM_CONFIG_DIR": tmpdir}):
            yield Path(tmpdir)


def test_get_config_dir_default():
    """Test get_config_dir returns home/.cli-onprem by default."""
    with patch.dict(os.environ, {}, clear=True):
        # 환경변수가 없을 때
        config_dir = get_config_dir()
        assert config_dir == Path.home() / DEFAULT_CONFIG_DIR_NAME


def test_get_config_dir_from_env():
    """Test get_config_dir respects CLI_ONPREM_CONFIG_DIR environment variable."""
    test_dir = "/tmp/test_config"
    with patch.dict(os.environ, {"CLI_ONPREM_CONFIG_DIR": test_dir}):
        config_dir = get_config_dir()
        assert config_dir == Path(test_dir)


def test_get_credential_path():
    """Test get_credential_path returns credential.yaml in config dir."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch.dict(os.environ, {"CLI_ONPREM_CONFIG_DIR": tmpdir}):
            cred_path = get_credential_path()
            assert cred_path == Path(tmpdir) / "credential.yaml"


def test_ensure_config_directory_creates_dir(temp_config_dir):
    """Test ensure_config_directory creates directory if it doesn't exist."""
    # 디렉터리가 아직 없는 상태
    if temp_config_dir.exists():
        temp_config_dir.rmdir()

    config_dir = ensure_config_directory()

    assert config_dir.exists()
    assert config_dir.is_dir()


def test_ensure_config_directory_existing_dir(temp_config_dir):
    """Test ensure_config_directory works with existing directory."""
    # 디렉터리가 이미 존재
    temp_config_dir.mkdir(exist_ok=True)

    config_dir = ensure_config_directory()

    assert config_dir.exists()
    assert config_dir == temp_config_dir


def test_load_credentials_nonexistent_file(temp_config_dir):
    """Test load_credentials returns empty dict when file doesn't exist."""
    credentials = load_credentials()

    assert credentials == {}


def test_load_credentials_empty_file(temp_config_dir):
    """Test load_credentials handles empty YAML file."""
    cred_path = get_credential_path()
    cred_path.write_text("")

    credentials = load_credentials()

    assert credentials == {}


def test_load_credentials_valid_file(temp_config_dir):
    """Test load_credentials reads valid credential file."""
    cred_path = get_credential_path()
    test_data = {
        "profile1": {
            "aws_access_key": "AKIATEST",
            "aws_secret_key": "secret123",
            "region": "us-east-1",
        }
    }
    with open(cred_path, "w") as f:
        yaml.dump(test_data, f)

    credentials = load_credentials()

    assert credentials == test_data


def test_load_credentials_invalid_yaml(temp_config_dir):
    """Test load_credentials raises CLIError on invalid YAML."""
    cred_path = get_credential_path()
    cred_path.write_text("invalid: yaml: content: [")

    with pytest.raises(CLIError) as exc_info:
        load_credentials()

    assert "자격증명 파일 로드 실패" in str(exc_info.value)


def test_save_credentials_creates_file(temp_config_dir):
    """Test save_credentials creates credential file."""
    test_data = {
        "test_profile": {
            "aws_access_key": "AKIATEST",
            "aws_secret_key": "secret",
        }
    }

    save_credentials(test_data)

    cred_path = get_credential_path()
    assert cred_path.exists()

    with open(cred_path) as f:
        loaded = yaml.safe_load(f)
    assert loaded == test_data


def test_save_credentials_sets_file_permissions(temp_config_dir):
    """Test save_credentials sets file permissions to 600."""
    test_data = {"profile": {"key": "value"}}

    save_credentials(test_data)

    cred_path = get_credential_path()
    stat = os.stat(cred_path)
    # 0o600 = rw-------
    assert oct(stat.st_mode)[-3:] == "600"


def test_get_profile_credentials_no_file(temp_config_dir):
    """Test get_profile_credentials raises error when no credential file."""
    with pytest.raises(CLIError) as exc_info:
        get_profile_credentials("test")

    assert "자격증명 파일이 없습니다" in str(exc_info.value)
    assert "init-credential" in str(exc_info.value)


def test_get_profile_credentials_profile_not_found(temp_config_dir):
    """Test get_profile_credentials raises error for non-existent profile."""
    save_credentials({"other_profile": {}})

    with pytest.raises(CLIError) as exc_info:
        get_profile_credentials("nonexistent")

    assert "존재하지 않습니다" in str(exc_info.value)


def test_get_profile_credentials_missing_aws_keys(temp_config_dir):
    """Test get_profile_credentials checks for required AWS keys."""
    save_credentials({"test": {"region": "us-east-1"}})

    with pytest.raises(CLIError) as exc_info:
        get_profile_credentials("test", check_aws=True)

    assert "AWS 자격증명이 없습니다" in str(exc_info.value)


def test_get_profile_credentials_missing_bucket(temp_config_dir):
    """Test get_profile_credentials checks for bucket when requested."""
    save_credentials(
        {
            "test": {
                "aws_access_key": "AKIATEST",
                "aws_secret_key": "secret",
            }
        }
    )

    with pytest.raises(CLIError) as exc_info:
        get_profile_credentials("test", check_bucket=True)

    assert "버킷이 설정되지 않았습니다" in str(exc_info.value)


def test_get_profile_credentials_success(temp_config_dir):
    """Test get_profile_credentials returns credentials successfully."""
    test_creds = {
        "test": {
            "aws_access_key": "AKIATEST",
            "aws_secret_key": "secret123",
            "region": "us-west-2",
            "bucket": "my-bucket",
        }
    }
    save_credentials(test_creds)

    result = get_profile_credentials("test", check_aws=True, check_bucket=True)

    assert result == test_creds["test"]
    assert isinstance(result["aws_access_key"], str)


def test_get_profile_credentials_no_checks(temp_config_dir):
    """Test get_profile_credentials without validation checks."""
    save_credentials({"test": {"region": "us-east-1"}})

    result = get_profile_credentials("test", check_aws=False, check_bucket=False)

    assert result == {"region": "us-east-1"}


def test_create_or_update_profile_new_profile(temp_config_dir):
    """Test create_or_update_profile creates new profile."""
    create_or_update_profile(
        "new_profile",
        aws_access_key="AKIANEW",
        aws_secret_key="newsecret",
        region="ap-northeast-2",
    )

    credentials = load_credentials()
    assert "new_profile" in credentials
    assert credentials["new_profile"]["aws_access_key"] == "AKIANEW"
    assert credentials["new_profile"]["region"] == "ap-northeast-2"


def test_create_or_update_profile_update_existing(temp_config_dir):
    """Test create_or_update_profile updates existing profile."""
    # 기존 프로파일 생성
    save_credentials(
        {
            "existing": {
                "aws_access_key": "AKIAOLD",
                "aws_secret_key": "oldsecret",
            }
        }
    )

    # 업데이트
    create_or_update_profile("existing", region="eu-west-1", bucket="new-bucket")

    credentials = load_credentials()
    assert credentials["existing"]["aws_access_key"] == "AKIAOLD"  # 유지
    assert credentials["existing"]["region"] == "eu-west-1"  # 추가
    assert credentials["existing"]["bucket"] == "new-bucket"  # 추가


def test_create_or_update_profile_partial_update(temp_config_dir):
    """Test create_or_update_profile with partial updates."""
    save_credentials(
        {
            "test": {
                "aws_access_key": "AKIATEST",
                "aws_secret_key": "secret",
                "region": "us-east-1",
            }
        }
    )

    # region만 업데이트
    create_or_update_profile("test", region="us-west-2")

    credentials = load_credentials()
    assert credentials["test"]["aws_access_key"] == "AKIATEST"  # 유지
    assert credentials["test"]["region"] == "us-west-2"  # 변경


def test_list_profiles_empty(temp_config_dir):
    """Test list_profiles returns empty list when no profiles exist."""
    profiles = list_profiles()

    assert profiles == []


def test_list_profiles_with_data(temp_config_dir):
    """Test list_profiles returns all profile names."""
    save_credentials(
        {
            "profile1": {},
            "profile2": {},
            "profile3": {},
        }
    )

    profiles = list_profiles()

    assert len(profiles) == 3
    assert "profile1" in profiles
    assert "profile2" in profiles
    assert "profile3" in profiles


def test_profile_exists_true(temp_config_dir):
    """Test profile_exists returns True for existing profile."""
    save_credentials({"existing": {}})

    assert profile_exists("existing") is True


def test_profile_exists_false(temp_config_dir):
    """Test profile_exists returns False for non-existent profile."""
    save_credentials({"other": {}})

    assert profile_exists("nonexistent") is False


def test_profile_exists_empty_credentials(temp_config_dir):
    """Test profile_exists returns False when no credentials file."""
    assert profile_exists("any") is False


def test_save_credentials_overwrites_existing(temp_config_dir):
    """Test save_credentials overwrites existing file."""
    save_credentials({"old": {}})
    save_credentials({"new": {}})

    credentials = load_credentials()
    assert "old" not in credentials
    assert "new" in credentials
