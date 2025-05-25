"""아카이브(압축 및 분할) 관련 비즈니스 로직."""

import re
import subprocess
from pathlib import Path
from typing import List, Tuple

from cli_onprem.core.errors import CommandError
from cli_onprem.core.logging import get_logger

logger = get_logger("services.archive")


def create_tar_archive(input_path: Path, output_path: Path, parent_dir: Path) -> None:
    """파일 또는 디렉터리를 tar.gz로 압축합니다.

    Args:
        input_path: 압축할 파일 또는 디렉터리 경로
        output_path: 출력 tar.gz 파일 경로
        parent_dir: 상대 경로 계산을 위한 부모 디렉터리

    Raises:
        CommandError: 압축 실패
    """
    logger.info(f"{input_path} 압축 중...")

    relative_path = input_path.relative_to(parent_dir)
    cmd = ["tar", "-czvf", str(output_path), "-C", str(parent_dir), str(relative_path)]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"압축 완료: {output_path}")
    except subprocess.CalledProcessError as e:
        raise CommandError(f"압축 실패: {e.stderr}") from e


def split_file(
    file_path: Path, chunk_size: str, output_dir: Path, prefix: str = ""
) -> List[Path]:
    """파일을 지정된 크기로 분할합니다.

    Args:
        file_path: 분할할 파일 경로
        chunk_size: 조각 크기 (예: "3G", "500M")
        output_dir: 출력 디렉터리
        prefix: 출력 파일 접두사

    Returns:
        생성된 조각 파일 경로 목록

    Raises:
        CommandError: 파일 분할 실패
    """
    logger.info(f"{file_path}을 {chunk_size} 크기로 분할 중...")

    # 파일 크기를 바이트로 변환
    file_size = file_path.stat().st_size

    # chunk_size를 바이트로 변환 (예: "3G" -> 3221225472)
    match = re.match(r"(\d+)([KMGT]?)", chunk_size.upper())
    if not match:
        raise CommandError(f"잘못된 크기 형식: {chunk_size}")

    size_num = int(match.group(1))
    size_unit = match.group(2) or "B"
    multipliers = {"B": 1, "K": 1024, "M": 1024**2, "G": 1024**3, "T": 1024**4}
    chunk_size_bytes = size_num * multipliers[size_unit]

    # 파일이 chunk_size보다 작으면 분할하지 않고 그대로 복사
    if file_size <= chunk_size_bytes:
        logger.info(f"파일 크기가 {chunk_size}보다 작아 분할하지 않습니다.")
        dest_path = output_dir / "0000.part"
        import shutil

        shutil.copy2(file_path, dest_path)
        logger.info("파일 분할 완료: 1개 조각")
        return [dest_path]

    output_prefix = str(output_dir / prefix) if prefix else str(output_dir) + "/"
    cmd = ["split", "-b", chunk_size, str(file_path), output_prefix]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)

        # 생성된 파일들 찾기
        parts = sorted(output_dir.glob(f"{prefix}*" if prefix else "*"))

        # 파일명을 숫자 형식으로 변경
        renamed_parts = []
        for i, part in enumerate(parts):
            if not part.name.endswith(".part"):
                new_name = output_dir / f"{i:04d}.part"
                part.rename(new_name)
                renamed_parts.append(new_name)
            else:
                renamed_parts.append(part)

        logger.info(f"파일 분할 완료: {len(renamed_parts)}개 조각")
        return renamed_parts

    except subprocess.CalledProcessError as e:
        raise CommandError(f"파일 분할 실패: {e.stderr}") from e


