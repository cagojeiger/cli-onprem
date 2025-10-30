"""Docker 관련 비즈니스 로직."""

import os
import re
import subprocess
import time
from typing import Any, List, Optional, Set, Tuple

import yaml

from cli_onprem.core.errors import (
    CommandError,
    DependencyError,
    PermanentError,
    TransientError,
)
from cli_onprem.core.logging import get_logger
from cli_onprem.core.types import ImageSet
from cli_onprem.utils.shell import (
    QUICK_TIMEOUT,
    VERY_LONG_TIMEOUT,
    check_command_exists,
)

logger = get_logger("services.docker")

# 기본 레지스트리 목록
DEFAULT_REGISTRIES = [
    "docker.io",
    "quay.io",
    "gcr.io",
    "registry.k8s.io",
    "ghcr.io",
    "nvcr.io",
    "public.ecr.aws",
]


def extract_images_from_text(
    text: str, registries: Optional[List[str]] = None
) -> Set[str]:
    """텍스트에서 정규식으로 컨테이너 이미지 참조를 추출합니다.

    Args:
        text: 검색할 텍스트
        registries: 검색할 레지스트리 목록 (기본값: 환경변수 또는 일반적인 레지스트리)

    Returns:
        발견된 이미지 세트
    """
    if registries is None:
        # 환경변수에서 추가 레지스트리 읽기
        env_registries = os.environ.get("CLI_ONPREM_REGISTRIES", "")
        registries = DEFAULT_REGISTRIES.copy()
        if env_registries:
            registries.extend(
                [r.strip() for r in env_registries.split(",") if r.strip()]
            )

    # 레지스트리 패턴 생성
    registry_pattern = "|".join(re.escape(reg) for reg in registries)

    # 이미지 참조 정규식 패턴
    # 형식: (registry/)?(namespace/)?image(:tag|@digest)?
    image_pattern = rf"""
        (?:^|[\s"'=])                           # 시작 또는 공백, 따옴표, = 뒤
        ((?:{registry_pattern})/)                # 레지스트리
        ([a-z0-9_-]+(?:/[a-z0-9_-]+)*)          # 네임스페이스/이미지
        (?::([a-z0-9_.-]+)|@(sha256:[a-f0-9]{{64}}))?  # 태그 또는 다이제스트
        (?:$|[\s"'])                            # 끝 또는 공백, 따옴표
    """

    pattern = re.compile(image_pattern, re.VERBOSE | re.IGNORECASE)
    images = set()

    for match in pattern.finditer(text):
        registry = match.group(1).rstrip("/") if match.group(1) else ""
        image_path = match.group(2)
        tag = match.group(3)
        digest = match.group(4)

        if registry and image_path:
            full_image = f"{registry}/{image_path}"
            if digest:
                full_image = f"{full_image}@{digest}"
            elif tag:
                full_image = f"{full_image}:{tag}"
            else:
                full_image = f"{full_image}:latest"

            images.add(full_image)

    return images


def normalize_image_name(image: str) -> str:
    """Docker 이미지 이름을 표준화합니다.

    표준 형식: [REGISTRY_HOST[:PORT]/][NAMESPACE/]REPOSITORY[:TAG][@DIGEST]

    표준화 규칙:
    1. 레지스트리 생략 → docker.io 적용 (Docker Hub)
    2. 네임스페이스 생략 → library 적용 (Docker Hub 전용)
    3. 태그 생략 → latest 적용

    Args:
        image: 원본 이미지 이름

    Returns:
        표준화된 이미지 이름

    예시:
        nginx → docker.io/library/nginx:latest
        user/repo → docker.io/user/repo:latest
        nvcr.io/nvidia → nvcr.io/nvidia:latest
        nvcr.io/nvidia/cuda → nvcr.io/nvidia/cuda:latest
    """
    has_digest = "@" in image
    digest_part = ""

    if has_digest:
        base_part, digest_part = image.split("@", 1)
        image = base_part

    has_tag = ":" in image and not (
        ":" in image.split("/", 1)[0] if "/" in image else False
    )
    tag_part = "latest"  # 기본값

    if has_tag:
        image_part, tag_part = image.split(":", 1)
        image = image_part

    has_domain = False
    domain_part = ""
    remaining_part = image

    if "/" in image:
        domain_candidate, remaining = image.split("/", 1)
        if (
            ("." in domain_candidate)
            or (domain_candidate == "localhost")
            or (":" in domain_candidate)
        ):
            has_domain = True
            domain_part = domain_candidate
            remaining_part = remaining

    if has_domain:
        normalized = f"{domain_part}/{remaining_part}"
    else:
        # Docker Hub 처리
        slash_count = remaining_part.count("/")
        if slash_count == 0:
            # 공식 이미지 (예: nginx)
            normalized = f"docker.io/library/{remaining_part}"
        else:
            # 사용자/조직 이미지 (예: user/repo)
            normalized = f"docker.io/{remaining_part}"

    # 태그 추가
    if has_digest:
        normalized = f"{normalized}@{digest_part}"
    else:
        normalized = f"{normalized}:{tag_part}"

    return normalized


