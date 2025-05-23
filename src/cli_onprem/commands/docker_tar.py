"""CLI-ONPREM을 위한 Docker 이미지 tar 명령어."""

import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, List, Optional, Tuple

import typer
from rich.console import Console
from rich.prompt import Confirm
from typing_extensions import Annotated

context_settings = {
    "ignore_unknown_options": True,  # Always allow unknown options
    "allow_extra_args": True,  # Always allow extra args
}

app = typer.Typer(
    help="Docker 이미지를 tar 파일로 저장",
    context_settings=context_settings,
)
console = Console()


def check_docker_cli_installed() -> None:
    """Docker CLI가 설치되어 있는지 확인합니다.

    설치되어 있지 않은 경우 안내 메시지를 출력하고 프로그램을 종료합니다.
    """
    if shutil.which("docker") is None:
        console.print("[bold red]오류: Docker CLI가 설치되어 있지 않습니다[/bold red]")
        console.print(
            "[yellow]Docker CLI 설치 방법: https://docs.docker.com/engine/install/[/yellow]"
        )
        raise typer.Exit(code=1)


def complete_docker_reference(incomplete: str) -> List[str]:
    """도커 이미지 레퍼런스 자동완성: 로컬에 있는 이미지 제안"""

    def fetch_docker_images() -> List[str]:
        if shutil.which("docker") is None:
            console.print(
                "[yellow]Docker CLI가 없어 자동완성을 제공할 수 없습니다[/yellow]"
            )
            return []  # Docker CLI가 없으면 자동완성 제안 없음

        try:
            result = subprocess.run(
                ["docker", "images", "--format", "{{.Repository}}:{{.Tag}}"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.splitlines()
        except Exception as e:
            console.print(f"[yellow]이미지 자동완성 오류: {e}[/yellow]")
            return []

    from cli_onprem.libs.cache import get_cached_data

    all_images = get_cached_data("docker_images", fetch_docker_images, ttl=300)

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
OUTPUT_OPTION = typer.Option(
    None, "--output", "-o", help="저장 위치(디렉터리 또는 완전한 경로)"
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


def pull_image(
    reference: str, quiet: bool = False, max_retries: int = 3, arch: str = "linux/amd64"
) -> Tuple[bool, str]:
    """이미지를 Docker Hub에서 가져옵니다."""
    if not quiet:
        console.print(f"[yellow]이미지 {reference} 다운로드 중...[/yellow]")
    cmd = ["docker", "pull", "--platform", arch, reference]

    retry_count = 0
    last_error = ""

    while retry_count <= max_retries:
        success, error = run_docker_command(cmd)
        if success:
            return True, ""

        last_error = error
        if isinstance(error, bytes):
            error_str = error.decode("utf-8", errors="replace")
        else:
            error_str = str(error)

        if "timeout" in error_str.lower() and retry_count < max_retries:
            retry_count += 1
            wait_time = 2**retry_count  # 지수 백오프 (2, 4, 8초)
            if not quiet:
                console.print(
                    f"[yellow]이미지 다운로드 타임아웃, {retry_count}/{max_retries} "
                    f"재시도 중 ({wait_time}초 대기)...[/yellow]"
                )
            time.sleep(wait_time)
        else:
            break

    return False, last_error


def run_docker_command(
    cmd: List[str], stdout: Optional[Any] = None
) -> Tuple[bool, str]:
    """Docker 명령어를 실행합니다."""
    try:
        subprocess.run(
            cmd, check=True, stdout=stdout, stderr=subprocess.PIPE, text=True
        )
        return True, ""
    except subprocess.CalledProcessError as e:
        return False, e.stderr


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
    check_docker_cli_installed()  # Docker CLI 의존성 확인
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

        success, error = pull_image(reference, quiet, arch=f"linux/{architecture}")
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
            f"[bold green]이미지가 성공적으로 저장되었습니다: {full_path}[/bold green]"
        )