def calculate_sha256_manifest(
    directory: Path, pattern: str = "*"
) -> List[Tuple[str, str]]:
    """디렉터리 내 파일들의 SHA256 해시를 계산합니다.

    Args:
        directory: 대상 디렉터리
        pattern: 파일 패턴 (기본값: "*")

    Returns:
        (파일명, 해시값) 튜플 리스트

    Raises:
        CommandError: 해시 계산 실패
    """
    logger.info(f"{directory} 내 파일들의 SHA256 해시 계산 중...")

    cmd = f"cd {directory} && sha256sum {pattern}"

    try:
        result = subprocess.run(
            ["sh", "-c", cmd], check=True, capture_output=True, text=True
        )

        manifest = []
        for line in result.stdout.strip().split("\n"):
            if line:
                hash_value, filename = line.split(None, 1)
                manifest.append((filename, hash_value))

        logger.info(f"해시 계산 완료: {len(manifest)}개 파일")
        return manifest

    except subprocess.CalledProcessError as e:
        raise CommandError(f"해시 계산 실패: {e.stderr}") from e


def write_manifest_file(manifest: List[Tuple[str, str]], output_path: Path) -> None:
    """SHA256 매니페스트 파일을 작성합니다.

    Args:
        manifest: (파일명, 해시값) 튜플 리스트
        output_path: 출력 파일 경로
    """
    with open(output_path, "w") as f:
        for filename, hash_value in manifest:
            f.write(f"{hash_value}  {filename}\n")

    logger.info(f"매니페스트 파일 생성: {output_path}")


def verify_manifest(manifest_path: Path) -> None:
    """SHA256 매니페스트를 검증합니다.

    Args:
        manifest_path: 매니페스트 파일 경로

    Raises:
        CommandError: 검증 실패
    """
    logger.info("조각 무결성 검증 중...")

    working_dir = manifest_path.parent
    cmd = ["sha256sum", "-c", manifest_path.name]

    try:
        subprocess.run(
            cmd, check=True, cwd=str(working_dir), capture_output=True, text=True
        )
        logger.info("무결성 검증 완료")
    except subprocess.CalledProcessError as e:
        raise CommandError(f"무결성 검증 실패: {e.stderr}") from e


def merge_files(parts_dir: Path, output_path: Path, pattern: str = "*") -> None:
    """분할된 파일들을 병합합니다.

    Args:
        parts_dir: 조각 파일들이 있는 디렉터리
        output_path: 출력 파일 경로
        pattern: 파일 패턴

    Raises:
        CommandError: 파일 병합 실패
    """
    logger.info("조각 파일 병합 중...")

    cmd = f"cat {parts_dir}/{pattern} > {output_path}"

    try:
        subprocess.run(["sh", "-c", cmd], check=True, capture_output=True, text=True)
        logger.info(f"파일 병합 완료: {output_path}")
    except subprocess.CalledProcessError as e:
        raise CommandError(f"파일 병합 실패: {e.stderr}") from e


def extract_tar_archive(
    archive_path: Path, extract_dir: Path, strip_components: int = 0
) -> None:
    """tar.gz 아카이브를 압축 해제합니다.

    Args:
        archive_path: tar.gz 파일 경로
        extract_dir: 압축 해제할 디렉터리
        strip_components: 제거할 경로 컴포넌트 수

    Raises:
        CommandError: 압축 해제 실패
    """
    logger.info(f"{archive_path} 압축 해제 중...")

    cmd = ["tar", "--no-same-owner", "-xzvf", str(archive_path)]
    if strip_components > 0:
        cmd.extend(["--strip-components", str(strip_components)])

    try:
        subprocess.run(
            cmd, check=True, cwd=str(extract_dir), capture_output=True, text=True
        )
        logger.info("압축 해제 완료")
    except subprocess.CalledProcessError as e:
        raise CommandError(f"압축 해제 실패: {e.stderr}") from e


def get_directory_size_mb(path: Path) -> int:
    """디렉터리 또는 파일의 크기를 MB 단위로 반환합니다.

    Args:
        path: 대상 경로

    Returns:
        크기 (MB)

    Raises:
        CommandError: 크기 계산 실패
    """
    cmd = ["du", "-m", str(path)]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        size_mb = int(result.stdout.split()[0])
        return size_mb
    except subprocess.CalledProcessError as e:
        raise CommandError(f"크기 계산 실패: {e.stderr}") from e
    except (ValueError, IndexError) as e:
        raise CommandError(f"크기 파싱 실패: {e}") from e
