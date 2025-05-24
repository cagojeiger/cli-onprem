"""파일 작업 유틸리티."""

import pathlib
import tarfile
from typing import Any, Dict, cast

import yaml


def ensure_dir(path: pathlib.Path) -> pathlib.Path:
    """디렉토리가 존재하도록 보장합니다.

    Args:
        path: 생성할 디렉토리 경로

    Returns:
        생성된 경로
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_yaml(path: pathlib.Path) -> Dict[str, Any]:
    """YAML 파일을 읽습니다.

    Args:
        path: YAML 파일 경로

    Returns:
        파싱된 YAML 데이터
    """
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
        if data is None:
            return {}
        return cast(Dict[str, Any], data)


def write_yaml(path: pathlib.Path, data: Dict[str, Any]) -> None:
    """YAML 파일을 작성합니다.

    Args:
        path: YAML 파일 경로
        data: 저장할 데이터
    """
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, default_flow_style=False)


def extract_tar(archive_path: pathlib.Path, dest_dir: pathlib.Path) -> None:
    """tar 아카이브를 추출합니다.

    Args:
        archive_path: tar 파일 경로
        dest_dir: 추출할 디렉토리
    """
    with tarfile.open(archive_path, "r:*") as tar:
        tar.extractall(dest_dir)
