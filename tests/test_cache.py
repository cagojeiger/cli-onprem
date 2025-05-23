import pathlib
import tempfile
from unittest import mock

from cli_onprem.libs import cache


def test_write_and_read_cache() -> None:
    """write_cache와 read_cache 동작 테스트."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = pathlib.Path(tmpdir)
        with mock.patch.object(cache, "CACHE_DIR", cache_dir):
            cache.write_cache("sample", {"value": 1}, ttl=5)
            data = cache.read_cache("sample")
            assert data is not None
            assert data["data"] == {"value": 1}
            assert data["ttl"] == 5


def test_get_cached_data_without_cache() -> None:
    """캐시가 없을 때 fetch_func 호출 및 파일 저장 확인."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = pathlib.Path(tmpdir)
        with mock.patch.object(cache, "CACHE_DIR", cache_dir):
            fetch_func = mock.Mock(return_value=[1, 2, 3])
            with mock.patch.object(cache, "write_cache") as mock_write:
                result = cache.get_cached_data("sample", fetch_func, ttl=10)
                assert result == [1, 2, 3]
                fetch_func.assert_called_once()
                mock_write.assert_called_once_with("sample", [1, 2, 3], 10)


def test_get_cached_data_with_valid_cache() -> None:
    """유효한 캐시가 있을 때 파일을 그대로 사용함을 확인."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = pathlib.Path(tmpdir)
        with mock.patch.object(cache, "CACHE_DIR", cache_dir):
            with mock.patch("time.time", return_value=1000):
                cache.write_cache("sample", "data", ttl=10)
            with mock.patch("time.time", return_value=1005):
                fetch_func = mock.Mock(return_value="new")
                result = cache.get_cached_data("sample", fetch_func, ttl=10)
                assert result == "data"
                fetch_func.assert_not_called()


def test_get_cached_data_with_expired_cache_background_refresh() -> None:
    """만료된 캐시가 있을 때 백그라운드 갱신이 호출되는지 테스트."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = pathlib.Path(tmpdir)
        with mock.patch.object(cache, "CACHE_DIR", cache_dir):
            with mock.patch("time.time", return_value=1000):
                cache.write_cache("sample", "old", ttl=1)
            with mock.patch("time.time", return_value=1002):
                fetch_func = mock.Mock(return_value="new")
                mock_thread = mock.Mock()
                with mock.patch("threading.Thread", return_value=mock_thread) as cls:
                    result = cache.get_cached_data("sample", fetch_func, ttl=1)
                assert result == "old"
                cls.assert_called_once()
                mock_thread.start.assert_called_once()
                fetch_func.assert_not_called()
