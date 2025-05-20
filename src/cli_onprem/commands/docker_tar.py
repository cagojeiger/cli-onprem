"""CLI-ONPREM을 위한 Docker 이미지 tar 명령어."""

import os
import re
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple, Any

import typer
from rich.console import Console
from rich.prompt import Confirm

app = typer.Typer(help="Docker 이미지를 tar 파일로 저장")
console = Console()

REFERENCE_ARG = typer.Argument(..., help="컨테이너 이미지 레퍼런스")
ARCH_OPTION = typer.Option(None, "--arch", help="추출 플랫폼 지정 (linux/arm64 등)")
OUTPUT_OPTION = typer.Option(
    None, "--output", "-o", help="저장 위치(디렉터리 또는 완전한 경로)"
)
STDOUT_OPTION = typer.Option(
    False, "--stdout", help="tar 스트림을 표준 출력으로 내보냄"
)
FORCE_OPTION = typer.Option(
    False, "--force", "-f", help="동일 이름 파일 덮어쓰기"
)
QUIET_OPTION = typer.Option(
    False, "--quiet", "-q", help="에러만 출력"
)
DRY_RUN_OPTION = typer.Option(
    False, "--dry-run", help="실제 저장하지 않고 파일명만 출력"
)
VERBOSE_OPTION = typer.Option(
    False, "--verbose", "-v", help="DEBUG 로그 출력"
)


def parse_image_reference(reference: str) -> Tuple[str, str, str, str]:
    """Docker 이미지 레퍼런스를 분해합니다.

    형식: [<registry>/][<namespace>/]<image>[:<tag>]
    누락 시 기본값:
    - registry: docker.io
    - namespace: library
    - tag: latest
    """
    registry = "docker.io"
    namespace = "library"
    image = ""
    tag = "latest"

    if ":" in reference:
        ref_parts = reference.split(":")
        tag = ref_parts[-1]
        reference = ":".join(ref_parts[:-1])

    parts = reference.split("/")
    
    if len(parts) == 1:
        image = parts[0]
    elif len(parts) == 2:
        if "." in parts[0] or ":" in parts[0]:  # 레지스트리로 판단
            registry = parts[0]
            image = parts[1]
        else:  # 네임스페이스/이미지로 판단
            namespace = parts[0]
            image = parts[1]
    elif len(parts) >= 3:
        registry = parts[0]
        namespace = parts[1]
        image = "/".join(parts[2:])

    return registry, namespace, image, tag


def generate_filename(
    registry: str, namespace: str, image: str, tag: str, arch: str
) -> str:
    """이미지 정보를 기반으로 파일명을 생성합니다.

    형식: [reg__][ns__]image__tag__arch.tar
    """
    registry = registry.replace("/", "_")
    namespace = namespace.replace("/", "_")
    image = image.replace("/", "_")
    tag = tag.replace("/", "_")
    arch = arch.replace("/", "_")

    parts = []
    
    if registry != "docker.io":
        parts.append(f"{registry}__")
    
    if namespace != "library":
        parts.append(f"{namespace}__")
    
    parts.append(f"{image}__{tag}__{arch}.tar")
    
    return "".join(parts)


def check_image_exists(reference: str) -> bool:
    """이미지가 로컬에 존재하는지 확인합니다."""
    cmd = ["docker", "inspect", "--type=image", reference]
    try:
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def pull_image(reference: str, quiet: bool = False) -> Tuple[bool, str]:
    """이미지를 Docker Hub에서 가져옵니다."""
    if not quiet:
        console.print(f"[yellow]이미지 {reference} 다운로드 중...[/yellow]")
    cmd = ["docker", "pull", reference]
    return run_docker_command(cmd)


def run_docker_command(
    cmd: List[str], stdout: Optional[Any] = None
) -> Tuple[bool, str]:
    """Docker 명령어를 실행합니다."""
    try:
        subprocess.run(
            cmd, 
            check=True, 
            stdout=stdout, 
            stderr=subprocess.PIPE,
            text=True
        )
        return True, ""
    except subprocess.CalledProcessError as e:
        return False, e.stderr


@app.command()
def save(
    reference: str = REFERENCE_ARG,
    arch: str = ARCH_OPTION,
    output: Optional[Path] = OUTPUT_OPTION,
    stdout: bool = STDOUT_OPTION,
    force: bool = FORCE_OPTION,
    quiet: bool = QUIET_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
    verbose: bool = VERBOSE_OPTION,
) -> None:
    """Docker 이미지를 tar 파일로 저장합니다.

    이미지 레퍼런스 구문: [<registry>/][<namespace>/]<image>[:<tag>]
    """
    registry, namespace, image, tag = parse_image_reference(reference)
    
    architecture = "amd64"
    if arch:
        architecture = arch.split("/")[-1]  # linux/arm64 -> arm64
    
    filename = generate_filename(registry, namespace, image, tag, architecture)
    
    output_path = Path.cwd() if output is None else output
    if output_path.is_dir():
        full_path = output_path / filename
    else:
        full_path = output_path
    
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
    
    if not check_image_exists(reference):
        if verbose:
            console.print(f"[blue]이미지 {reference}가 로컬에 없습니다.[/blue]")
        
        success, error = pull_image(reference, quiet)
        if not success:
            console.print(f"[bold red]Error: 이미지 다운로드 실패: {error}[/bold red]")
            raise typer.Exit(code=1)
    
    if not quiet:
        console.print(f"[green]이미지 {reference} 저장 중...[/green]")
    
    if stdout:
        docker_cmd = ["docker", "save", reference]
        success, error = run_docker_command(docker_cmd, stdout=subprocess.STDOUT)
    else:
        docker_cmd = ["docker", "save", "-o", str(full_path), reference]
        success, error = run_docker_command(docker_cmd)
    
    if not success:
        console.print(f"[bold red]Error: {error}[/bold red]")
        raise typer.Exit(code=1)
    
    if not stdout and not quiet:
        console.print(
            f"[bold green]이미지가 성공적으로 저장되었습니다: "
            f"{full_path}[/bold green]"
        )
