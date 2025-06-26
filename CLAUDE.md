# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

cli_onprem is a Typer-based Python CLI tool that automates repetitive tasks for infrastructure engineers. It provides commands for Docker image management, Helm chart processing, S3 synchronization, and FAT32-compatible file splitting. The project supports both Korean and English, with Korean as the primary language for user-facing text.

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

# Run tests quietly
pytest -q

# Run a specific test
pytest tests/test_docker_tar.py::test_function_name

# Type checking
mypy src/

# Type checking with strict mode
mypy src --strict --no-warn-unused-ignores

# Linting
ruff check src/

# Format code
ruff format src/
# or
black src/

# Run pre-commit on all files
SKIP=uv-lock uv run pre-commit run --all-files

# Build the package
uv run python -m build

# Install locally for testing
pipx install -e . --force

# Upload to TestPyPI
twine upload --repository-url https://test.pypi.org/legacy/ --skip-existing dist/*

# Upload to PyPI
twine upload --skip-existing dist/*

# Run semantic release
semantic-release version
```

## Architecture

The project follows Python's recommended src layout with a clean layered architecture:

```
cli-onprem/                 # Project root
├── src/                    # Source code directory (Python packaging best practice)
│   └── cli_onprem/        # Package directory (underscore for Python imports)
│       ├── commands/      # CLI interface layer (thin, orchestration-focused)
│       ├── services/      # Business logic layer (domain-specific operations)
│       ├── utils/         # Pure utility functions (no business logic)
│       └── core/          # Framework concerns (errors, logging, types)
├── tests/                 # Test files
└── pyproject.toml         # Project configuration
```

Note: The package name `cli-onprem` (with hyphen) is used for PyPI distribution, while the module name `cli_onprem` (with underscore) is used for Python imports. This follows Python naming conventions.

### Key Architectural Patterns

1. **Modular Command Structure**: Each command is an independent Typer app in `src/cli_onprem/commands/`
2. **Dynamic Command Loading**: Commands are lazily loaded via `get_command()` in `__main__.py` using `importlib` to minimize startup time
3. **Functional Programming**: Emphasis on pure functions with explicit parameters, especially in utils layer
4. **Type Safety**: Comprehensive type hints using TypedDict and typing throughout, with `py.typed` marker for PEP 561 compliance
5. **Rich CLI Output**: Uses Rich library for progress bars, tables, and formatted output
6. **Error Handling**: Hierarchical error types (CLIError → CommandError/DependencyError) in core/errors.py
7. **Autocompletion Support**: Commands implement shell autocompletion where relevant
8. **Context Settings**: CLI allows unknown options and extra args globally for flexibility
9. **Bilingual Support**: Korean primary language for user-facing text, English for code

### Service Layer Responsibilities

- `docker.py`: Docker API interactions, image management, platform-specific builds
- `helm.py`: Helm chart parsing, template rendering, image extraction
- `s3.py`: AWS S3 operations, presigned URLs, uses AWS CLI for sync operations
- `archive.py`: Tar file operations, compression, FAT32-compatible splitting
- `credential.py`: AWS credential profile management

### Available Commands

- **docker-tar save**: Pulls and saves Docker images with platform-specific builds
- **helm-local extract-images**: Extracts container image references from Helm charts
- **s3-share**: File sharing via S3 (init-credential, init-bucket, sync, presign)
- **tar-fat32**: Compress and split files for FAT32 (pack, restore)

## Command Implementation Pattern

When adding a new command:
1. Create a new file in `src/cli_onprem/commands/`
2. Define a Typer app and implement the command function
3. Register it in `__main__.py` using the `get_command()` pattern with kebab-case naming

Example structure:
```python
import typer
from typing_extensions import Annotated
from rich.console import Console
from cli_onprem.core.logging import init_logging, QUIET_OPTION, VERBOSE_OPTION

app = typer.Typer(help="Command description")
console = Console()

@app.command()
def command_name(
    argument: Annotated[str, typer.Argument(help="Description")],
    option: Annotated[str, typer.Option(help="Description")] = "default",
    quiet: QUIET_OPTION = False,
    verbose: VERBOSE_OPTION = False
):
    """Command description."""
    init_logging(quiet=quiet, verbose=verbose)
    
    try:
        # 1. Validate inputs
        # 2. Call service layer functions
        # 3. Display output using console
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)
```

## Testing Patterns

Tests follow these conventions:
- Located in `tests/` with naming pattern `test_<command_name>.py`
- Extended tests use `test_<command_name>_extended.py` pattern
- Integration tests use `test_<command_name>_integration.py` pattern
- Mock external dependencies (Docker daemon, AWS services)
- Use pytest fixtures for common test data
- Test both success and error paths
- CI tests against Python 3.9, 3.10, 3.11, and 3.12

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

Releases are automated via GitHub Actions:
1. Commits to main trigger semantic-release version calculation
2. New versions are tagged as `v{version}`
3. CHANGELOG.md is automatically updated
4. Packages are built and uploaded to TestPyPI first
5. Non-RC/beta versions are then uploaded to PyPI
6. Concurrency groups prevent duplicate release runs

## Version Management

The project now includes dynamic version management:
- Version is displayed with `cli-onprem --version`
- In production: reads from installed package metadata
- In development: displays "dev" version
- Version is included in help text: "CLI-ONPREM v{version}"
- No manual version updates needed - handled by semantic-release

## CI/CD Pipeline

GitHub Actions workflows:
- **CI**: Runs on every PR and push to main
  - Tests against Python 3.9, 3.10, 3.11, and 3.12
  - Runs pre-commit hooks (ruff, black, mypy)
  - Builds package to verify packaging
- **Release**: Automatic version bumping and PyPI deployment
  - Uses `GH_TOKEN` for GitHub operations
  - Requires `TEST_PYPI_API_TOKEN` and `PYPI_API_TOKEN` secrets

## Creating Pull Requests

When creating PRs for this project:
1. Create feature branch: `git checkout -b feat/feature-name` or `fix/bug-name`
2. Make changes following the architecture patterns
3. Run tests locally: `uv run pytest -q`
4. Run linting: `SKIP=uv-lock uv run pre-commit run --all-files`
5. Commit with semantic-release format
6. Push and create PR: `gh pr create`

The project uses `uv` for dependency management - always use `uv lock` when updating dependencies.

Note: All commits should end with:
```
🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```