"""CLI-ONPREM을 위한 S3 공유 관련 명령어.

이 모듈은 하이브리드 접근법을 사용합니다:
- sync 명령: AWS CLI 직접 사용 (더 안정적이고 기능이 풍부함)
- presign, init-* 명령: boto3 사용 (복잡한 로직과 자동완성 기능 때문)
"""

import csv
import datetime
import io
import subprocess
import sys
from datetime import timedelta
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.prompt import Confirm, Prompt
from typing_extensions import Annotated

from cli_onprem.core.errors import CLIError
from cli_onprem.core.logging import get_logger, init_logging
from cli_onprem.services.credential import (
    DEFAULT_PROFILE,
    create_or_update_profile,
    get_profile_credentials,
    list_profiles,
    profile_exists,
)
from cli_onprem.services.s3 import (
    create_s3_client,
    generate_presigned_url,
    generate_s3_path,
    head_object,
    list_buckets,
    list_objects,
)

context_settings = {
    "ignore_unknown_options": True,  # Always allow unknown options
    "allow_extra_args": True,  # Always allow extra args
}


def format_file_size(size_bytes: int) -> str:
    """파일 크기를 적절한 단위로 변환하여 문자열로 반환."""
    if size_bytes >= 1000 * 1024 * 1024:  # 1000MB 이상은 GB로
        return f"{size_bytes / (1024 * 1024 * 1024):.1f}GB"
    elif size_bytes >= 1024 * 1024:  # 1MB 이상은 MB로
        size_mb = size_bytes / (1024 * 1024)
        if size_mb >= 100:
            return f"{size_mb:.0f}MB"
        else:
            return f"{size_mb:.1f}MB"
    else:  # 1MB 미만은 KB로
        return f"{size_bytes / 1024:.1f}KB"


app = typer.Typer(
    help="S3 공유 관련 작업 수행",
    context_settings=context_settings,
)
console = Console()
logger = get_logger("commands.s3_share")


def complete_profile(incomplete: str) -> List[str]:
    """프로파일 자동완성: 기존 프로파일 이름 제안"""
    try:
        profiles = list_profiles()
        return [p for p in profiles if p.startswith(incomplete)]
    except Exception:
        return []


def complete_bucket(incomplete: str) -> List[str]:
    """S3 버킷 자동완성: 접근 가능한 버킷 제안"""
    try:
        # 첫 번째 프로파일의 자격증명 사용
        profiles = list_profiles()
        if not profiles:
            return []

        creds = get_profile_credentials(profiles[0], check_bucket=False)
        s3_client = create_s3_client(
            creds["aws_access_key"], creds["aws_secret_key"], creds["region"]
        )

        buckets = list_buckets(s3_client)
        return [b for b in buckets if b.startswith(incomplete)]
    except Exception as e:
        logger.warning(f"버킷 자동완성 오류: {e}")
        return []


def complete_prefix(incomplete: str, bucket: str = "") -> List[str]:
    """S3 프리픽스 자동완성: 버킷 내 프리픽스 제안"""
    try:
        profiles = list_profiles()
        if not profiles:
            return []

        creds = get_profile_credentials(profiles[0], check_bucket=False)

        if not bucket:
            bucket = creds.get("bucket", "")
            if not bucket:
                return []

        s3_client = create_s3_client(
            creds["aws_access_key"], creds["aws_secret_key"], creds["region"]
        )

        current_path = ""
        if "/" in incomplete:
            last_slash_index = incomplete.rfind("/")
            if last_slash_index >= 0:
                current_path = incomplete[: last_slash_index + 1]

        prefixes, _ = list_objects(s3_client, bucket, current_path)
        return [p for p in prefixes if p.startswith(incomplete)]

    except Exception as e:
        logger.warning(f"프리픽스 자동완성 오류: {e}")
        return []


def complete_cli_onprem_paths(incomplete: str) -> List[str]:
    """cli-onprem 프리픽스 파일 및 폴더 자동완성"""
    try:
        profiles = list_profiles()
        if not profiles:
            return []

        creds = get_profile_credentials(profiles[0], check_bucket=True)
        s3_client = create_s3_client(
            creds["aws_access_key"], creds["aws_secret_key"], creds["region"]
        )

        bucket = creds.get("bucket", "")
        prefix = creds.get("prefix", "")
        if prefix and not prefix.endswith("/"):
            prefix = f"{prefix}/"

        prefixes, objects = list_objects(s3_client, bucket, f"{prefix}cli-onprem-")

        paths = []

        # 폴더
        for folder_path in prefixes:
            folder_name = folder_path.rstrip("/").split("/")[-1]
            if folder_name.startswith("cli-onprem-"):
                paths.append(folder_name)

        # 파일
        for obj in objects:
            if not obj["Key"].endswith("/"):
                file_name = obj["Key"].split("/")[-1]
                if file_name.startswith("cli-onprem-"):
                    paths.append(file_name)

        return [p for p in paths if p.startswith(incomplete)]

    except Exception:
        return []


