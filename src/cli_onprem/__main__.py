"""CLI-ONPREM 애플리케이션의 메인 진입점."""

import importlib
import sys
from typing import Any, cast

import typer
from rich.console import Console

from cli_onprem import __version__

# from cli_onprem.commands import docker_tar, tar_fat32, helm, s3_share

context_settings = {
    "ignore_unknown_options": True,  # Always allow unknown options
    "allow_extra_args": True,  # Always allow extra args
}

app = typer.Typer(
    name="cli-onprem",
    help=f"CLI-ONPREM v{__version__} - 인프라 엔지니어를 위한 CLI 도구",
    add_completion=True,
    context_settings=context_settings,
    no_args_is_help=True,
    invoke_without_command=True,
)

console = Console()


def get_command(import_path: str) -> typer.Typer:
    """지정된 경로에서 명령어 모듈을 로드합니다."""
    module_path, attr_name = import_path.split(":")
    module = importlib.import_module(module_path)
    return cast(typer.Typer, getattr(module, attr_name))


app.add_typer(get_command("cli_onprem.commands.docker_tar:app"), name="docker-tar")
app.add_typer(get_command("cli_onprem.commands.tar_fat32:app"), name="tar-fat32")
app.add_typer(get_command("cli_onprem.commands.helm_local:app"), name="helm-local")
app.add_typer(get_command("cli_onprem.commands.s3_share:app"), name="s3-share")


@app.callback()
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False, "--version", help="버전 정보 표시", is_eager=True
    ),
    verbose: bool = False,
) -> None:
    """CLI-ONPREM - 인프라 엔지니어를 위한 CLI 도구."""
    if version:
        console.print(f"cli-onprem v{__version__}")
        raise typer.Exit()

    # 명령어가 지정되지 않았고 --version도 아닌 경우에만 help 표시
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        raise typer.Exit()


def main_cli() -> Any:
    """Entry point for CLI."""
    return app(sys.argv[1:])


if __name__ == "__main__":
    main_cli()
