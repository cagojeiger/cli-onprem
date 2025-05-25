"""자격증명 관리 관련 비즈니스 로직."""

import os
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from cli_onprem.core.errors import CLIError
from cli_onprem.core.logging import get_logger

logger = get_logger("services.credential")

DEFAULT_PROFILE = "default_profile"
DEFAULT_CONFIG_DIR_NAME = ".cli-onprem"


def get_config_dir() -> Path:
    """설정 디렉터리 경로를 반환합니다.

    환경변수 CLI_ONPREM_CONFIG_DIR가 설정되어 있으면 해당 경로를 사용하고,
    없으면 ~/.cli-onprem을 사용합니다.

    Returns:
        설정 디렉터리 경로
    """
    if config_dir_env := os.environ.get("CLI_ONPREM_CONFIG_DIR"):
        return Path(config_dir_env)
    return Path.home() / DEFAULT_CONFIG_DIR_NAME


def get_credential_path() -> Path:
    """자격증명 파일 경로를 반환합니다.

    Returns:
        자격증명 파일 경로
    """
    return get_config_dir() / "credential.yaml"


def ensure_config_directory() -> Path:
    """설정 디렉터리가 존재하는지 확인하고 없으면 생성합니다.

    Returns:
        설정 디렉터리 경로
    """
    config_dir = get_config_dir()
    if not config_dir.exists():
        logger.info(f"설정 디렉터리 생성: {config_dir}")
        config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def load_credentials() -> Dict[str, Dict[str, str]]:
    """저장된 자격증명을 로드합니다.

    Returns:
        프로파일별 자격증명 딕셔너리

    Raises:
        CLIError: 자격증명 파일 로드 실패
    """
    credential_path = get_credential_path()

    if not credential_path.exists():
        logger.debug("자격증명 파일이 없습니다.")
        return {}

    try:
        with open(credential_path) as f:
            credentials = yaml.safe_load(f) or {}
            logger.debug(f"{len(credentials)}개의 프로파일 로드됨")
            return credentials
    except Exception as e:
        raise CLIError(f"자격증명 파일 로드 실패: {e}") from e


def save_credentials(credentials: Dict[str, Dict[str, str]]) -> None:
    """자격증명을 파일에 저장합니다.

    Args:
        credentials: 프로파일별 자격증명 딕셔너리

    Raises:
        CLIError: 자격증명 파일 저장 실패
    """
    ensure_config_directory()
    credential_path = get_credential_path()

    try:
        with open(credential_path, "w") as f:
            yaml.dump(credentials, f, default_flow_style=False)

        # 파일 권한을 600으로 설정 (소유자만 읽기/쓰기 가능)
        os.chmod(credential_path, 0o600)
        logger.info(f"자격증명 저장됨: {credential_path}")
    except Exception as e:
        raise CLIError(f"자격증명 파일 저장 실패: {e}") from e


def get_profile_credentials(
    profile: str, check_aws: bool = True, check_bucket: bool = False
) -> Dict[str, str]:
    """특정 프로파일의 자격증명을 가져옵니다.

    Args:
        profile: 프로파일 이름
        check_aws: AWS 자격증명 존재 여부 확인
        check_bucket: 버킷 설정 여부 확인

    Returns:
        자격증명 딕셔너리

    Raises:
        CLIError: 프로파일이 없거나 필수 정보가 부족한 경우
    """
    credentials = load_credentials()

    if not credentials:
        raise CLIError(
            "자격증명 파일이 없습니다. "
            "먼저 's3-share init-credential' 명령을 실행하세요."
        )

    if profile not in credentials:
        raise CLIError(f"프로파일 '{profile}'이(가) 존재하지 않습니다.")

    profile_creds = credentials[profile]

    if check_aws:
        if not profile_creds.get("aws_access_key") or not profile_creds.get(
            "aws_secret_key"
        ):
            raise CLIError(
                f"프로파일 '{profile}'에 AWS 자격증명이 없습니다. "
                f"먼저 's3-share init-credential' 명령을 실행하세요."
            )

    if check_bucket and not profile_creds.get("bucket"):
        raise CLIError(
            f"프로파일 '{profile}'에 버킷이 설정되지 않았습니다. "
            f"먼저 's3-share init-bucket' 명령을 실행하세요."
        )

    # 문자열 타입으로 변환하여 반환
    result: Dict[str, str] = {}
    for key, value in profile_creds.items():
        result[key] = str(value)

    return result


def create_or_update_profile(
    profile: str,
    aws_access_key: Optional[str] = None,
    aws_secret_key: Optional[str] = None,
    region: Optional[str] = None,
    bucket: Optional[str] = None,
    prefix: Optional[str] = None,
) -> None:
    """프로파일을 생성하거나 업데이트합니다.

    Args:
        profile: 프로파일 이름
        aws_access_key: AWS Access Key
        aws_secret_key: AWS Secret Key
        region: AWS 리전
        bucket: S3 버킷
        prefix: S3 프리픽스
    """
    credentials = load_credentials()

    if profile not in credentials:
        credentials[profile] = {}
        logger.info(f"새 프로파일 생성: {profile}")
    else:
        logger.info(f"기존 프로파일 업데이트: {profile}")

    # 제공된 값만 업데이트
    if aws_access_key is not None:
        credentials[profile]["aws_access_key"] = aws_access_key
    if aws_secret_key is not None:
        credentials[profile]["aws_secret_key"] = aws_secret_key
    if region is not None:
        credentials[profile]["region"] = region
    if bucket is not None:
        credentials[profile]["bucket"] = bucket
    if prefix is not None:
        credentials[profile]["prefix"] = prefix

    save_credentials(credentials)


def list_profiles() -> List[str]:
    """저장된 프로파일 목록을 반환합니다.

    Returns:
        프로파일 이름 리스트
    """
    credentials = load_credentials()
    return list(credentials.keys())


def profile_exists(profile: str) -> bool:
    """프로파일이 존재하는지 확인합니다.

    Args:
        profile: 프로파일 이름

    Returns:
        존재 여부
    """
    credentials = load_credentials()
    return profile in credentials
