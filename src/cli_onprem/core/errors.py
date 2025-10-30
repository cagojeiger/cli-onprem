"""에러 처리 함수 및 타입."""

from typing import List, Optional

import typer
from rich.console import Console

console = Console()


class CLIError(Exception):
    """CLI 에러 기본 클래스."""

    def __init__(self, message: str, exit_code: int = 1):
        super().__init__(message)
        self.exit_code = exit_code


class CommandError(CLIError):
    """명령 실행 중 발생하는 에러.

    외부 도구(docker, helm, aws, tar 등) 실행 실패 시 발생합니다.
    명령어와 stderr를 포함하여 디버깅을 돕습니다.
    """

    def __init__(
        self,
        message: str,
        command: Optional[List[str]] = None,
        stderr: Optional[str] = None,
        exit_code: int = 1,
    ):
        super().__init__(message, exit_code)
        self.command = command
        self.stderr = stderr

    def __str__(self) -> str:
        msg = super().__str__()

        if self.command:
            msg += f"\n\n실행 명령:\n  {' '.join(self.command)}"

        if self.stderr:
            # stderr가 너무 길면 마지막 20줄만
            stderr_lines = self.stderr.strip().split("\n")
            if len(stderr_lines) > 20:
                stderr_display = "\n".join(stderr_lines[-20:])
                msg += f"\n\n상세 오류 (마지막 20줄):\n{stderr_display}"
            else:
                msg += f"\n\n상세 오류:\n{self.stderr}"

        return msg


class TransientError(CommandError):
    """일시적인 오류로 재시도 가능.

    네트워크 타임아웃, 레이트 리밋, 일시적인 서비스 장애 등.
    자동화 스크립트에서 이 오류를 잡아 재시도할 수 있습니다.
    """

    pass


class PermanentError(CommandError):
    """영구적인 오류로 재시도 불필요.

    잘못된 자격증명, 존재하지 않는 리소스, 권한 부족 등.
    재시도해도 성공할 수 없는 오류입니다.
    """

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