def extract_images_from_yaml(
    yaml_content: str, normalize: bool = True, extract_from_text: bool = True
) -> List[str]:
    """YAML 문서에서 이미지 참조를 파싱하고 정렬된 목록을 반환합니다.

    Args:
        yaml_content: 렌더링된 Kubernetes 매니페스트
        normalize: 이미지 이름 정규화 여부
        extract_from_text: 텍스트 패턴 매칭으로 추가 이미지 추출 여부

    Returns:
        정렬된 이미지 목록
    """
    logger.info("렌더링된 매니페스트에서 이미지 수집 중")
    images: ImageSet = set()
    doc_count = 0

    for doc in yaml.safe_load_all(yaml_content):
        if doc is not None:
            doc_count += 1
            _traverse(doc, images)

    logger.info(f"총 {doc_count}개 문서 처리, {len(images)}개 고유 이미지 발견")

    # 텍스트 기반 추가 이미지 추출
    if extract_from_text:
        text_images = extract_images_from_text(yaml_content)
        if text_images:
            logger.info(f"텍스트 패턴 매칭으로 {len(text_images)}개 추가 이미지 발견")
            images.update(text_images)

    if normalize:
        normalized_images = {normalize_image_name(img) for img in images}
        logger.info(f"표준화 후 {len(normalized_images)}개 고유 이미지 남음")
        return sorted(normalized_images)
    else:
        return sorted(images)


def _traverse(obj: Any, images: ImageSet) -> None:
    """객체를 재귀적으로 순회하여 이미지 참조를 수집합니다.

    다음 패턴들을 찾습니다:
    1. 완전한 이미지 문자열 필드 (image: "repo:tag")
    2. 분리된 필드 조합:
       - repository + tag/version/digest
       - repository + image + tag/version

    Args:
        obj: 순회할 객체 (딕셔너리 또는 리스트)
        images: 발견된 이미지를 저장할 세트
    """
    if isinstance(obj, dict):
        img_val = obj.get("image")
        if isinstance(img_val, str) and not obj.get("repository"):
            images.add(img_val)

        repo = obj.get("repository")
        img = obj.get("image")
        tag = obj.get("tag") or obj.get("version")
        digest = obj.get("digest")

        if isinstance(repo, str):
            if isinstance(img, str):
                full_repo = f"{repo}/{img}"
            else:
                full_repo = repo

            if isinstance(tag, str) or isinstance(digest, str):
                _add_repo_tag_digest(
                    images,
                    full_repo,
                    tag if isinstance(tag, str) else None,
                    digest if isinstance(digest, str) else None,
                )

        for value in obj.values():
            _traverse(value, images)

    elif isinstance(obj, list):
        for item in obj:
            _traverse(item, images)


def _add_repo_tag_digest(
    images: ImageSet, repo: str, tag: Optional[str], digest: Optional[str]
) -> None:
    """저장소와 태그 또는 다이제스트를 결합하여 이미지 세트에 추가합니다.

    Args:
        images: 이미지 세트
        repo: 이미지 저장소
        tag: 이미지 태그 (선택적)
        digest: 이미지 다이제스트 (선택적)
    """
    if tag:
        images.add(f"{repo}:{tag}")
    elif digest:
        images.add(f"{repo}@{digest}")
    else:
        images.add(repo)


def check_docker_installed() -> None:
    """Docker CLI가 설치되어 있는지 확인합니다.

    Raises:
        DependencyError: Docker CLI가 설치되어 있지 않은 경우
    """
    if not check_command_exists("docker"):
        raise DependencyError(
            "Docker CLI가 설치되어 있지 않습니다. "
            "설치 방법: https://docs.docker.com/engine/install/"
        )


