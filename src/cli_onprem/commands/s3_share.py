"""CLI-ONPREM을 위한 S3 공유 관련 명령어."""

import hashlib
import os
import pathlib
from typing import Dict, List, Optional

import typer
import yaml
from rich.console import Console
from rich.prompt import Confirm, Prompt
from tqdm import tqdm

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


def complete_profile(incomplete: str) -> List[str]:
    """프로파일 자동완성: 기존 프로파일 이름 제안"""

    def fetch_profiles() -> List[str]:
        try:
            credential_path = get_credential_path()
            if not credential_path.exists():
                return []

            with open(credential_path) as f:
                credentials = yaml.safe_load(f) or {}

            if not credentials:
                return []

            profiles = list(credentials.keys())
            return profiles
        except Exception:
            return []  # 오류 발생 시 자동완성 제안 없음

    from cli_onprem.libs.cache import get_cached_data

    profiles = get_cached_data("profile_list", fetch_profiles, ttl=300)
    return [p for p in profiles if p.startswith(incomplete)]


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


def get_credential_path() -> pathlib.Path:
    """자격증명 파일 경로를 반환합니다."""
    config_dir = pathlib.Path.home() / ".cli-onprem"
    return config_dir / "credential.yaml"


def complete_bucket(incomplete: str) -> List[str]:
    """S3 버킷 자동완성: 접근 가능한 버킷 제안"""

    def fetch_buckets() -> List[str]:
        try:
            import boto3

            credential_path = get_credential_path()
            if not credential_path.exists():
                return []

            with open(credential_path) as f:
                credentials = yaml.safe_load(f) or {}

            if not credentials:
                return []

            profile = next(iter(credentials))
            creds = credentials[profile]

            s3_client = boto3.client(
                "s3",
                aws_access_key_id=creds["aws_access_key"],
                aws_secret_access_key=creds["aws_secret_key"],
                region_name=creds["region"],
            )

            response = s3_client.list_buckets()
            buckets = [bucket["Name"] for bucket in response["Buckets"]]
            return buckets
        except Exception as e:
            console.print(f"[yellow]버킷 자동완성 오류: {e}[/yellow]")
            return []

    from cli_onprem.libs.cache import get_cached_data

    buckets = get_cached_data("s3_buckets", fetch_buckets, ttl=600)
    return [b for b in buckets if b.startswith(incomplete)]


def complete_prefix(incomplete: str, bucket: str = "") -> List[str]:
    """S3 프리픽스 자동완성: 버킷 내 프리픽스 제안"""

    def fetch_prefixes(bucket_name: str, current_path: str) -> List[str]:
        try:
            import boto3

            if not bucket_name:
                credential_path = get_credential_path()
                if not credential_path.exists():
                    return []

                with open(credential_path) as f:
                    credentials = yaml.safe_load(f) or {}

                if not credentials:
                    return []

                profile = next(iter(credentials))
                creds = credentials[profile]
                bucket_name = creds.get("bucket", "")
                if not bucket_name:
                    return []

            credential_path = get_credential_path()
            if not credential_path.exists():
                return []

            with open(credential_path) as f:
                credentials = yaml.safe_load(f) or {}

            if not credentials:
                return []

            profile = next(iter(credentials))
            creds = credentials[profile]

            s3_client = boto3.client(
                "s3",
                aws_access_key_id=creds["aws_access_key"],
                aws_secret_access_key=creds["aws_secret_key"],
                region_name=creds["region"],
            )

            response = s3_client.list_objects_v2(
                Bucket=bucket_name, Delimiter="/", Prefix=current_path
            )

            prefixes = []

            if "CommonPrefixes" in response:
                for prefix in response["CommonPrefixes"]:
                    prefixes.append(prefix["Prefix"])

            return prefixes
        except Exception as e:
            console.print(f"[yellow]프리픽스 자동완성 오류: {e}[/yellow]")
            return []

    current_path = ""

    if "/" in incomplete:
        last_slash_index = incomplete.rfind("/")
        if last_slash_index >= 0:
            current_path = incomplete[: last_slash_index + 1]

    bucket_name = bucket
    if not bucket_name:
        try:
            credential_path = get_credential_path()
            if credential_path.exists():
                with open(credential_path) as f:
                    credentials = yaml.safe_load(f) or {}
                if credentials:
                    profile = next(iter(credentials))
                    creds = credentials[profile]
                    bucket_name = creds.get("bucket", "")
        except Exception:
            pass

    cache_key = f"s3_prefixes_{bucket_name}_{current_path}"

    from cli_onprem.libs.cache import get_cached_data

    prefixes = get_cached_data(
        cache_key, lambda: fetch_prefixes(bucket_name, current_path), ttl=600
    )

    return [p for p in prefixes if p.startswith(incomplete)]


