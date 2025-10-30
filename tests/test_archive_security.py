"""Archive 서비스의 보안 테스트.

Shell injection 취약점 방어를 검증합니다.
"""

from pathlib import Path

import pytest

from cli_onprem.core.errors import CommandError
from cli_onprem.services.archive import calculate_sha256_manifest, merge_files


def test_calculate_sha256_no_shell_injection(tmp_path: Path) -> None:
    """Shell injection 시도가 실패하는지 확인 - SHA256 계산."""
    # 악의적인 패턴 시도
    malicious_patterns = [
        "*.tar; rm -rf /",
        "*.tar && cat /etc/passwd",
        "*.tar | whoami",
        "*.tar`whoami`",
        "*.tar$(whoami)",
    ]

    for pattern in malicious_patterns:
        with pytest.raises(CommandError, match="패턴과 일치하는 파일이 없습니다"):
            calculate_sha256_manifest(tmp_path, pattern)


def test_calculate_sha256_path_traversal(tmp_path: Path) -> None:
    """경로 순회(path traversal) 시도 방어."""
    # 상위 디렉터리 접근 시도
    malicious_patterns = [
        "../../../etc/passwd",
        "../../*",
    ]

    for pattern in malicious_patterns:
        # 패턴이 파일을 찾지 못하거나, 찾더라도 안전하게 처리됨
        try:
            result = calculate_sha256_manifest(tmp_path, pattern)
            # 결과가 있다면 tmp_path 외부 파일이 아닌지 확인
            for filename, _ in result:
                assert not filename.startswith("..")
        except CommandError as e:
            # 파일이 없다는 에러는 정상
            assert "패턴과 일치하는 파일이 없습니다" in str(e)


def test_calculate_sha256_correct_behavior(tmp_path: Path) -> None:
    """SHA256 계산이 올바르게 작동하는지 확인."""
    # 테스트 파일 생성
    file1 = tmp_path / "test1.txt"
    file1.write_bytes(b"Hello World")

    file2 = tmp_path / "test2.txt"
    file2.write_bytes(b"Python Security")

    # SHA256 계산
    manifest = calculate_sha256_manifest(tmp_path, "*.txt")

    # 검증
    assert len(manifest) == 2

    # 파일명 확인
    filenames = [name for name, _ in manifest]
    assert "test1.txt" in filenames
    assert "test2.txt" in filenames

    # 해시 길이 확인 (SHA256은 64자)
    for _, hash_value in manifest:
        assert len(hash_value) == 64
        assert all(c in "0123456789abcdef" for c in hash_value)


def test_calculate_sha256_empty_directory(tmp_path: Path) -> None:
    """빈 디렉터리나 매칭되지 않는 패턴 처리."""
    with pytest.raises(CommandError, match="패턴과 일치하는 파일이 없습니다"):
        calculate_sha256_manifest(tmp_path, "*.nonexistent")


def test_merge_files_no_shell_injection(tmp_path: Path) -> None:
    """Shell injection 시도가 실패하는지 확인 - 파일 병합."""
    output = tmp_path / "output.bin"

    # 악의적인 패턴 시도
    malicious_patterns = [
        "*.part; rm -rf /",
        "*.part && cat /etc/passwd",
        "*.part | whoami",
    ]

    for pattern in malicious_patterns:
        with pytest.raises(CommandError, match="병합할 파일이 없습니다"):
            merge_files(tmp_path, output, pattern)


def test_merge_files_correct_behavior(tmp_path: Path) -> None:
    """파일 병합이 올바르게 작동하는지 확인."""
    # 분할 파일 생성
    part1 = tmp_path / "0000.part"
    part1.write_bytes(b"Part 1 content\n")

    part2 = tmp_path / "0001.part"
    part2.write_bytes(b"Part 2 content\n")

    part3 = tmp_path / "0002.part"
    part3.write_bytes(b"Part 3 content\n")

    # 병합
    output = tmp_path / "merged.bin"
    merge_files(tmp_path, output, "*.part")

    # 검증
    assert output.exists()

    content = output.read_bytes()
    expected = b"Part 1 content\nPart 2 content\nPart 3 content\n"
    assert content == expected


def test_merge_files_large_files(tmp_path: Path) -> None:
    """큰 파일 병합이 정상 작동하는지 확인 (메모리 효율성)."""
    # 10MB 파일 2개 생성
    chunk_size = 1024 * 1024  # 1MB
    large_data = b"X" * chunk_size

    part1 = tmp_path / "large1.part"
    with open(part1, "wb") as f:
        for _ in range(10):  # 10MB
            f.write(large_data)

    part2 = tmp_path / "large2.part"
    with open(part2, "wb") as f:
        for _ in range(10):  # 10MB
            f.write(large_data)

    # 병합
    output = tmp_path / "merged.bin"
    merge_files(tmp_path, output, "*.part")

    # 크기 검증 (20MB)
    assert output.stat().st_size == 20 * chunk_size


def test_merge_files_empty_directory(tmp_path: Path) -> None:
    """병합할 파일이 없을 때 에러 발생."""
    output = tmp_path / "output.bin"

    with pytest.raises(CommandError, match="병합할 파일이 없습니다"):
        merge_files(tmp_path, output, "*.nonexistent")


def test_special_characters_in_filenames(tmp_path: Path) -> None:
    """특수 문자가 포함된 파일명 처리."""
    # 특수 문자를 포함한 파일 생성
    special_files = [
        "file with spaces.txt",
        "file-with-dashes.txt",
        "file_with_underscores.txt",
        "file.multiple.dots.txt",
    ]

    for filename in special_files:
        (tmp_path / filename).write_bytes(b"test content")

    # SHA256 계산
    manifest = calculate_sha256_manifest(tmp_path, "*.txt")

    # 모든 파일이 처리되었는지 확인
    assert len(manifest) == len(special_files)

    found_names = [name for name, _ in manifest]
    for expected in special_files:
        assert expected in found_names


def test_unicode_filenames(tmp_path: Path) -> None:
    """유니코드 파일명 처리."""
    # 한글 파일명
    korean_file = tmp_path / "한글파일.txt"
    korean_file.write_bytes(b"Korean content")

    # SHA256 계산
    manifest = calculate_sha256_manifest(tmp_path, "*.txt")

    assert len(manifest) == 1
    assert manifest[0][0] == "한글파일.txt"