# Options
PROFILE_OPTION = typer.Option(
    DEFAULT_PROFILE,
    "--profile",
    help="생성·수정할 프로파일 이름",
    autocompletion=complete_profile,
)
OVERWRITE_OPTION = typer.Option(
    False, "--overwrite/--no-overwrite", help="동일 프로파일 존재 시 덮어쓸지 여부"
)
BUCKET_OPTION = typer.Option(
    None, "--bucket", help="대상 S3 버킷 (미지정 시 프로파일의 bucket 사용)"
)
PREFIX_OPTION = typer.Option(
    None, "--prefix", help="대상 프리픽스 (미지정 시 프로파일의 prefix 사용)"
)
DELETE_OPTION = typer.Option(
    False, "--delete/--no-delete", help="원본에 없는 객체 삭제 여부 (기본: --no-delete)"
)
PARALLEL_OPTION = typer.Option(8, "--parallel", help="동시 업로드 쓰레드 수 (기본: 8)")


@app.command()
def init_credential(
    profile: str = PROFILE_OPTION,
    overwrite: bool = OVERWRITE_OPTION,
) -> None:
    """AWS 자격증명 정보(Access Key, Secret Key, Region)를 설정합니다."""
    init_logging()

    try:
        if profile_exists(profile) and not overwrite:
            console.print(
                f"[bold yellow]경고: 프로파일 '{profile}'이(가) "
                "이미 존재합니다.[/bold yellow]"
            )
            if not Confirm.ask("덮어쓰시겠습니까?"):
                console.print("[yellow]작업이 취소되었습니다.[/yellow]")
                return

        console.print(
            f"[bold blue]프로파일 '{profile}' 자격증명 설정 중...[/bold blue]"
        )

        aws_access_key = Prompt.ask("AWS Access Key")
        aws_secret_key = Prompt.ask("AWS Secret Key", password=True)
        region = Prompt.ask("Region", default="us-west-2")

        create_or_update_profile(
            profile,
            aws_access_key=aws_access_key,
            aws_secret_key=aws_secret_key,
            region=region,
        )

        console.print(f'[bold green]자격증명 저장됨: 프로파일 "{profile}"[/bold green]')

    except CLIError as e:
        console.print(f"[bold red]오류: {e}[/bold red]")
        raise typer.Exit(code=1) from e


