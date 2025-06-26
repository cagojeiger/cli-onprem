"""CLI-ONPREM - CLI tool for infrastructure engineers."""

import os
import sys
from importlib.metadata import PackageNotFoundError, version
from typing import Any, Dict

try:
    # 설치된 패키지에서 버전 읽기
    __version__ = version("cli-onprem")
except PackageNotFoundError:
    # 개발 환경에서 pyproject.toml에서 직접 읽기
    if sys.version_info >= (3, 11):
        import tomllib
    else:
        try:
            import tomli as tomllib  # type: ignore[import-not-found]
        except ImportError:
            tomllib = None  # type: ignore[assignment]

    pyproject_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "pyproject.toml"
    )
    if os.path.exists(pyproject_path) and tomllib is not None:
        with open(pyproject_path, "rb") as f:
            data: Dict[str, Any] = tomllib.load(f)
            __version__ = data["project"]["version"]
    else:
        __version__ = "unknown"
