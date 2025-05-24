"""Docker 관련 비즈니스 로직."""

from typing import Any, List, Optional

import yaml

from cli_onprem.core.logging import get_logger
from cli_onprem.core.types import ImageSet

logger = get_logger("services.docker")


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


def extract_images_from_yaml(yaml_content: str, normalize: bool = True) -> List[str]:
    """YAML 문서에서 이미지 참조를 파싱하고 정렬된 목록을 반환합니다.

    Args:
        yaml_content: 렌더링된 Kubernetes 매니페스트
        normalize: 이미지 이름 정규화 여부

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
