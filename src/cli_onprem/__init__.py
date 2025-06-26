"""CLI-ONPREM - CLI tool for infrastructure engineers."""

from importlib.metadata import PackageNotFoundError, version

try:
    # 설치된 패키지에서 버전 읽기
    __version__ = version("cli-onprem")
except PackageNotFoundError:
    # 개발 환경에서는 'dev' 버전 사용
    __version__ = "dev"