def check_docker_daemon() -> None:
    """Docker daemon이 실행 중인지 확인합니다.

    빠른 실패(fail-fast)를 위해 Docker 명령 실행 전에 호출합니다.

    Raises:
        DependencyError: Docker daemon이 실행되지 않거나 응답하지 않는 경우
    """
    try:
        subprocess.run(
            ["docker", "info"],
            check=True,
            capture_output=True,
            text=True,
            timeout=QUICK_TIMEOUT,
        )
        logger.debug("Docker daemon 상태 확인 완료")
    except subprocess.TimeoutExpired as e:
        raise DependencyError(
            "Docker daemon이 응답하지 않습니다.\n\n"
            "해결 방법:\n"
            "  1. Docker Desktop이 실행 중인지 확인하세요\n"
            "  2. Docker daemon을 재시작하세요\n"
            "  3. 시스템 리소스(CPU, 메모리)를 확인하세요"
        ) from e
    except subprocess.CalledProcessError as e:
        stderr = e.stderr or ""
        raise DependencyError(
            "Docker daemon이 실행되지 않았습니다.\n\n"
            "해결 방법:\n"
            "  1. Docker Desktop을 시작하세요\n"
            "  2. Linux: sudo systemctl start docker\n"
            "  3. macOS/Windows: Docker Desktop 애플리케이션 실행\n\n"
            f"상세 오류:\n{stderr}"
        ) from e
    except FileNotFoundError as e:
        raise DependencyError(
            "Docker CLI가 설치되어 있지 않습니다. "
            "설치 방법: https://docs.docker.com/engine/install/"
        ) from e


def _parse_docker_error(stderr: str, reference: str) -> str:
    """Docker 에러를 사용자 친화적인 한국어 메시지로 변환.

    Args:
        stderr: Docker CLI의 stderr 출력
        reference: 이미지 참조 (예: nginx:latest)

    Returns:
        파싱된 사용자 친화적 메시지
    """
    stderr_lower = stderr.lower()

    # 인증 관련 오류
    if "denied" in stderr_lower or "unauthorized" in stderr_lower:
        return (
            f"이미지 접근 권한이 없습니다: {reference}\n\n"
            "해결 방법:\n"
            "  1. Private 레지스트리인 경우 로그인하세요: docker login\n"
            "  2. 이미지 이름과 태그를 확인하세요\n"
            "  3. 조직/레포지토리 권한을 확인하세요"
        )

    # 이미지를 찾을 수 없음
    if "not found" in stderr_lower or "manifest unknown" in stderr_lower:
        return (
            f"이미지를 찾을 수 없습니다: {reference}\n\n"
            "해결 방법:\n"
            "  1. 이미지 이름을 확인하세요 (오타 확인)\n"
            "  2. 태그가 존재하는지 확인하세요\n"
            "  3. 레지스트리가 올바른지 확인하세요"
        )

    # 네트워크 관련 오류
    if any(
        word in stderr_lower for word in ["timeout", "network", "connection", "lookup"]
    ):
        return (
            f"네트워크 오류로 이미지 다운로드 실패: {reference}\n\n"
            "해결 방법:\n"
            "  1. 인터넷 연결을 확인하세요\n"
            "  2. VPN이나 프록시 설정을 확인하세요\n"
            "  3. Docker Hub 상태를 확인하세요: https://status.docker.com\n"
            "  4. 잠시 후 다시 시도하세요"
        )

    # 디스크 공간 부족
    if "no space" in stderr_lower or "disk full" in stderr_lower:
        return (
            f"디스크 공간 부족으로 이미지 저장 실패: {reference}\n\n"
            "해결 방법:\n"
            "  1. 디스크 공간을 확보하세요\n"
            "  2. 사용하지 않는 Docker 이미지/컨테이너를 정리하세요:\n"
            "     docker system prune -a"
        )

    # 기타 오류는 원본 메시지 반환
    return f"이미지 작업 실패: {reference}\n\n상세 오류:\n{stderr}"


def _is_retryable_error(stderr: str) -> bool:
    """에러가 재시도 가능한지 판단.

    Args:
        stderr: 명령의 stderr 출력

    Returns:
        재시도 가능하면 True
    """
    retryable_patterns = [
        "timeout",
        "connection refused",
        "connection reset",
        "temporary failure",
        "service unavailable",
        "too many requests",  # Rate limiting
        "503",  # HTTP 503
        "i/o timeout",
        "network",
    ]

    stderr_lower = stderr.lower()
    return any(pattern in stderr_lower for pattern in retryable_patterns)


