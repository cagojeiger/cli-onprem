"""S3 관련 비즈니스 로직."""

import datetime
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import boto3
from botocore.exceptions import ClientError  # type: ignore[import-untyped]

from cli_onprem.core.errors import CLIError
from cli_onprem.core.logging import get_logger

logger = get_logger("services.s3")


def create_s3_client(aws_access_key: str, aws_secret_key: str, region: str) -> Any:
    """S3 클라이언트를 생성합니다.

    Args:
        aws_access_key: AWS Access Key
        aws_secret_key: AWS Secret Key
        region: AWS 리전

    Returns:
        S3 클라이언트 객체
    """
    return boto3.client(
        "s3",
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name=region,
    )


def list_buckets(s3_client: Any) -> List[str]:
    """S3 버킷 목록을 조회합니다.

    Args:
        s3_client: S3 클라이언트

    Returns:
        버킷 이름 리스트

    Raises:
        CLIError: 버킷 목록 조회 실패
    """
    try:
        response = s3_client.list_buckets()
        buckets = [bucket["Name"] for bucket in response.get("Buckets", [])]
        logger.debug(f"{len(buckets)}개의 버킷 조회됨")
        return buckets
    except ClientError as e:
        raise CLIError(f"버킷 목록 조회 실패: {e}") from e


def list_objects(
    s3_client: Any, bucket: str, prefix: str = "", delimiter: str = "/"
) -> Tuple[List[str], List[Dict[str, Any]]]:
    """S3 객체 목록을 조회합니다.

    Args:
        s3_client: S3 클라이언트
        bucket: 버킷 이름
        prefix: 프리픽스
        delimiter: 구분자

    Returns:
        (프리픽스 리스트, 객체 정보 리스트) 튜플

    Raises:
        CLIError: 객체 목록 조회 실패
    """
    try:
        paginator = s3_client.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(
            Bucket=bucket, Prefix=prefix, Delimiter=delimiter
        )

        prefixes = []
        objects = []

        for page in page_iterator:
            if "CommonPrefixes" in page:
                for prefix_info in page["CommonPrefixes"]:
                    prefixes.append(prefix_info["Prefix"])

            if "Contents" in page:
                for obj in page["Contents"]:
                    objects.append(
                        {
                            "Key": obj["Key"],
                            "Size": obj["Size"],
                            "LastModified": obj["LastModified"],
                            "ETag": obj["ETag"].strip('"'),
                        }
                    )

        logger.debug(f"{len(prefixes)}개 프리픽스, {len(objects)}개 객체 조회됨")
        return prefixes, objects

    except ClientError as e:
        raise CLIError(f"객체 목록 조회 실패: {e}") from e


def upload_file(
    s3_client: Any,
    local_path: Path,
    bucket: str,
    key: str,
    callback: Optional[Callable[[int], None]] = None,
) -> None:
    """파일을 S3에 업로드합니다.

    Args:
        s3_client: S3 클라이언트
        local_path: 로컬 파일 경로
        bucket: 대상 버킷
        key: S3 키
        callback: 진행률 콜백 함수

    Raises:
        CLIError: 업로드 실패
    """
    try:
        logger.info(f"{local_path} -> s3://{bucket}/{key} 업로드 중")
        s3_client.upload_file(str(local_path), bucket, key, Callback=callback)
        logger.info(f"업로드 완료: {key}")
    except ClientError as e:
        raise CLIError(f"'{local_path}' 업로드 실패: {e}") from e


def delete_objects(
    s3_client: Any, bucket: str, keys: List[str], batch_size: int = 1000
) -> int:
    """S3 객체들을 삭제합니다.

    Args:
        s3_client: S3 클라이언트
        bucket: 버킷 이름
        keys: 삭제할 키 리스트
        batch_size: 배치 크기

    Returns:
        삭제된 객체 수

    Raises:
        CLIError: 삭제 실패
    """
    if not keys:
        return 0

    deleted_count = 0

    try:
        # 배치 단위로 삭제
        for i in range(0, len(keys), batch_size):
            batch = keys[i : i + batch_size]

            response = s3_client.delete_objects(
                Bucket=bucket, Delete={"Objects": [{"Key": key} for key in batch]}
            )

            deleted_count += len(response.get("Deleted", []))

            # 오류 확인
            errors = response.get("Errors", [])
            if errors:
                logger.warning(f"일부 객체 삭제 실패: {errors}")

        logger.info(f"{deleted_count}개 객체 삭제됨")
        return deleted_count

    except ClientError as e:
        raise CLIError(f"객체 삭제 실패: {e}") from e


def generate_presigned_url(
    s3_client: Any, bucket: str, key: str, expires_in: int = 3600
) -> str:
    """Presigned URL을 생성합니다.

    Args:
        s3_client: S3 클라이언트
        bucket: 버킷 이름
        key: 객체 키
        expires_in: 만료 시간(초)

    Returns:
        Presigned URL

    Raises:
        CLIError: URL 생성 실패
    """
    try:
        url = s3_client.generate_presigned_url(
            "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=expires_in
        )
        logger.debug(f"Presigned URL 생성됨: {key}")
        return str(url)
    except ClientError as e:
        raise CLIError(f"Presigned URL 생성 실패: {e}") from e


