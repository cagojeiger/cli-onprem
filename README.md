# CLI-ONPREM

A Typer-based Python CLI tool for infrastructure engineers to automate repetitive tasks.

## Features

- Simple, intuitive command-line interface
- Rich text output with colors and formatting
- Directory scanning and reporting
- Comprehensive documentation

## Installation

```bash
# Install from PyPI
pipx install cli-onprem

# Or install from source
git clone https://github.com/cagojeiger/cli.git
cd cli
uv sync --locked --all-extras --dev
pip install -e .
```

## Usage

```bash
# Get help
cli-onprem --help

# Greet command
cli-onprem greet hello [NAME]

# Scan directory
cli-onprem scan directory PATH [--verbose]
```

## Development

This project uses:
- `uv` for package management
- `pre-commit` hooks for code quality
- `ruff`, `black`, and `mypy` for linting and formatting
- GitHub Actions for CI/CD

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/cagojeiger/cli.git
cd cli

# Install dependencies
uv sync --locked --all-extras --dev

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
pytest
```

## Documentation

Detailed documentation for each command is available in the `docs/` directory:
- [Greet Command](docs/greet.md)
- [Scan Command](docs/scan.md)

## License

MIT License
