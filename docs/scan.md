# Scan Command

The `scan` command scans a specified directory and generates a report of its contents.

## Usage

```bash
cli-onprem scan directory PATH [--verbose]
```

## Options

- `PATH`: Required. The directory path to scan.
- `--verbose`, `-v`: Optional. Enable verbose output with additional information during the scan process.

## Examples

```bash
# Scan a directory
cli-onprem scan directory /path/to/directory
# Output: A table showing file and directory counts

# Scan with verbose output
cli-onprem scan directory /path/to/directory --verbose
# Output: Additional information during the scan process
```

## Report Format

The command generates a table report containing:
- Total number of files
- Total number of directories
- Total number of items (files + directories)

## Error Handling

The command will exit with an error code (1) if:
- The specified path does not exist
- The specified path is not a directory