def head_object(s3_client: Any, bucket: str, key: str) -> Dict[str, Any]:
    """객체의 메타데이터를 조회합니다.

    Args:
        s3_client: S3 클라이언트
        bucket: 버킷 이름
        key: 객체 키

    Returns:
        객체 메타데이터

    Raises:
        CLIError: 조회 실패
    """
    try:
        response = s3_client.head_object(Bucket=bucket, Key=key)
        return {
            "ContentLength": response["ContentLength"],
            "ETag": response.get("ETag", "").strip('"'),
            "LastModified": response.get("LastModified"),
        }
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            raise CLIError(f"객체를 찾을 수 없습니다: s3://{bucket}/{key}") from e
        raise CLIError(f"객체 조회 실패: {e}") from e


def sync_to_s3(
    s3_client: Any,
    local_path: Path,
    bucket: str,
    prefix: str,
    delete: bool = False,
    upload_callback: Optional[Callable[[Path, str, int], None]] = None,
) -> Tuple[int, int, int]:
    """로컬 디렉터리를 S3와 동기화합니다.

    Args:
        s3_client: S3 클라이언트
        local_path: 로컬 경로
        bucket: 대상 버킷
        prefix: S3 프리픽스
        delete: 원본에 없는 객체 삭제 여부
        upload_callback: 업로드 콜백 (로컬 경로, S3 키, 크기)

    Returns:
        (업로드 수, 스킵 수, 삭제 수) 튜플
    """
    # S3 객체 목록 조회
    _, s3_objects = list_objects(s3_client, bucket, prefix, delimiter="")
    s3_object_map = {obj["Key"]: obj for obj in s3_objects}

    upload_count = 0
    skip_count = 0
    delete_count = 0
    local_keys = set()

    # 디렉터리인 경우
    if local_path.is_dir():
        for file_path in local_path.glob("**/*"):
            if file_path.is_file():
                rel_path = file_path.relative_to(local_path)
                s3_key = f"{prefix}{str(rel_path).replace(os.sep, '/')}"
                local_keys.add(s3_key)

                # 업로드 필요 여부 확인
                if _should_upload(file_path, s3_key, s3_object_map):
                    if upload_callback:
                        upload_callback(file_path, s3_key, file_path.stat().st_size)
                    else:
                        upload_file(s3_client, file_path, bucket, s3_key)
                    upload_count += 1
                else:
                    skip_count += 1
    else:
        # 단일 파일인 경우
        s3_key = prefix
        local_keys.add(s3_key)

        if _should_upload(local_path, s3_key, s3_object_map):
            if upload_callback:
                upload_callback(local_path, s3_key, local_path.stat().st_size)
            else:
                upload_file(s3_client, local_path, bucket, s3_key)
            upload_count += 1
        else:
            skip_count += 1

    # 삭제 처리
    if delete:
        keys_to_delete = [key for key in s3_object_map if key not in local_keys]
        if keys_to_delete:
            delete_count = delete_objects(s3_client, bucket, keys_to_delete)

    return upload_count, skip_count, delete_count


def _should_upload(
    local_path: Path, s3_key: str, s3_object_map: Dict[str, Dict[str, Any]]
) -> bool:
    """파일 업로드가 필요한지 확인합니다.

    Args:
        local_path: 로컬 파일 경로
        s3_key: S3 키
        s3_object_map: S3 객체 정보 맵

    Returns:
        업로드 필요 여부
    """
    if s3_key not in s3_object_map:
        return True

    s3_obj = s3_object_map[s3_key]
    local_size = local_path.stat().st_size

    # 크기가 다르면 업로드
    if local_size != s3_obj["Size"]:
        return True

    # ETag로 비교 (작은 파일만)
    if local_size < 5 * 1024 * 1024 * 1024:  # 5GB 미만
        from cli_onprem.utils.hash import calculate_file_md5

        local_md5 = calculate_file_md5(local_path)
        if local_md5 and local_md5 != s3_obj["ETag"]:
            return True

    # 수정 시간으로 비교
    local_mtime = local_path.stat().st_mtime
    s3_mtime = s3_obj["LastModified"].timestamp()
    if local_mtime > s3_mtime:
        return True

    return False


def generate_s3_path(src_path: Path, s3_prefix: str) -> str:
    """S3 업로드 경로를 생성합니다.

    Args:
        src_path: 소스 파일 또는 디렉터리 경로
        s3_prefix: S3 프리픽스

    Returns:
        S3 경로 (프리픽스 포함)
    """
    date_str = datetime.datetime.now().strftime("%Y%m%d")
    if src_path.is_dir():
        folder_name = src_path.name
        return f"{s3_prefix}cli-onprem-{date_str}-{folder_name}/"
    else:
        file_name = src_path.name
        return f"{s3_prefix}cli-onprem-{date_str}-{file_name}"
