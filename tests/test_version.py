"""버전 표시 기능 테스트."""

import re
from importlib.metadata import PackageNotFoundError
from unittest.mock import patch

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
        # 버전 또는 dev 허용
        assert re.match(r"cli-onprem v(\d+\.\d+\.\d+|dev)", result.output.strip())

    def test_version_matches_package(self):
        """__version__이 실제 패키지 버전과 일치하는지 확인."""
        from importlib.metadata import PackageNotFoundError, version

        from cli_onprem import __version__

        try:
            package_version = version("cli-onprem")
            assert __version__ == package_version
        except PackageNotFoundError:
            # 개발 환경에서는 'dev' 버전이어야 함
            assert __version__ == "dev"

    def test_help_shows_version(self):
        """도움말에 버전이 표시되는지 확인."""
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        # 정규식으로 버전 패턴 확인 (하드코딩 X)
        # 버전 또는 dev 허용
        assert re.search(r"v(\d+\.\d+\.\d+|dev)", result.output)

    def test_version_dev_fallback(self):
        """패키지가 설치되지 않았을 때 dev 버전 표시 확인."""
        with patch("importlib.metadata.version") as mock_version:
            mock_version.side_effect = PackageNotFoundError("Package not found")
            # __init__.py를 다시 import하여 버전 로직 재실행
            import sys

            # 캐시된 모듈 제거
            if "cli_onprem" in sys.modules:
                del sys.modules["cli_onprem"]

            import cli_onprem

            assert cli_onprem.__version__ == "dev"
