# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

cli-onprem is a Typer-based Python CLI tool that automates repetitive tasks for infrastructure engineers. It provides commands for Docker image management, Helm chart processing, S3 synchronization, and FAT32-compatible file splitting.

## Development Commands

```bash
# Install dependencies (using uv)
uv sync --locked --all-extras --dev

# Install pre-commit hooks
pre-commit install

# Run all tests
pytest

# Run tests with coverage
pytest --cov

# Run a specific test
pytest tests/test_docker_tar.py::test_function_name

# Build the package
build

# Type checking
mypy src/

# Linting
ruff check src/

# Format code
black src/

# Install locally for testing
pipx install -e . --force
```

## Architecture

The project follows a clean layered architecture with clear separation of concerns:

```
src/cli_onprem/
├── commands/      # CLI interface layer (thin, orchestration-focused)
├── services/      # Business logic layer (domain-specific operations)
├── utils/         # Pure utility functions (no business logic)
└── core/          # Framework concerns (errors, logging, types)
```

### Key Architectural Patterns

1. **Modular Command Structure**: Each command is an independent Typer app in `src/cli_onprem/commands/`
2. **Dynamic Command Loading**: Commands are lazily loaded via `get_command()` in `__main__.py` to minimize startup time
3. **Functional Programming**: Emphasis on pure functions with explicit parameters, especially in utils layer
4. **Type Safety**: Comprehensive type hints using TypedDict and typing throughout the codebase
5. **Rich CLI Output**: Uses Rich library for progress bars, tables, and formatted output
6. **Error Handling**: Centralized error types (CustomError, ErrorContext) in core/errors.py
7. **Autocompletion Support**: Commands implement shell autocompletion where relevant

### Service Layer Responsibilities

- `docker.py`: Docker API interactions, image management
- `helm.py`: Helm chart parsing, template rendering
- `s3.py`: AWS S3 operations, credential management
- `archive.py`: Tar file operations, compression handling
- `credential.py`: AWS credential profile management

## Command Implementation Pattern

When adding a new command:
1. Create a new file in `src/cli_onprem/commands/`
2. Define a Typer app and implement the command function
3. Register it in `__main__.py` using the `get_command()` pattern

Example structure:
```python
import typer
from typing_extensions import Annotated
from rich.console import Console

app = typer.Typer(help="Command description")
console = Console()

@app.command()
def command_name(
    argument: Annotated[str, typer.Argument(help="Description")],
    option: Annotated[str, typer.Option(help="Description")] = "default"
):
    """Command description."""
    # 1. Validate inputs
    # 2. Call service layer functions
    # 3. Handle errors with try/except
    # 4. Display output using console
```

## Testing Patterns

Tests follow these conventions:
- Located in `tests/` with naming pattern `test_<command_name>.py`
- Extended tests use `test_<command_name>_extended.py` pattern
- Mock external dependencies (Docker daemon, AWS services)
- Use pytest fixtures for common test data
- Test both success and error paths

Example test structure:
```python
def test_function_name(mock_dependency):
    """Test description."""
    # Arrange
    mock_dependency.return_value = expected_data
    
    # Act
    result = function_under_test(params)
    
    # Assert
    assert result == expected_result
    mock_dependency.assert_called_with(expected_params)
```

## Release Process

The project uses semantic-release with the Angular commit convention:
- `feat:` new features (minor version bump)
- `fix:` bug fixes (patch version bump)
- `perf:` performance improvements (patch version bump)
- `docs:` documentation only changes
- `style:` formatting, missing semicolons, etc.
- `refactor:` code changes that neither fix bugs nor add features
- `test:` adding missing tests
- `chore:` maintenance tasks
- `ci:` CI configuration changes
- `build:` build system changes

Releases are automated via GitHub Actions when changes are pushed to the main branch.