@app.command()
def init_bucket(
    profile: str = PROFILE_OPTION,
    bucket: Optional[str] = typer.Option(
        None, "--bucket", help="S3 버킷", autocompletion=complete_bucket
    ),
    prefix: str = typer.Option(
        "/",
        "--prefix",
        help="S3 프리픽스 (기본값: /)",
        autocompletion=lambda ctx, incomplete: complete_prefix(
            incomplete, ctx.params.get("bucket", "")
        ),
    ),
) -> None:
    """S3 버킷 및 프리픽스 정보를 설정합니다.

    init-credential 명령 실행 후 사용 가능합니다.
    """
    init_logging()

    try:
        # 자격증명 확인
        _ = get_profile_credentials(profile, check_aws=True)

        console.print(f"[bold blue]프로파일 '{profile}' 버킷 설정 중...[/bold blue]")

        if bucket is None:
            bucket = Prompt.ask("Bucket")

        if prefix == "/":
            prefix = Prompt.ask("Prefix", default="/")

        create_or_update_profile(profile, bucket=bucket, prefix=prefix)

        console.print(
            f'[bold green]버킷 정보 저장됨: 프로파일 "{profile}"[/bold green]'
        )

    except CLIError as e:
        console.print(f"[bold red]오류: {e}[/bold red]")
        raise typer.Exit(code=1) from e


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def sync(
    ctx: typer.Context,
    src_path: Annotated[Path, typer.Argument(help="동기화할 로컬 파일 또는 폴더 경로")],
    bucket: Optional[str] = BUCKET_OPTION,
    prefix: Optional[str] = PREFIX_OPTION,
    delete: bool = DELETE_OPTION,
    parallel: int = PARALLEL_OPTION,
    profile: str = PROFILE_OPTION,
) -> None:
    """로컬 파일/디렉터리와 S3 프리픽스 간 증분 동기화를 수행합니다.

    AWS CLI의 s3 sync 명령을 사용하여 더 안정적인 동기화를 제공합니다.
    추가 옵션은 -- 뒤에 전달할 수 있습니다.

    예시:
        cli-onprem s3-share sync mydir -- --size-only
        cli-onprem s3-share sync myfile.pack -- --exclude "*.tmp"
    """
    init_logging()

    if not src_path.exists():
        console.print(
            f"[bold red]오류: 소스 경로 '{src_path}'가 존재하지 않습니다.[/bold red]"
        )
        raise typer.Exit(code=1)

    try:
        # AWS CLI 설치 확인
        from cli_onprem.utils.shell import check_command_exists, run_command

        if not check_command_exists("aws"):
            console.print(
                "[bold red]오류: AWS CLI가 설치되어 있지 않습니다.\n"
                "설치: https://aws.amazon.com/cli/[/bold red]"
            )
            raise typer.Exit(code=1)

        creds = get_profile_credentials(profile, check_bucket=True)

        s3_bucket = bucket or creds.get("bucket", "")
        s3_prefix = prefix or creds.get("prefix", "")

        if not s3_bucket:
            console.print("[bold red]오류: S3 버킷이 지정되지 않았습니다.[/bold red]")
            raise typer.Exit(code=1)

        if s3_prefix and not s3_prefix.endswith("/"):
            s3_prefix = f"{s3_prefix}/"

        final_s3_path = generate_s3_path(src_path, s3_prefix)
        s3_uri = f"s3://{s3_bucket}/{final_s3_path}"

        # AWS CLI 명령 구성
        cmd = ["aws", "s3", "sync", str(src_path), s3_uri, "--region", creds["region"]]

        if delete:
            cmd.append("--delete")

        # 추가 인자 처리 (-- 뒤의 모든 인자)
        if ctx.args:
            cmd.extend(ctx.args)

        console.print(f"[bold blue]'{src_path}' → '{s3_uri}' 동기화 중...[/bold blue]")

        # 환경 변수 설정 (AWS 자격증명)
        import os

        env = os.environ.copy()
        env["AWS_ACCESS_KEY_ID"] = creds["aws_access_key"]
        env["AWS_SECRET_ACCESS_KEY"] = creds["aws_secret_key"]

        # AWS CLI 실행
        run_command(cmd, env=env)

        console.print("[bold green]동기화 완료[/bold green]")

        # 파이프 출력용
        if not sys.stdout.isatty():
            print(f"{src_path.name}:{final_s3_path}")

    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]AWS CLI 오류: {e}[/bold red]")
        raise typer.Exit(code=1) from e
    except CLIError as e:
        console.print(f"[bold red]오류: {e}[/bold red]")
        raise typer.Exit(code=1) from e


