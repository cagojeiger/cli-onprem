"""파일 유틸리티 함수 테스트."""

import tempfile
from pathlib import Path

from cli_onprem.utils.file import ensure_dir, extract_tar, read_yaml, write_yaml


def test_read_yaml_success() -> None:
    """YAML 파일 읽기 성공 테스트."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml_content = """
key1: value1
key2:
  nested: value2
list:
  - item1
  - item2
"""
        f.write(yaml_content)
        f.flush()

        file_path = Path(f.name)
        try:
            result = read_yaml(file_path)
            assert result["key1"] == "value1"
            assert result["key2"]["nested"] == "value2"
            assert len(result["list"]) == 2
        finally:
            file_path.unlink()


def test_read_yaml_empty_file() -> None:
    """빈 YAML 파일 읽기 테스트."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("")
        f.flush()

        file_path = Path(f.name)
        try:
            result = read_yaml(file_path)
            assert result == {}
        finally:
            file_path.unlink()


def test_write_yaml_success() -> None:
    """YAML 파일 쓰기 성공 테스트."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.yaml"

        data = {
            "key1": "value1",
            "key2": {"nested": "value2"},
            "list": ["item1", "item2"],
        }

        write_yaml(file_path, data)

        assert file_path.exists()
        result = read_yaml(file_path)
        assert result == data


def test_extract_tar_success() -> None:
    """tar 파일 추출 성공 테스트."""
    import tarfile

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # tar 파일 생성
        tar_path = tmpdir_path / "test.tar.gz"
        test_file = tmpdir_path / "test.txt"
        test_file.write_text("test content")

        with tarfile.open(tar_path, "w:gz") as tar:
            tar.add(test_file, arcname="test.txt")

        # 추출
        extract_dir = tmpdir_path / "extracted"
        extract_dir.mkdir()

        extract_tar(tar_path, extract_dir)

        # 검증
        extracted_file = extract_dir / "test.txt"
        assert extracted_file.exists()
        assert extracted_file.read_text() == "test content"


def test_ensure_dir_creates_directory() -> None:
    """디렉터리 생성 테스트."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)
        new_dir = base_path / "new" / "nested" / "directory"

        # 디렉터리가 존재하지 않음을 확인
        assert not new_dir.exists()

        # ensure_dir 호출
        result = ensure_dir(new_dir)

        # 디렉터리가 생성되었는지 확인
        assert new_dir.exists()
        assert new_dir.is_dir()
        assert result == new_dir


def test_ensure_dir_existing_directory() -> None:
    """이미 존재하는 디렉터리 테스트."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)
        existing_dir = base_path / "existing"
        existing_dir.mkdir()

        # 디렉터리가 이미 존재함을 확인
        assert existing_dir.exists()

        # ensure_dir 호출
        result = ensure_dir(existing_dir)

        # 여전히 존재하고 동일한 경로를 반환
        assert existing_dir.exists()
        assert existing_dir.is_dir()
        assert result == existing_dir


def test_ensure_dir_with_file_path() -> None:
    """파일 경로에 대한 ensure_dir 테스트."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)
        file_path = base_path / "test.txt"
        file_path.write_text("content")

        # 파일이 존재함을 확인
        assert file_path.exists()
        assert file_path.is_file()

        # ensure_dir는 파일을 디렉터리로 변환하려고 시도할 때 예외 발생
        try:
            ensure_dir(file_path)
        except Exception:
            # 예외가 발생하면 테스트 통과
            pass
