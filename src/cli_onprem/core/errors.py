"""에러 처리 함수 및 타입."""

from typing import Optional

import typer
from rich.console import Console

console = Console()


class CLIError(Exception):
    """CLI 에러 기본 클래스."""

    def __init__(self, message: str, exit_code: int = 1):
        super().__init__(message)
        self.exit_code = exit_code


class CommandError(CLIError):
    """명령 실행 중 발생하는 에러."""

    pass


class DependencyError(CLIError):
    """의존성 관련 에러."""

    pass


def handle_error(error: Exception, exit_code: int = 1) -> None:
    """에러를 처리하고 적절한 메시지를 출력합니다.

    Args:
        error: 발생한 예외
        exit_code: 종료 코드
    """
    console.print(f"[bold red]오류: {str(error)}[/bold red]")
    raise typer.Exit(code=exit_code)


def check_command_installed(command: str, install_url: Optional[str] = None) -> None:
    """명령어가 설치되어 있는지 확인합니다.

    Args:
        command: 확인할 명령어
        install_url: 설치 안내 URL (선택적)

    Raises:
        typer.Exit: 명령어가 없을 경우
    """
    import shutil

    if shutil.which(command) is None:
        console.print(
            f"[bold red]오류: {command} CLI가 설치되어 있지 않습니다[/bold red]"
        )
        if install_url:
            console.print(f"[yellow]설치 방법: {install_url}[/yellow]")
        raise typer.Exit(code=1)
