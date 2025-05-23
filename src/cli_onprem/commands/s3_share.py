"""CLI-ONPREM을 위한 S3 공유 관련 명령어."""

import os
import pathlib
from typing import Dict

import typer
import yaml
from rich.console import Console
from rich.prompt import Confirm, Prompt

context_settings = {
    "ignore_unknown_options": True,  # Always allow unknown options
    "allow_extra_args": True,  # Always allow extra args
}

app = typer.Typer(
    help="S3 공유 관련 작업 수행",
    context_settings=context_settings,
)
console = Console()

DEFAULT_PROFILE = "default_profile"

PROFILE_OPTION = typer.Option(
    DEFAULT_PROFILE, "--profile", help="생성·수정할 프로파일 이름"
)
OVERWRITE_OPTION = typer.Option(
    False, "--overwrite/--no-overwrite", help="동일 프로파일 존재 시 덮어쓸지 여부"
)


def get_credential_path() -> pathlib.Path:
    """자격증명 파일 경로를 반환합니다."""
    config_dir = pathlib.Path.home() / ".cli-onprem"
    return config_dir / "credential.yaml"


@app.command()
def init(
    profile: str = PROFILE_OPTION,
    overwrite: bool = OVERWRITE_OPTION,
) -> None:
    """~/.cli-onprem/credential.yaml 파일을 생성·갱신합니다."""
    credential_path = get_credential_path()
    config_dir = credential_path.parent

    if not config_dir.exists():
        console.print(f"[blue]설정 디렉토리 생성: {config_dir}[/blue]")
        config_dir.mkdir(parents=True, exist_ok=True)

    credentials: Dict[str, Dict[str, str]] = {}
    if credential_path.exists():
        try:
            with open(credential_path) as f:
                credentials = yaml.safe_load(f) or {}
        except Exception as e:
            console.print(f"[bold red]오류: 자격증명 파일 로드 실패: {e}[/bold red]")
            raise typer.Exit(code=1) from e

    if profile in credentials and not overwrite:
        profile_exists = f"프로파일 '{profile}'이(가) 이미 존재합니다."
        warning_msg = f"[bold yellow]경고: {profile_exists}[/bold yellow]"
        console.print(warning_msg)
        if not Confirm.ask("덮어쓰시겠습니까?"):
            console.print("[yellow]작업이 취소되었습니다.[/yellow]")
            raise typer.Exit(code=0)

    console.print(f"[bold blue]프로파일 '{profile}' 설정 중...[/bold blue]")

    aws_access_key = Prompt.ask("AWS Access Key")
    aws_secret_key = Prompt.ask("AWS Secret Key")
    region = Prompt.ask("Region")
    bucket = Prompt.ask("Bucket")
    prefix = Prompt.ask("Prefix")

    credentials[profile] = {
        "aws_access_key": aws_access_key,
        "aws_secret_key": aws_secret_key,
        "region": region,
        "bucket": bucket,
        "prefix": prefix,
    }

    try:
        with open(credential_path, "w") as f:
            yaml.dump(credentials, f, default_flow_style=False)

        os.chmod(credential_path, 0o600)

        console.print(f'[bold green]자격증명 저장됨: 프로파일 "{profile}"[/bold green]')
    except Exception as e:
        console.print(f"[bold red]오류: 자격증명 파일 저장 실패: {e}[/bold red]")
        raise typer.Exit(code=1) from e