def parse_image_reference(reference: str) -> Tuple[str, str, str, str]:
    """Docker 이미지 레퍼런스를 분해합니다.

    형식: [<registry>/][<namespace>/]<image>[:<tag>]
    누락 시 기본값:
    - registry: docker.io
    - namespace: library
    - tag: latest

    Args:
        reference: Docker 이미지 레퍼런스

    Returns:
        (registry, namespace, image, tag) 튜플
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


def generate_tar_filename(
    registry: str, namespace: str, image: str, tag: str, arch: str
) -> str:
    """이미지 정보를 기반으로 tar 파일명을 생성합니다.

    형식: [reg__][ns__]image__tag__arch.tar

    Args:
        registry: 레지스트리 (예: docker.io)
        namespace: 네임스페이스 (예: library)
        image: 이미지 이름
        tag: 태그
        arch: 아키텍처

    Returns:
        생성된 파일명
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
    """이미지가 로컬에 존재하는지 확인합니다.

    Args:
        reference: Docker 이미지 레퍼런스

    Returns:
        이미지 존재 여부
    """
    cmd = ["docker", "inspect", "--type=image", reference]
    try:
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=QUICK_TIMEOUT,  # 메타데이터 조회는 빠름
        )
        return True
    except subprocess.CalledProcessError:
        return False


def pull_image(reference: str, arch: str = "linux/amd64", max_retries: int = 3) -> None:
    """이미지를 Docker Hub에서 가져옵니다 (재시도 로직 포함).

    네트워크 관련 일시적 오류는 자동으로 재시도합니다.

    Args:
        reference: Docker 이미지 레퍼런스
        arch: 타겟 아키텍처
        max_retries: 최대 재시도 횟수

    Raises:
        TransientError: 재시도 가능한 일시적 오류
        PermanentError: 재시도 불가능한 영구적 오류
    """
    logger.info(f"이미지 {reference} 다운로드 중 (아키텍처: {arch})")
    cmd = ["docker", "pull", "--platform", arch, reference]

    last_error = ""
    # 첫 시도(0) + 재시도(1, 2, 3) = 총 max_retries + 1번 시도
    for attempt in range(0, max_retries + 1):
        try:
            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                timeout=VERY_LONG_TIMEOUT,
            )
            logger.info(f"이미지 {reference} 다운로드 완료")
            return  # 성공

        except subprocess.CalledProcessError as e:
            last_error = e.stderr or ""

            # 재시도 가능한 에러인지 확인
            if attempt < max_retries and _is_retryable_error(last_error):
                wait_time = 2 ** (attempt + 1)  # Exponential backoff: 2, 4, 8초
                logger.warning(
                    f"이미지 다운로드 실패 (시도 {attempt + 1}/{max_retries + 1}). "
                    f"{wait_time}초 후 재시도... 오류: {last_error[:100]}"
                )
                time.sleep(wait_time)
                continue

            # 재시도 불가능하거나 마지막 시도면 예외 발생
            friendly_message = _parse_docker_error(last_error, reference)

            if _is_retryable_error(last_error):
                raise TransientError(
                    friendly_message, command=cmd, stderr=last_error
                ) from e
            else:
                raise PermanentError(
                    friendly_message, command=cmd, stderr=last_error
                ) from e


def save_image(reference: str, output_path: str) -> None:
    """Docker 이미지를 tar 파일로 저장합니다.

    Args:
        reference: Docker 이미지 레퍼런스
        output_path: 출력 파일 경로

    Raises:
        CommandError: 이미지 저장 실패
    """
    logger.info(f"이미지 {reference}를 {output_path}로 저장 중")
    cmd = ["docker", "save", "-o", output_path, reference]

    try:
        subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=VERY_LONG_TIMEOUT,
        )
        logger.info(f"이미지 저장 완료: {output_path}")
    except subprocess.CalledProcessError as e:
        raise CommandError(f"이미지 저장 실패: {e.stderr}") from e


def save_image_to_stdout(reference: str) -> None:
    """Docker 이미지를 표준 출력으로 내보냅니다.

    Args:
        reference: Docker 이미지 레퍼런스

    Raises:
        CommandError: 이미지 저장 실패
    """
    cmd = ["docker", "save", reference]

    try:
        subprocess.run(
            cmd,
            check=True,
            stderr=subprocess.PIPE,
            text=True,
            timeout=VERY_LONG_TIMEOUT,
        )
    except subprocess.CalledProcessError as e:
        raise CommandError(f"이미지 저장 실패: {e.stderr}") from e


def list_local_images() -> List[str]:
    """로컬에 있는 Docker 이미지 목록을 반환합니다.

    Returns:
        이미지 레퍼런스 목록

    Raises:
        CommandError: 이미지 목록 조회 실패
    """
    try:
        result = subprocess.run(
            ["docker", "images", "--format", "{{.Repository}}:{{.Tag}}"],
            capture_output=True,
            text=True,
            check=True,
            timeout=QUICK_TIMEOUT,  # 로컬 이미지 조회는 빠름
        )
        return result.stdout.splitlines()
    except subprocess.CalledProcessError as e:
        raise CommandError(f"이미지 목록 조회 실패: {e.stderr}") from e