@app.command()
def presign(
    select_path: str = typer.Option(
        ...,
        "--select-path",
        help="presign URL을 생성할 cli-onprem 폴더 또는 파일 선택",
        autocompletion=complete_cli_onprem_paths,
    ),
    output: Optional[str] = typer.Option(None, "--output", help="CSV 출력 파일 경로"),
    profile: str = PROFILE_OPTION,
    expires: int = typer.Option(
        1,
        "--expires",
        help="URL 만료 시간(일), 기본값: 1일, 최대 7일",
    ),
) -> None:
    """선택한 폴더의 파일들 또는 개별 파일에 대한 presigned URL을 생성합니다."""
    init_logging()

    try:
        # expires 옵션 처리
        if expires < 1 or expires > 7:
            console.print(
                "[bold red]오류: --expires는 1에서 7 사이여야 합니다.[/bold red]"
            )
            raise typer.Exit(code=1)
        expiry = expires * 24 * 60 * 60  # 일을 초로 변환
        # 파이프 입력 처리
        path_from_pipe = None
        if not sys.stdin.isatty():
            pipe_input = sys.stdin.read().strip()
            if pipe_input:
                parts = pipe_input.split(":", 1)
                if len(parts) == 2:
                    path_name, s3_path = parts
                    path_from_pipe = s3_path

        creds = get_profile_credentials(profile, check_bucket=True)
        s3_client = create_s3_client(
            creds["aws_access_key"], creds["aws_secret_key"], creds["region"]
        )

        s3_bucket = creds.get("bucket", "")
        s3_prefix = creds.get("prefix", "")

        if not s3_bucket:
            console.print("[bold red]오류: S3 버킷이 지정되지 않았습니다.[/bold red]")
            raise typer.Exit(code=1)

        if s3_prefix and not s3_prefix.endswith("/"):
            s3_prefix = f"{s3_prefix}/"

        path_prefix = path_from_pipe if path_from_pipe else f"{s3_prefix}{select_path}"

        # 폴더인지 파일인지 판단
        has_file_extension = "." in select_path.split("/")[-1]
        is_folder = path_prefix.endswith("/") or (
            not has_file_extension and "/" not in select_path.split("-")[-1]
        )

        if is_folder and not path_prefix.endswith("/"):
            path_prefix = f"{path_prefix}/"

        files = []

        if is_folder:
            console.print(
                f"[bold blue]폴더 '{path_prefix}'의 presigned URL "
                "생성 중...[/bold blue]"
            )

            _, objects = list_objects(s3_client, s3_bucket, path_prefix, delimiter="")

            for obj in objects:
                if not obj["Key"].endswith("/"):
                    relative_path = obj["Key"]
                    if path_prefix and relative_path.startswith(path_prefix):
                        relative_path = relative_path[len(path_prefix) :]

                    files.append(
                        {
                            "key": obj["Key"],
                            "size": obj["Size"],
                            "filename": (
                                relative_path
                                if relative_path
                                else obj["Key"].split("/")[-1]
                            ),
                        }
                    )

            if not files:
                console.print(
                    f"[yellow]경고: 폴더 '{path_prefix}'에 파일이 없습니다.[/yellow]"
                )
                return
        else:
            console.print(
                f"[bold blue]파일 '{path_prefix}'의 presigned URL "
                "생성 중...[/bold blue]"
            )

            try:
                metadata = head_object(s3_client, s3_bucket, path_prefix)

                relative_path = path_prefix
                if s3_prefix and relative_path.startswith(s3_prefix):
                    relative_path = relative_path[len(s3_prefix) :]

                files = [
                    {
                        "key": path_prefix,
                        "size": metadata["ContentLength"],
                        "filename": relative_path,
                    }
                ]
            except CLIError as e:
                console.print(f"[bold red]{e}[/bold red]")
                raise typer.Exit(code=1) from e

        # CSV 데이터 생성
        csv_data = []
        expire_time = datetime.datetime.now() + timedelta(seconds=expiry)
        expire_time_formatted = expire_time.strftime("%Y-%m-%d %H:%M")

        for file_info in files:
            try:
                presigned_url = generate_presigned_url(
                    s3_client, s3_bucket, file_info["key"], expires_in=expiry
                )

                size_formatted = format_file_size(file_info["size"])

                csv_data.append(
                    {
                        "filename": file_info["filename"],
                        "link": presigned_url,
                        "expire_at": expire_time_formatted,
                        "size": size_formatted,
                    }
                )
            except CLIError as e:
                console.print(
                    f"[yellow]경고: '{file_info['filename']}' "
                    f"URL 생성 실패: {e}[/yellow]"
                )

        # 출력
        if output:
            try:
                with open(output, "w", newline="") as csvfile:
                    writer = csv.DictWriter(
                        csvfile,
                        fieldnames=[
                            "filename",
                            "link",
                            "expire_at",
                            "size",
                        ],
                    )
                    writer.writeheader()
                    for row in csv_data:
                        writer.writerow(row)
                console.print(f"[bold green]CSV 파일 저장됨: {output}[/bold green]")
            except Exception as e:
                console.print(f"[bold red]오류: CSV 파일 저장 실패: {e}[/bold red]")
                raise typer.Exit(code=1) from e
        else:
            output_csv = io.StringIO()
            writer = csv.DictWriter(
                output_csv,
                fieldnames=[
                    "filename",
                    "link",
                    "expire_at",
                    "size",
                ],
            )
            writer.writeheader()
            for row in csv_data:
                writer.writerow(row)

            print(output_csv.getvalue())

        console.print(f"[bold green]URL 생성 완료: {len(csv_data)}개 파일[/bold green]")

    except CLIError as e:
        console.print(f"[bold red]오류: {e}[/bold red]")
        raise typer.Exit(code=1) from e
