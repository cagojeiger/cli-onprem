"""CLI-ONPREM을 위한 파일 압축 및 분할 명령어."""

import shutil
from pathlib import Path
from typing import List

import typer
from rich.console import Console
from rich.markup import escape
from typing_extensions import Annotated

from cli_onprem.core.errors import CommandError
from cli_onprem.core.logging import get_logger, init_logging
from cli_onprem.services.archive import (
    calculate_sha256_manifest,
    create_tar_archive,
    extract_tar_archive,
    get_directory_size_mb,
    merge_files,
    split_file,
    verify_manifest,
    write_manifest_file,
)
from cli_onprem.utils.fs import (
    create_size_marker,
    find_completable_paths,
    find_pack_directories,
    generate_restore_script,
    make_executable,
)

context_settings = {
    "ignore_unknown_options": True,  # Always allow unknown options
    "allow_extra_args": True,  # Always allow extra args
}

app = typer.Typer(
    help="파일 압축과 분할 관리",
    context_settings=context_settings,
)
console = Console()
logger = get_logger("commands.tar_fat32")

DEFAULT_CHUNK_SIZE = "3G"


def complete_path(incomplete: str) -> List[str]:
    """경로 자동완성: 압축 가능한 파일과 디렉토리 제안"""
    paths = find_completable_paths(
        include_files=True, include_dirs=True, min_file_size=1
    )
    return [p for p in paths if p.startswith(incomplete)]


def complete_pack_dir(incomplete: str) -> List[str]:
    """팩 디렉토리 자동완성: 유효한 .pack 디렉토리 제안"""
    pack_dirs = find_pack_directories()
    return [d for d in pack_dirs if d.startswith(incomplete)]


PATH_ARG = Annotated[
    Path,
    typer.Argument(
        ...,
        help="압축할 경로",
        autocompletion=complete_path,
    ),
]
CHUNK_SIZE_OPTION = typer.Option(
    DEFAULT_CHUNK_SIZE, "--chunk-size", "-c", help="조각 크기 (예: 3G, 500M)"
)
PURGE_OPTION = typer.Option(False, "--purge", help="성공 복원 시 .pack 폴더 삭제")


@app.command()
def pack(
    path: Annotated[
        Path,
        typer.Argument(
            help="압축할 경로",
            autocompletion=complete_path,
        ),
    ],
    chunk_size: str = CHUNK_SIZE_OPTION,
) -> None:
    """파일 또는 디렉터리를 압축하고 분할하여 저장합니다."""
    # 로깅 초기화
    init_logging()

    if not path.exists():
        console.print(f"[bold red]오류: 경로 {path}가 존재하지 않습니다[/bold red]")
        raise typer.Exit(code=1)

    path = path.absolute()
    output_dir = Path(f"{path.name}.pack")
    parts_dir = output_dir / "parts"

    if output_dir.exists():
        console.print(
            f"[bold yellow]경고: 출력 디렉터리 {output_dir}가 이미 존재합니다. "
            f"삭제 중...[/bold yellow]"
        )
        shutil.rmtree(output_dir)
        console.print("[bold green]기존 디렉터리 삭제 완료[/bold green]")

    console.print(f"[bold blue]► 출력 디렉터리 {output_dir} 생성 중...[/bold blue]")
    parts_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 1. 압축
        archive_path = output_dir.absolute() / "archive.tar.gz"
        console.print(f"[bold blue]► {path.name} 압축 중...[/bold blue]")
        create_tar_archive(path, archive_path, path.parent)

        # 2. 분할
        console.print(
            f"[bold blue]► 압축 파일을 {chunk_size} 크기로 분할 중...[/bold blue]"
        )
        split_file(archive_path, chunk_size, parts_dir.absolute())

        # 3. 압축 파일 제거
        archive_path.unlink()

        # 4. 해시 생성
        console.print("[bold blue]► 무결성 해시 파일 생성 중...[/bold blue]")
        manifest = calculate_sha256_manifest(output_dir, "parts/*")
        write_manifest_file(manifest, output_dir / "manifest.sha256")

        # 5. 복원 스크립트 생성
        console.print("[bold blue]► 복원 스크립트 생성 중...[/bold blue]")
        restore_script = generate_restore_script()
        restore_path = output_dir / "restore.sh"
        restore_path.write_text(restore_script)
        make_executable(restore_path)

        # 6. 크기 마커 생성
        console.print("[bold blue]► 크기 정보 파일 생성 중...[/bold blue]")
        size_mb = get_directory_size_mb(output_dir)
        create_size_marker(output_dir, size_mb)

        console.print(
            f"[bold green]🎉 압축 완료: {escape(str(output_dir))}[/bold green]"
        )
        console.print(
            f"[green]복원하려면: cd {escape(str(output_dir))} && ./restore.sh[/green]"
        )

    except CommandError as e:
        console.print(f"[bold red]오류: {e}[/bold red]")
        raise typer.Exit(code=1) from e


@app.command()
def restore(
    pack_dir: Annotated[
        Path,
        typer.Argument(
            help="복원할 .pack 디렉터리 경로",
            autocompletion=complete_pack_dir,
        ),
    ],
    purge: bool = PURGE_OPTION,
) -> None:
    """압축된 파일을 복원합니다."""
    # 로깅 초기화
    init_logging()

    if not pack_dir.exists() or not pack_dir.is_dir():
        console.print(
            f"[bold red]오류: {pack_dir}가 존재하지 않거나 "
            f"디렉터리가 아닙니다[/bold red]"
        )
        raise typer.Exit(code=1)

    if not (pack_dir / "restore.sh").exists():
        console.print(f"[bold red]오류: {pack_dir}에 restore.sh가 없습니다[/bold red]")
        raise typer.Exit(code=1)

    try:
        console.print("[bold blue]► 복원 프로세스 시작...[/bold blue]")

        # 1. 무결성 검증
        console.print("[bold blue]► 조각 무결성 검증 중...[/bold blue]")
        verify_manifest(pack_dir / "manifest.sha256")

        # 2. 파일 병합
        console.print("[bold blue]► 조각 파일 병합 중...[/bold blue]")
        archive_path = pack_dir / "archive.tar.gz"
        merge_files(pack_dir / "parts", archive_path, "*")

        # 3. 압축 해제
        console.print("[bold blue]► 압축 해제 중...[/bold blue]")
        extract_tar_archive(archive_path, pack_dir.parent)

        # 4. 중간 파일 정리
        console.print("[bold blue]► 중간 파일 정리 중...[/bold blue]")
        archive_path.unlink()

        # 5. 옵션에 따라 pack 디렉터리 삭제
        if purge:
            console.print("[bold blue]► .pack 폴더 삭제 중...[/bold blue]")
            shutil.rmtree(pack_dir)

        console.print("[bold green]🎉 복원 완료[/bold green]")

    except CommandError as e:
        console.print(f"[bold red]오류: {e}[/bold red]")
        raise typer.Exit(code=1) from e
