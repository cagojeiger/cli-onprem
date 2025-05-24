# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

cli-onprem is a CLI tool that automates repetitive tasks for infrastructure engineers. It provides commands for Docker image management, Helm chart processing, S3 synchronization, and FAT32-compatible file splitting.

## Development Commands

```bash
# Install dependencies (using uv)
uv sync --locked --all-extras --dev

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

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
```

## Architecture

The project uses a modular command structure where each command is a separate module in `src/cli_onprem/commands/`. The main entry point (`__main__.py`) dynamically loads commands based on available modules.

Key architectural patterns:
- Each command is implemented as an independent Typer app
- Commands are lazily loaded to minimize startup time
- Rich is used for enhanced terminal output (progress bars, tables)
- Commands support autocompletion where relevant (e.g., Docker image names)

## Command Implementation Pattern

When adding a new command:
1. Create a new file in `src/cli_onprem/commands/`
2. Define a Typer app and implement the command function
3. The command will be automatically discovered and registered

Example structure:
```python
import typer
from typing_extensions import Annotated

app = typer.Typer()

@app.command()
def command_name(
    argument: Annotated[str, typer.Argument(help="Description")],
    option: Annotated[str, typer.Option(help="Description")] = "default"
):
    """Command description."""
    # Implementation
```

## Testing

Tests are located in `tests/` and follow the naming pattern `test_<command_name>.py`. Tests use pytest and often mock external dependencies (Docker, AWS).

## Release Process

The project uses semantic-release for automated versioning and changelog generation. Commits should follow conventional commit format:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation updates
- `chore:` for maintenance tasks

Releases are automatically created when changes are pushed to the main branch.