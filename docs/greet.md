# Greet Command

The `greet` command provides a simple way to output a greeting message.

## Usage

```bash
cli-onprem greet hello [NAME]
```

## Options

- `NAME`: Optional. The name of the person to greet. If not provided, defaults to "world".

## Examples

```bash
# Greet with default message
cli-onprem greet hello
# Output: Hello, world!

# Greet a specific person
cli-onprem greet hello Alice
# Output: Hello, Alice!
```

## Purpose

This command serves as an MVP skeleton validation tool to quickly verify:
- Typer decorator functionality
- Automatic help generation
- ANSI color output via Rich
- Complete pre-commit → mypy → pytest → CI pipeline
