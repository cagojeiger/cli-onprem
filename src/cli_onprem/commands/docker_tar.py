"""CLI-ONPREM을 위한 Docker 이미지 tar 명령어."""

from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.prompt import Confirm
from typing_extensions import Annotated

from cli_onprem.core.errors import CommandError, DependencyError
from cli_onprem.core.logging import get_logger, init_logging, set_log_level
from cli_onprem.services.docker import (
    check_docker_installed,
    generate_tar_filename,
    list_local_images,
    parse_image_reference,
    pull_image,
    save_image,
    save_image_to_stdout,
)
from cli_onprem.utils.shell import check_command_exists

context_settings = {
    "ignore_unknown_options": True,  # Always allow unknown options
    "allow_extra_args": True,  # Always allow extra args
}

app = typer.Typer(
    help="Docker 이미지를 tar 파일로 저장",
    context_settings=context_settings,
)
console = Console()
logger = get_logger("commands.docker_tar")


def _check_docker_cli() -> None:
    """Docker CLI 설치 확인 및 에러 처리."""
    try:
        check_docker_installed()
    except DependencyError as e:
        console.print(f"[bold red]오류: {e}[/bold red]")
        raise typer.Exit(code=1) from e


def complete_docker_reference(incomplete: str) -> List[str]:
    """도커 이미지 레퍼런스 자동완성: 로컬에 있는 이미지 제안"""
    if not check_command_exists("docker"):
        return []

    try:
        all_images = list_local_images()
    except CommandError:
        return []

    registry_filter = None
    if "/" in incomplete:
        parts = incomplete.split("/", 1)
        if "." in parts[0] or ":" in parts[0]:  # 레지스트리로 판단
            registry_filter = parts[0]

    filtered_images = [img for img in all_images if img.startswith(incomplete)]

    if registry_filter:
        filtered_images = [
            img for img in filtered_images if img.startswith(registry_filter)
        ]

    return filtered_images


REFERENCE_ARG = Annotated[
    str,
    typer.Argument(
        ...,
        help="컨테이너 이미지 레퍼런스",
        autocompletion=complete_docker_reference,
    ),
]


def _validate_arch(value: str) -> str:
    """`--arch` 옵션 값을 검증한다.

    Args:
        value: 사용자가 입력한 플랫폼 문자열.

    Returns:
        검증된 플랫폼 문자열.

    Raises:
        typer.BadParameter: 허용되지 않은 값이 입력된 경우.
    """
    allowed = {"linux/amd64", "linux/arm64"}
    if value not in allowed:
        msg = "linux/amd64 또는 linux/arm64만 지원합니다."
        raise typer.BadParameter(msg)
    return value


def complete_arch(incomplete: str) -> List[str]:
    """아키텍처 옵션 자동완성"""
    options = ["linux/amd64", "linux/arm64"]
    return [opt for opt in options if opt.startswith(incomplete)]


ARCH_OPTION = typer.Option(
    "linux/amd64",
    "--arch",
    help="추출 플랫폼 지정 (linux/amd64 또는 linux/arm64)",
    callback=_validate_arch,
    autocompletion=complete_arch,
)
DEST_OPTION = typer.Option(
    None,
    "--destination",
    "-d",
    help="저장 위치(디렉터리 또는 완전한 경로)",
)
STDOUT_OPTION = typer.Option(
    False, "--stdout", help="tar 스트림을 표준 출력으로 내보냄"
)
FORCE_OPTION = typer.Option(False, "--force", "-f", help="동일 이름 파일 덮어쓰기")
QUIET_OPTION = typer.Option(False, "--quiet", "-q", help="에러만 출력")
DRY_RUN_OPTION = typer.Option(
    False, "--dry-run", help="실제 저장하지 않고 파일명만 출력"
)
VERBOSE_OPTION = typer.Option(False, "--verbose", "-v", help="DEBUG 로그 출력")


# 삭제 - 서비스 모듈로 이동


@app.command()
def save(
    reference: Annotated[
        str,
        typer.Argument(
            help="컨테이너 이미지 레퍼런스",
            autocompletion=complete_docker_reference,
        ),
    ],
    arch: str = ARCH_OPTION,
    destination: Optional[Path] = DEST_OPTION,
    stdout: bool = STDOUT_OPTION,
    force: bool = FORCE_OPTION,
    quiet: bool = QUIET_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
    verbose: bool = VERBOSE_OPTION,
) -> None:
    """Docker 이미지를 tar 파일로 저장합니다.

    이미지 레퍼런스 구문: [<registry>/][<namespace>/]<image>[:<tag>]
    """
    # 로깅 초기화
    init_logging()

    if quiet:
        set_log_level("ERROR")
    elif verbose:
        set_log_level("DEBUG")

    _check_docker_cli()  # Docker CLI 의존성 확인

    registry, namespace, image, tag = parse_image_reference(reference)

    architecture = "amd64"
    if arch:
        architecture = arch.split("/")[-1]  # linux/arm64 -> arm64

    filename = generate_tar_filename(registry, namespace, image, tag, architecture)

    dest_path = Path.cwd() if destination is None else destination

    if destination is None or (
        dest_path.is_dir() or (not dest_path.exists() and not dest_path.suffix)
    ):
        if not dest_path.exists():
            dest_path.mkdir(parents=True, exist_ok=True)
        full_path = dest_path / filename
    else:
        full_path = dest_path

    if verbose:
        console.print(f"[bold blue]레퍼런스: {reference}[/bold blue]")
        console.print(f"[blue]분해: {registry}/{namespace}/{image}:{tag}[/blue]")
        console.print(f"[blue]아키텍처: {architecture}[/blue]")
        console.print(f"[blue]파일명: {filename}[/blue]")
        console.print(f"[blue]저장 경로: {full_path}[/blue]")

    if dry_run:
        if not quiet:
            console.print(f"[yellow]다음 파일을 생성할 예정: {full_path}[/yellow]")
        return

    if not stdout and full_path.exists() and not force:
        if not Confirm.ask(
            f"[yellow]파일 {full_path}이(가) 이미 존재합니다. "
            f"덮어쓰시겠습니까?[/yellow]"
        ):
            console.print("[yellow]작업이 취소되었습니다.[/yellow]")
            return

    try:
        # 이미지 pull
        pull_image(reference, arch=f"linux/{architecture}")

        if not quiet:
            console.print(f"[green]이미지 {reference} 저장 중...[/green]")

        # 이미지 저장
        if stdout:
            save_image_to_stdout(reference)
        else:
            save_image(reference, str(full_path))
            if not quiet:
                console.print(
                    f"[bold green]이미지가 성공적으로 저장되었습니다: "
                    f"{full_path}[/bold green]"
                )
    except (CommandError, DependencyError) as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(code=1) from e
