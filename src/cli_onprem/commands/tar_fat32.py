"""CLI-ONPREM을 위한 파일 압축 및 분할 명령어."""

import os
import subprocess
from pathlib import Path
from typing import List, Optional

import typer
from rich.markup import escape
from typing_extensions import Annotated

from ..libs import CLIError, create_typer_app, filter_completions
from ..libs.progress import ProgressReporter
from ..libs.subprocess import run_command as run_cmd

app, console = create_typer_app("파일 압축과 분할 관리")
progress = ProgressReporter(console)

DEFAULT_CHUNK_SIZE = "3G"


def complete_path(incomplete: str) -> List[str]:
    """경로 자동완성: 압축 가능한 파일과 디렉토리 제안"""

    def fetch_paths() -> List[str]:
        from pathlib import Path

        matches = []

        for path in Path(".").glob("*"):
            if path.name.startswith("."):
                continue

            if path.is_file() and path.stat().st_size > 0:
                matches.append(str(path))
            elif path.is_dir():
                matches.append(str(path))

        return matches

    return filter_completions(fetch_paths, incomplete)


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


def run_command(cmd: List[str], cwd: Optional[str] = None) -> bool:
    """셸 명령어를 실행합니다."""
    try:
        run_cmd(cmd, console, check=True, cwd=cwd)
        return True
    except Exception:
        return False


def get_file_size_mb(path: str) -> int:
    """파일 크기를 MB 단위로 반환합니다."""
    cmd = ["du", "-m", path]
    output = subprocess.check_output(cmd, text=True)
    size_mb = int(output.split()[0])
    return size_mb


def generate_restore_script(purge: bool = False) -> str:
    """복원 스크립트를 생성합니다."""
    script = """#!/usr/bin/env sh
set -eu

PURGE=0
[ "${1:-}" = "--purge" ] && PURGE=1

PACK_DIR="$(basename "$(pwd)")"

printf "▶ 조각 무결성 검증...\\n"
sha256sum -c manifest.sha256         # 실패 시 즉시 종료

printf "▶ 조각 병합...\\n"
cat parts/* > archive.tar.gz

printf "▶ 압축 해제...\\n"
cd ..
# 원본 파일·디렉터리 복원
tar --no-same-owner -xzvf "$PACK_DIR/archive.tar.gz"

printf "▶ 중간 파일 정리...\\n"
cd "$PACK_DIR"
rm -f archive.tar.gz                 # 병합본 제거

if [ "$PURGE" -eq 1 ]; then
  printf "▶ .pack 폴더 삭제(--purge)...\\n"
  cd ..
  rm -rf "$PACK_DIR"                 # .pack 디렉터리 전체 삭제
fi

printf "🎉 복원 완료\\n"
"""
    return script


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
    if not path.exists():
        console.print(f"[bold red]오류: 경로 {path}가 존재하지 않습니다[/bold red]")
        raise typer.Exit(code=1)

    input_path = str(path.absolute())
    basename = os.path.basename(input_path)
    output_dir = f"{basename}.pack"
    parts_dir = f"{output_dir}/parts"

    if os.path.exists(output_dir):
        progress.warning(f"출력 디렉터리 {output_dir}가 이미 존재합니다. 삭제 중...")
        import shutil

        shutil.rmtree(output_dir)
        progress.success("기존 디렉터리 삭제 완료")

    progress.step(f"출력 디렉터리 {output_dir} 생성 중...")
    os.makedirs(parts_dir)

    archive_path = f"{output_dir}/archive.tar.gz"
    progress.step(f"{basename} 압축 중...")

    if path.is_dir():
        cmd = ["tar", "-czvf", archive_path, "-C", str(path.parent), basename]
    else:
        cmd = ["tar", "-czvf", archive_path, "-C", str(path.parent), basename]

    if not run_command(cmd):
        CLIError.print_error(console, "압축 실패")

    progress.step(f"압축 파일을 {chunk_size} 크기로 분할 중...")
    split_cmd = ["split", "-b", chunk_size, archive_path, f"{parts_dir}/"]

    try:
        if not run_command(split_cmd):
            CLIError.print_error(console, "파일 분할 실패")

        import glob

        parts = glob.glob(f"{parts_dir}/*")
        if parts and not parts[0].endswith(".part"):
            progress.step("파일 이름 형식 조정 중...")
            for i, part in enumerate(sorted(parts)):
                new_name = f"{parts_dir}/{i:04d}.part"
                os.rename(part, new_name)
    except Exception as e:
        CLIError.print_error(console, f"파일 분할 중 예외 발생: {str(e)}", e)

    os.remove(archive_path)

    console.print("[bold blue]► 무결성 해시 파일 생성 중...[/bold blue]")
    hash_cmd = f"cd {output_dir} && sha256sum parts/* > manifest.sha256"
    if not run_command(["sh", "-c", hash_cmd]):
        console.print("[bold red]오류: 해시 파일 생성 실패[/bold red]")
        raise typer.Exit(code=1)

    console.print("[bold blue]► 복원 스크립트 생성 중...[/bold blue]")
    restore_script = generate_restore_script()
    with open(f"{output_dir}/restore.sh", "w") as f:
        f.write(restore_script)
    os.chmod(f"{output_dir}/restore.sh", 0o755)  # 실행 권한 부여

    progress.step("크기 정보 파일 생성 중...")
    size_mb = get_file_size_mb(output_dir)
    size_filename = f"{size_mb}_MB"
    with open(f"{output_dir}/{size_filename}", "w") as f:
        pass  # 빈 파일 생성

    progress.success(f"압축 완료: {escape(output_dir)}")
    console.print(f"[green]복원하려면: cd {escape(output_dir)} && ./restore.sh[/green]")


def complete_pack_dir(incomplete: str) -> List[str]:
    """팩 디렉토리 자동완성: 유효한 .pack 디렉토리 제안"""

    def fetch_pack_dirs() -> List[str]:
        from pathlib import Path

        matches = []

        for path in Path(".").glob("*.pack"):
            if path.is_dir() and (path / "restore.sh").exists():
                matches.append(str(path))

        return matches

    return filter_completions(fetch_pack_dirs, incomplete)


PACK_DIR_ARG = Annotated[
    Path,
    typer.Argument(
        ...,
        help="복원할 .pack 디렉토리 경로",
        autocompletion=complete_pack_dir,
    ),
]


@app.command()
def restore(
    pack_dir: Annotated[
        Path,
        typer.Argument(
            help="복원할 .pack 디렉토리 경로",
            autocompletion=complete_pack_dir,
        ),
    ],
    purge: bool = PURGE_OPTION,
) -> None:
    """압축된 파일을 복원합니다."""
    if not pack_dir.exists() or not pack_dir.is_dir():
        CLIError.print_error(
            console,
            f"{pack_dir}가 존재하지 않거나 디렉터리가 아닙니다"
        )

    if not (pack_dir / "restore.sh").exists():
        CLIError.print_error(console, f"{pack_dir}에 restore.sh가 없습니다")

    cmd = ["./restore.sh"]
    if purge:
        cmd.append("--purge")

    progress.step("복원 스크립트 실행 중...")
    if not run_command(cmd, cwd=str(pack_dir)):
        CLIError.print_error(console, "복원 실패")

    progress.success("복원 완료")
