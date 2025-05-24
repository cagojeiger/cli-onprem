# CLI-ONPREM Architecture

## Overview

CLI-ONPREM follows a functional programming approach with clear separation of concerns. The architecture is designed to be simple, testable, and maintainable.

## Directory Structure

```
src/cli_onprem/
├── core/                      # Core framework functionality
│   ├── __init__.py
│   ├── cli.py                # CLI helper functions
│   ├── errors.py             # Error handling functions and types
│   ├── logging.py            # Logging configuration
│   └── types.py              # Common type definitions
│
├── utils/                     # Pure utility functions
│   ├── __init__.py
│   ├── shell.py              # Shell command execution
│   ├── file.py               # File operations
│   ├── formatting.py         # Output formatting
│   └── validation.py         # Input validation
│
├── services/                  # Domain-specific business logic
│   ├── __init__.py
│   ├── docker.py             # Docker-related functions
│   ├── helm.py               # Helm-related functions
│   ├── s3.py                 # AWS S3 operations
│   └── archive.py            # Archive and compression functions
│
├── commands/                  # CLI commands (thin layer)
│   ├── __init__.py
│   ├── docker_tar.py         # Docker tar command
│   ├── helm_local.py         # Helm local operations
│   ├── s3_share.py           # S3 sharing functionality
│   └── tar_fat32.py          # FAT32-compatible archiving
│
└── __main__.py               # Entry point
```

## Design Principles

### 1. Functional Programming
- Prefer pure functions without side effects
- Use explicit parameters instead of global state
- Return values instead of modifying state
- Compose small functions for complex operations

### 2. Separation of Concerns
- **Commands**: Thin CLI layer that orchestrates service calls
- **Services**: Domain-specific business logic
- **Utils**: General-purpose utility functions
- **Core**: Framework-level functionality

### 3. Dependency Direction
```
Commands → Services → Utils
    ↓          ↓        ↓
          Core ←────────┘
```

### 4. Type Safety
- All functions have type hints
- Use TypedDict for complex data structures
- Prefer explicit types over Any

## Module Responsibilities

### Core Layer (`core/`)
Framework-level functionality shared across all commands:
- CLI context and settings management
- Centralized error handling
- Logging configuration
- Common type definitions

### Utils Layer (`utils/`)
Pure utility functions that can be used anywhere:
- **shell.py**: `run_command()`, `check_command_exists()`
- **file.py**: `safe_write()`, `ensure_dir()`, `read_yaml()`
- **formatting.py**: `format_json()`, `format_table()`, `format_csv()`
- **validation.py**: `validate_path()`, `validate_image_name()`

### Services Layer (`services/`)
Domain-specific business logic organized by concern:

#### docker.py
```python
- check_docker_installed() -> None
- pull_image(reference: str, platform: str = None) -> None
- save_image(reference: str, output_path: Path) -> None
- parse_image_reference(reference: str) -> ImageReference
- normalize_image_name(image: str) -> str
- extract_images_from_yaml(yaml_content: str, normalize: bool = True) -> list[str]
```

#### helm.py
```python
- check_helm_installed() -> None
- extract_chart(archive_path: Path, dest_dir: Path) -> Path
- prepare_chart(chart_path: Path, workdir: Path) -> Path
- update_dependencies(chart_dir: Path) -> None
- render_template(chart_path: Path, values_files: list[Path] = None) -> str
```

#### s3.py
```python
- create_client(profile: dict) -> boto3.client
- sync_files(client, local_path: Path, bucket: str, prefix: str, **options) -> None
- generate_presigned_url(client, bucket: str, key: str, expires_in: int) -> str
- calculate_md5(file_path: Path) -> str
- list_objects(client, bucket: str, prefix: str) -> list[dict]
```

#### archive.py
```python
- compress_path(path: Path, output: Path) -> None
- split_file(file_path: Path, chunk_size: str, output_dir: Path) -> list[Path]
- create_manifest(parts: list[Path], output_path: Path) -> None
- verify_integrity(manifest_path: Path) -> bool
- generate_restore_script(purge: bool = False) -> str
```

### Commands Layer (`commands/`)
Thin orchestration layer that:
1. Defines CLI interface using Typer
2. Validates inputs
3. Calls service functions
4. Formats outputs
5. Handles errors gracefully

## Example: Refactoring helm-local

### Before (Monolithic)
```python
# commands/helm_local.py (486 lines)
def extract_images(...):
    # CLI setup
    # Helm check
    # Chart extraction
    # Template rendering
    # Image parsing
    # Normalization
    # Output formatting
    # Error handling
    # ... all in one function
```

### After (Modular)
```python
# commands/helm_local.py (thin layer)
from cli_onprem.services import helm, docker
from cli_onprem.utils import formatting

@app.command()
def extract_images(
    chart: Path,
    values: list[Path] = [],
    json_output: bool = False,
    raw: bool = False
) -> None:
    """Extract Docker images from Helm chart."""
    
    # Service orchestration
    helm.check_helm_installed()
    
    with tempfile.TemporaryDirectory() as workdir:
        chart_path = helm.prepare_chart(chart, Path(workdir))
        helm.update_dependencies(chart_path)
        
        rendered = helm.render_template(chart_path, values)
        images = docker.extract_images_from_yaml(rendered, normalize=not raw)
        
        # Output formatting
        if json_output:
            typer.echo(formatting.format_json(images))
        else:
            for image in images:
                typer.echo(image)
```

## Testing Strategy

### Unit Tests
- Test each service function independently
- Mock external dependencies (Docker, Helm, AWS)
- Use pytest fixtures for common test data

### Integration Tests
- Test command orchestration
- Verify service interactions
- Use temporary directories for file operations

### Example Test Structure
```python
# tests/services/test_helm.py
def test_render_template():
    # Test single function in isolation
    
# tests/services/test_docker.py  
def test_normalize_image_name():
    # Test pure function with various inputs

# tests/commands/test_helm_local.py
def test_extract_images_command():
    # Test full command with mocked services
```

## Benefits

1. **Maintainability**: Clear boundaries between layers
2. **Testability**: Each function can be tested in isolation
3. **Reusability**: Services can be used by multiple commands
4. **Extensibility**: Easy to add new commands or services
5. **Simplicity**: No complex class hierarchies
6. **Type Safety**: Full type coverage for better IDE support

## Migration Guide

When refactoring existing commands:

1. Identify business logic → Move to `services/`
2. Extract utilities → Move to `utils/`
3. Keep CLI definition in `commands/`
4. Update imports in tests
5. Ensure backward compatibility

## Future Considerations

- Plugin system for extending functionality
- Async support for concurrent operations
- Configuration management system
- Internationalization support