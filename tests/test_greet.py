"""Tests for the greet command."""

from typer.testing import CliRunner

from cli_onprem.__main__ import app

runner = CliRunner()


def test_greet_command_with_name() -> None:
    """Test the greet command with a name argument."""
    result = runner.invoke(app, ["greet", "hello", "User"])
    assert result.exit_code == 0
    assert "Hello, User!" in result.stdout


def test_greet_command_without_name() -> None:
    """Test the greet command without a name argument."""
    result = runner.invoke(app, ["greet", "hello"])
    assert result.exit_code == 0
    assert "Hello, world!" in result.stdout
