"""Subprocess execution utilities."""

import subprocess
from typing import Any, List, Union

from rich.console import Console

from .errors import CLIError


def run_command(
    cmd: Union[str, List[str]],
    console: Console,
    check: bool = True,
    capture_output: bool = False,
    text: bool = True,
    **kwargs: Any
) -> subprocess.CompletedProcess[str]:
    """Run a subprocess command with standardized error handling.
    
    Args:
        cmd: Command to run (string or list)
        console: Rich console instance
        check: Whether to check return code
        capture_output: Whether to capture stdout/stderr
        text: Whether to decode output as text
        **kwargs: Additional arguments to pass to subprocess.run
        
    Returns:
        CompletedProcess instance
        
    Raises:
        typer.Exit: If command fails and check=True
    """
    if isinstance(cmd, str):
        cmd_list = cmd.split()
        cmd_str = cmd
    else:
        cmd_list = cmd
        cmd_str = " ".join(cmd)
    
    try:
        return subprocess.run(
            cmd_list,
            check=check,
            capture_output=capture_output,
            text=text,
            **kwargs
        )
    except subprocess.CalledProcessError as e:
        CLIError.handle_subprocess_error(
            console,
            cmd_str,
            e,
            suggestion=None
        )
        raise  # For type checker
    except FileNotFoundError:
        CLIError.print_error(
            console,
            f"명령어를 찾을 수 없습니다: {cmd_list[0]}",
            None
        )
        raise  # For type checker


def get_command_output(
    cmd: Union[str, List[str]],
    console: Console,
    **kwargs: Any
) -> str:
    """Run a command and return its output.
    
    Args:
        cmd: Command to run
        console: Rich console instance
        **kwargs: Additional arguments to pass to run_command
        
    Returns:
        Command output as string
    """
    result = run_command(
        cmd,
        console,
        capture_output=True,
        text=True,
        **kwargs
    )
    return str(result.stdout).strip()