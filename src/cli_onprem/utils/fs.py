"""파일 시스템 관련 유틸리티 함수."""

import os
from pathlib import Path
from typing import List, Optional


def find_completable_paths(
    pattern: str = "*",
    include_dirs: bool = True,
    include_files: bool = True,
    min_file_size: int = 0,
    base_path: Optional[Path] = None,
) -> List[str]:
    """자동완성을 위한 경로 목록을 찾습니다.

    Args:
        pattern: 파일 패턴
        include_dirs: 디렉터리 포함 여부
        include_files: 파일 포함 여부
        min_file_size: 최소 파일 크기 (바이트)
        base_path: 기준 경로 (기본값: 현재 디렉터리)

    Returns:
        경로 문자열 리스트
    """
    if base_path is None:
        base_path = Path(".")

    matches = []

    for path in base_path.glob(pattern):
        if path.name.startswith("."):
            continue

        if path.is_file() and include_files:
            if path.stat().st_size >= min_file_size:
                matches.append(str(path.relative_to(base_path)))
        elif path.is_dir() and include_dirs:
            matches.append(str(path.relative_to(base_path)))

    return sorted(matches)


def find_pack_directories(base_path: Optional[Path] = None) -> List[str]:
    """유효한 .pack 디렉터리를 찾습니다.

    Args:
        base_path: 기준 경로 (기본값: 현재 디렉터리)

    Returns:
        .pack 디렉터리 경로 리스트
    """
    if base_path is None:
        base_path = Path(".")

    matches = []

    for path in base_path.glob("*.pack"):
        if path.is_dir() and (path / "restore.sh").exists():
            matches.append(str(path.relative_to(base_path)))

    return sorted(matches)


def create_size_marker(directory: Path, size_mb: int) -> None:
    """디렉터리에 크기 마커 파일을 생성합니다.

    Args:
        directory: 대상 디렉터리
        size_mb: 크기 (MB)
    """
    marker_path = directory / f"{size_mb}_MB"
    marker_path.touch()


def generate_restore_script(purge_option: bool = False) -> str:
    """복원 스크립트를 생성합니다.

    Args:
        purge_option: --purge 옵션 포함 여부

    Returns:
        복원 스크립트 내용
    """
    script = """#!/usr/bin/env sh
set -eu

PURGE=0
[ "${1:-}" = "--purge" ] && PURGE=1

PACK_DIR="$(basename "$(pwd)")"

printf "▶ 조각 무결성 검증...\\n"
sha256sum -c manifest.sha256         # 실패 시 즉시 종료

printf "▶ 조각 병합...\\n"
cat parts/* > archive.tar.gz

printf "▶ 압축 해제...\\n"
cd ..
# 원본 파일·디렉터리 복원
tar --no-same-owner -xzvf "$PACK_DIR/archive.tar.gz"

printf "▶ 중간 파일 정리...\\n"
cd "$PACK_DIR"
rm -f archive.tar.gz                 # 병합본 제거

if [ "$PURGE" -eq 1 ]; then
  printf "▶ .pack 폴더 삭제(--purge)...\\n"
  cd ..
  rm -rf "$PACK_DIR"                 # .pack 디렉터리 전체 삭제
fi

printf "🎉 복원 완료\\n"
"""
    return script


def make_executable(file_path: Path) -> None:
    """파일에 실행 권한을 부여합니다.

    Args:
        file_path: 대상 파일 경로
    """
    os.chmod(file_path, 0o755)