@app.command()
def init_credential(
    profile: str = PROFILE_OPTION,
    overwrite: bool = OVERWRITE_OPTION,
) -> None:
    """AWS 자격증명 정보(Access Key, Secret Key, Region)를 설정합니다."""
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

    console.print(f"[bold blue]프로파일 '{profile}' 자격증명 설정 중...[/bold blue]")

    aws_access_key = Prompt.ask("AWS Access Key")
    aws_secret_key = Prompt.ask("AWS Secret Key")
    region = Prompt.ask("Region", default="us-west-2")

    if profile in credentials:
        bucket = credentials[profile].get("bucket", "")
        prefix = credentials[profile].get("prefix", "")
    else:
        bucket = ""
        prefix = ""

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


@app.command()
def init_bucket(
    profile: str = PROFILE_OPTION,
    bucket: str = typer.Option(
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
    creds = get_profile_credentials(profile, check_bucket=False)

    if not creds.get("aws_access_key") or not creds.get("aws_secret_key"):
        console.print(
            f"[bold red]오류: 프로파일 '{profile}'에 AWS 자격증명이 없습니다. "
            f"먼저 's3-share init-credential' 명령을 실행하세요.[/bold red]"
        )
        raise typer.Exit(code=1)

    credential_path = get_credential_path()

    try:
        with open(credential_path) as f:
            credentials = yaml.safe_load(f) or {}
    except Exception as e:
        console.print(f"[bold red]오류: 자격증명 파일 로드 실패: {e}[/bold red]")
        raise typer.Exit(code=1) from e

    console.print(f"[bold blue]프로파일 '{profile}' 버킷 설정 중...[/bold blue]")

    if bucket is None:
        bucket = Prompt.ask("Bucket")

    if prefix == "/":
        prefix = Prompt.ask("Prefix", default="/")

    credentials[profile]["bucket"] = bucket
    credentials[profile]["prefix"] = prefix

    try:
        with open(credential_path, "w") as f:
            yaml.dump(credentials, f, default_flow_style=False)

        console.print(
            f'[bold green]버킷 정보 저장됨: 프로파일 "{profile}"[/bold green]'
        )
    except Exception as e:
        console.print(f"[bold red]오류: 자격증명 파일 저장 실패: {e}[/bold red]")
        raise typer.Exit(code=1) from e


def get_profile_credentials(profile: str, check_bucket: bool = False) -> Dict[str, str]:
    """저장된 프로파일에서 자격증명을 로드합니다.

    Args:
        profile: 프로파일 이름
        check_bucket: 버킷 설정 여부 확인
            (True인 경우 버킷이 설정되지 않았으면 오류 발생)
    """
    credential_path = get_credential_path()

    if not credential_path.exists():
        console.print(
            "[bold red]오류: 자격증명 파일이 없습니다. "
            "먼저 's3-share init-credential' 명령을 실행하세요.[/bold red]"
        )
        raise typer.Exit(code=1)

    try:
        with open(credential_path) as f:
            credentials = yaml.safe_load(f) or {}
    except Exception as e:
        console.print(f"[bold red]오류: 자격증명 파일 로드 실패: {e}[/bold red]")
        raise typer.Exit(code=1) from e

    if profile not in credentials:
        console.print(
            f"[bold red]오류: 프로파일 '{profile}'이(가) 존재하지 않습니다.[/bold red]"
        )
        raise typer.Exit(code=1)

    if not credentials[profile].get("aws_access_key") or not credentials[profile].get(
        "aws_secret_key"
    ):
        console.print(
            f"[bold red]오류: 프로파일 '{profile}'에 AWS 자격증명이 없습니다. "
            f"먼저 's3-share init-credential' 명령을 실행하세요.[/bold red]"
        )
        raise typer.Exit(code=1)

    if check_bucket and not credentials[profile].get("bucket"):
        console.print(
            f"[bold red]오류: 프로파일 '{profile}'에 버킷이 설정되지 않았습니다. "
            f"먼저 's3-share init-bucket' 명령을 실행하세요.[/bold red]"
        )
        raise typer.Exit(code=1)

    result: Dict[str, str] = {}
    for key, value in credentials[profile].items():
        result[key] = str(value)

    return result


def calculate_file_md5(file_path: pathlib.Path) -> Optional[str]:
    """파일의 MD5 해시를 계산합니다. 대용량 파일의 경우 None을 반환합니다."""
    if file_path.stat().st_size >= 5 * 1024 * 1024 * 1024:
        return None

    try:
        md5_hash = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()
    except Exception:
        return None


SRC_PATH_ARGUMENT = typer.Argument(..., help="동기화할 로컬 폴더 경로")


@app.command()
def sync(
    src_path: pathlib.Path = SRC_PATH_ARGUMENT,
    bucket: Optional[str] = BUCKET_OPTION,
    prefix: Optional[str] = PREFIX_OPTION,
    delete: bool = DELETE_OPTION,
    parallel: int = PARALLEL_OPTION,
    profile: str = PROFILE_OPTION,
) -> None:
    """로컬 디렉터리와 S3 프리픽스 간 증분 동기화를 수행합니다."""
    if not src_path.exists() or not src_path.is_dir():
        console.print(
            f"[bold red]오류: 소스 경로 '{src_path}'가 존재하지 않거나 "
            f"디렉토리가 아닙니다.[/bold red]"
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

    import boto3

    console.print(
        f"[bold blue]S3 동기화: {src_path} → s3://{s3_bucket}/{s3_prefix}[/bold blue]"
    )

    s3_client = boto3.client(
        "s3",
        aws_access_key_id=creds["aws_access_key"],
        aws_secret_access_key=creds["aws_secret_key"],
        region_name=creds["region"],
    )

    s3_objects = {}
    paginator = s3_client.get_paginator("list_objects_v2")
    try:
        for page in paginator.paginate(Bucket=s3_bucket, Prefix=s3_prefix):
            if "Contents" in page:
                for obj in page["Contents"]:
                    key = obj["Key"]
                    s3_objects[key] = {
                        "ETag": obj["ETag"].strip('"'),  # ETag는 따옴표로 둘러싸여 있음
                        "Size": obj["Size"],
                        "LastModified": obj["LastModified"],
                    }
    except Exception as e:
        console.print(f"[bold red]오류: S3 객체 목록 가져오기 실패: {e}[/bold red]")
        raise typer.Exit(code=1) from e

    local_files = set()
    upload_count = 0
    skip_count = 0
    delete_count = 0

    for local_path in src_path.glob("**/*"):
        if local_path.is_file():
            rel_path = local_path.relative_to(src_path)
            s3_key = f"{s3_prefix}{str(rel_path).replace(os.sep, '/')}"
            local_files.add(s3_key)

            if s3_key in s3_objects:
                s3_obj = s3_objects[s3_key]
                local_size = local_path.stat().st_size
                local_mtime = local_path.stat().st_mtime

                local_md5 = calculate_file_md5(local_path)

                if local_md5 is not None and local_md5 == s3_obj["ETag"]:
                    skip_count += 1
                    continue
                elif local_md5 is None:
                    s3_mtime = s3_obj["LastModified"].timestamp()
                    if local_size == s3_obj["Size"] and local_mtime <= s3_mtime:
                        skip_count += 1
                        continue

            try:
                with tqdm(
                    total=local_path.stat().st_size,
                    unit="B",
                    unit_scale=True,
                    desc=f"업로드: {rel_path}",
                ) as pbar:
                    s3_client.upload_file(
                        str(local_path),
                        s3_bucket,
                        s3_key,
                        Callback=lambda bytes_transferred: pbar.update(
                            bytes_transferred
                        ),
                    )
                upload_count += 1
            except Exception as e:
                console.print(
                    f"[bold red]오류: '{rel_path}' 업로드 실패: {e}[/bold red]"
                )

    if delete:
        objects_to_delete = [key for key in s3_objects if key not in local_files]
        if objects_to_delete:
            console.print(
                f"[yellow]S3에서 {len(objects_to_delete)}개 객체 삭제 중...[/yellow]"
            )

            for i in range(0, len(objects_to_delete), 1000):
                batch = objects_to_delete[i : i + 1000]
                try:
                    s3_client.delete_objects(
                        Bucket=s3_bucket,
                        Delete={"Objects": [{"Key": key} for key in batch]},
                    )
                    delete_count += len(batch)
                except Exception as e:
                    console.print(f"[bold red]오류: 객체 삭제 실패: {e}[/bold red]")

    console.print(
        f"[bold green]동기화 완료: {upload_count} 업로드, {skip_count} 스킵, "
        f"{delete_count} 삭제되었음.[/bold green]"
    )
