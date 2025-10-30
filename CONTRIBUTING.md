# Contributing to CLI-ONPREM

Thank you for your interest in contributing to cli-onprem! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Commit Convention](#commit-convention)
- [Pull Request Process](#pull-request-process)
- [Testing](#testing)
- [Code Style](#code-style)

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help create a positive community

## Getting Started

### Prerequisites

- Python 3.9 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Git

### Development Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/cli-onprem.git
   cd cli-onprem
   ```

2. **Install dependencies:**
   ```bash
   uv sync --all-extras --dev
   ```

3. **Install pre-commit hooks:**
   ```bash
   pre-commit install
   ```

4. **Verify setup:**
   ```bash
   uv run pytest -q
   ```

## Making Changes

### Branch Naming

Create a descriptive branch name based on the change type:

- `feat/feature-name` - New features
- `fix/bug-description` - Bug fixes
- `docs/what-changed` - Documentation updates
- `refactor/what-changed` - Code refactoring
- `test/what-added` - Test additions

Example:
```bash
git checkout -b feat/add-batch-operations
```

### Development Workflow

1. **Make your changes** following our [Architecture Guidelines](#architecture-guidelines)
2. **Write tests** for new functionality (aim for >90% coverage)
3. **Run tests locally:**
   ```bash
   uv run pytest -q
   ```
4. **Run pre-commit hooks:**
   ```bash
   SKIP=uv-lock uv run pre-commit run --all-files
   ```
5. **Commit your changes** following our [Commit Convention](#commit-convention)

## Commit Convention

We use [Angular Commit Convention](https://github.com/angular/angular/blob/master/CONTRIBUTING.md#commit) with semantic-release:

### Commit Message Format

```
<type>: <subject>

<body>

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Types

- `feat:` - New feature (triggers minor version bump)
- `fix:` - Bug fix (triggers patch version bump)
- `perf:` - Performance improvement (triggers patch version bump)
- `docs:` - Documentation only changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks
- `ci:` - CI/CD configuration changes
- `build:` - Build system changes

### Examples

```bash
# Feature (v2.2.0 → v2.3.0)
git commit -m "feat: add batch operation support for docker-tar"

# Bug fix (v2.2.0 → v2.2.1)
git commit -m "fix: correct path resolution in tar-fat32 restore"

# Performance (v2.2.0 → v2.2.1)
git commit -m "perf: optimize Docker image pull with parallel downloads"
```

## Pull Request Process

### Before Creating a PR

1. **Ensure all tests pass:**
   ```bash
   uv run pytest --cov=src/cli_onprem --cov-report=term
   ```

2. **Check code quality:**
   ```bash
   SKIP=uv-lock uv run pre-commit run --all-files
   ```

3. **Update documentation** if needed

### Creating a PR

1. **Push your branch:**
   ```bash
   git push -u origin feat/your-feature
   ```

2. **Create PR using GitHub CLI:**
   ```bash
   gh pr create --title "feat: your feature description" --body "..."
   ```

### PR Title Format

Use the same convention as commit messages:
```
feat: add new feature
fix: resolve issue with X
docs: update installation guide
```

### PR Description Template

```markdown
## Summary
Brief description of what this PR does.

## Changes
- Change 1
- Change 2
- Change 3

## Test Plan
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Related
- Closes #123
- Related to #456
```

### Review Process

- PRs require CI checks to pass
- Maintainers will review within 1-2 business days
- Address feedback by pushing new commits
- Once approved, maintainers will merge

## Testing

### Test Structure

```
tests/
├── test_<command_name>.py          # Unit tests
├── test_<command_name>_extended.py # Extended tests
├── test_<command_name>_integration.py # Integration tests
└── test_<service_name>.py          # Service layer tests
```

### Writing Tests

```python
def test_function_name() -> None:
    """Test description in Korean or English."""
    # Arrange
    mock_dependency.return_value = expected_data

    # Act
    result = function_under_test(params)

    # Assert
    assert result == expected_result
    mock_dependency.assert_called_with(expected_params)
```

### Running Tests

```bash
# All tests
uv run pytest -q

# Specific test file
uv run pytest tests/test_docker_tar.py -v

# With coverage
uv run pytest --cov=src/cli_onprem --cov-report=html

# Specific test function
uv run pytest tests/test_docker_tar.py::test_function_name -v
```

## Code Style

### Python Style

- **Line length:** 88 characters (Black default)
- **Type hints:** Required for all functions
- **Docstrings:** Required for public functions
- **Language:** Korean for user-facing text, English for code/comments

### Linting and Formatting

All enforced automatically via pre-commit:

```bash
# Manually run formatters
uv run ruff format src/
uv run black src/

# Manually run linters
uv run ruff check src/
uv run mypy src/ --strict --no-warn-unused-ignores
```

### Architecture Guidelines

Follow the layered architecture:

```
src/cli_onprem/
├── commands/    # CLI interface (thin, orchestration)
│   └── Uses services for business logic
├── services/    # Business logic (domain operations)
│   └── Uses utils for common operations
├── utils/       # Pure utility functions (no business logic)
│   └── No dependencies on services/commands
└── core/        # Framework concerns
    ├── errors.py   # Error types
    ├── logging.py  # Logging setup
    └── types.py    # Type definitions
```

**Key Principles:**
- Commands orchestrate, services implement
- Pure functions in utils layer
- Type safety with comprehensive hints
- Functional programming emphasis
- Error handling with custom exceptions

## Adding New Commands

1. **Create command file:** `src/cli_onprem/commands/your_command.py`
2. **Implement Typer app:**
   ```python
   import typer
   from rich.console import Console

   app = typer.Typer(help="Command description")
   console = Console()

   @app.command()
   def your_command(
       arg: str,
       option: str = "default",
   ):
       """Command description."""
       # Implementation
   ```

3. **Register in `__main__.py`:**
   ```python
   def get_command(name: str) -> Optional[typer.Typer]:
       commands = {
           # ...
           "your-command": "cli_onprem.commands.your_command",
       }
   ```

4. **Add tests:** `tests/test_your_command.py`
5. **Add documentation:** `docs/your-command.md`

## Questions or Need Help?

- Check existing issues and PRs
- Create a new issue for bugs or feature requests
- Use discussions for questions

Thank you for contributing! 🎉
