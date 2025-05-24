"""Common test fixtures for CLI-ONPREM tests."""

import pytest
from typer.testing import CliRunner


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def mock_console(mocker):
    """Mock the console for testing."""
    return mocker.patch("rich.console.Console")


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for testing."""
    return tmp_path


@pytest.fixture
def mock_subprocess_run(mocker):
    """Mock subprocess.run for testing."""
    return mocker.patch("subprocess.run")


@pytest.fixture
def mock_boto3_client(mocker):
    """Mock boto3 client for testing."""
    return mocker.patch("boto3.client")


@pytest.fixture
def mock_yaml_file(tmp_path):
    """Create a temporary YAML file for testing."""
    def _create_yaml(filename: str, content: dict):
        import yaml
        file_path = tmp_path / filename
        with open(file_path, "w") as f:
            yaml.dump(content, f)
        return file_path
    return _create_yaml