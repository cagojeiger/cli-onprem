"""CLI-ONPREM을 위한 캐시 관리 모듈."""

import json
import os
import pathlib
import threading
import time
from typing import Any, Callable, Dict, Optional, TypeVar

T = TypeVar("T")

CACHE_DIR = pathlib.Path.home() / ".cache" / "cli-onprem"
DEFAULT_TTL = 600  # 10분 (초 단위)


def ensure_cache_dir() -> None:
    """캐시 디렉토리가 존재하는지 확인하고 없으면 생성합니다."""
    if not CACHE_DIR.exists():
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        os.chmod(CACHE_DIR, 0o700)


def get_cache_path(cache_name: str) -> pathlib.Path:
    """캐시 파일의 경로를 반환합니다."""
    ensure_cache_dir()
    return CACHE_DIR / f"{cache_name}.json"


def read_cache(cache_name: str) -> Optional[Dict[str, Any]]:
    """캐시 파일에서 데이터를 읽습니다."""
    cache_path = get_cache_path(cache_name)

    if not cache_path.exists():
        return None

    try:
        with open(cache_path, encoding="utf-8") as f:
            result: Dict[str, Any] = json.load(f)
            return result
    except (json.JSONDecodeError, OSError):
        return None


def write_cache(cache_name: str, data: Any, ttl: int = DEFAULT_TTL) -> None:
    """데이터를 캐시 파일에 저장합니다."""
    cache_path = get_cache_path(cache_name)

    cache_data = {"timestamp": int(time.time()), "data": data, "ttl": ttl}

    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache_data, f)
        os.chmod(cache_path, 0o600)
    except OSError:
        pass


def is_cache_valid(cache_data: Dict[str, Any]) -> bool:
    """캐시가 유효한지 확인합니다."""
    if not cache_data or "timestamp" not in cache_data or "ttl" not in cache_data:
        return False

    current_time = int(time.time())
    result: bool = current_time - cache_data["timestamp"] < cache_data["ttl"]
    return result


def get_cached_data(
    cache_name: str, fetch_func: Callable[[], T], ttl: int = DEFAULT_TTL
) -> T:
    """
    캐시에서 데이터를 가져오거나, 필요시 백그라운드에서 갱신합니다.

    Args:
        cache_name: 캐시 파일 이름
        fetch_func: 캐시가 없거나 만료된 경우 데이터를 가져오는 함수
        ttl: 캐시 유효 시간(초)

    Returns:
        캐시된 데이터 또는 fetch_func의 결과
    """
    cache_data = read_cache(cache_name)

    if cache_data and is_cache_valid(cache_data):
        result1: T = cache_data["data"]
        return result1

    if cache_data:
        update_cache_in_background(cache_name, fetch_func, ttl)
        result2: T = cache_data["data"]
        return result2
    else:
        data = fetch_func()
        write_cache(cache_name, data, ttl)
        return data


def update_cache_in_background(
    cache_name: str, fetch_func: Callable[[], Any], ttl: int = DEFAULT_TTL
) -> None:
    """백그라운드 스레드에서 캐시를 갱신합니다."""

    def _update_cache() -> None:
        try:
            data = fetch_func()
            write_cache(cache_name, data, ttl)
        except Exception:
            pass

    thread = threading.Thread(target=_update_cache, daemon=True)
    thread.start()
