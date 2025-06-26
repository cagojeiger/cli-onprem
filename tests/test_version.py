"""버전 표시 기능 테스트."""

import re
from importlib.metadata import PackageNotFoundError
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from cli_onprem.__main__ import app


class TestVersion:
    """버전 관련 테스트."""

    def test_version_option(self):
        """--version 옵션이 버전을 표시하는지 확인."""
        runner = CliRunner()
        result = runner.invoke(app, ["--version"])

        # 버전 형식 검증 (하드코딩 X)
        assert result.exit_code == 0
        assert re.match(r"cli-onprem v\d+\.\d+\.\d+", result.output.strip())

    def test_version_matches_package(self):
        """__version__이 실제 패키지 버전과 일치하는지 확인."""
        from importlib.metadata import PackageNotFoundError, version

        from cli_onprem import __version__

        try:
            package_version = version("cli-onprem")
            assert __version__ == package_version
        except PackageNotFoundError:
            # 개발 환경에서는 pyproject.toml의 버전과 비교
            import os
            import sys

            if sys.version_info >= (3, 11):
                import tomllib
            else:
                try:
                    import tomli as tomllib  # type: ignore[import-not-found]
                except ImportError:
                    pytest.skip("tomli not available for Python < 3.11")

            pyproject_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "pyproject.toml",
            )
            if os.path.exists(pyproject_path):
                with open(pyproject_path, "rb") as f:
                    data = tomllib.load(f)
                    expected_version = data["project"]["version"]
                    assert __version__ == expected_version
            else:
                pytest.skip("Cannot find package version or pyproject.toml")

    def test_help_shows_version(self):
        """도움말에 버전이 표시되는지 확인."""
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        # 정규식으로 버전 패턴 확인 (하드코딩 X)
        assert re.search(r"v\d+\.\d+\.\d+", result.output)

    def test_version_unknown_fallback(self):
        """패키지가 설치되지 않았을 때 unknown 버전 표시 확인."""
        with patch("importlib.metadata.version") as mock_version:
            mock_version.side_effect = PackageNotFoundError("Package not found")
            with patch("os.path.exists", return_value=False):
                # __init__.py를 다시 import하여 버전 로직 재실행
                import sys

                # 캐시된 모듈 제거
                if "cli_onprem" in sys.modules:
                    del sys.modules["cli_onprem"]

                import cli_onprem

                assert cli_onprem.__version__ == "unknown"
