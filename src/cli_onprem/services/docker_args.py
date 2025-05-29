"""명령줄 인수에서 Docker 이미지 참조를 추출하는 기능."""

import os
import re
from typing import List, Optional, Set

from cli_onprem.core.logging import get_logger

logger = get_logger("services.docker_args")

DEFAULT_REGISTRY_PATTERNS = [
    "quay.io",
    "docker.io",
    "registry.k8s.io",
    "gcr.io",
    "ghcr.io",
    "mcr.microsoft.com",
]


def extract_images_from_args(
    yaml_content: str, registry_patterns: Optional[List[str]] = None
) -> List[str]:
    """명령줄 인수에서 Docker 이미지 참조를 추출합니다.

    Args:
        yaml_content: 렌더링된 Kubernetes 매니페스트
        registry_patterns: 검색할 레지스트리 패턴 목록
            (기본값: DEFAULT_REGISTRY_PATTERNS)

    Returns:
        추출된 이미지 목록 (정렬됨)
    """
    if registry_patterns is None:
        registry_patterns = DEFAULT_REGISTRY_PATTERNS.copy()

    env_patterns = os.environ.get("CLI_ONPREM_REGISTRY_PATTERNS", "")
    if env_patterns:
        registry_patterns.extend(
            [p.strip() for p in env_patterns.split(",") if p.strip()]
        )

    logger.info(f"레지스트리 패턴 목록: {', '.join(registry_patterns)}")

    images: Set[str] = set()
    pattern_parts = []

    for registry in registry_patterns:
        pattern_parts.append(f"{re.escape(registry)}/[^=\\s\"']+")

    pattern = (
        r'(?:--[^=]+=|-[^=]+=|=|["\']|:\s+)('
        + "|".join(pattern_parts)
        + r')(?:["\']|$|\s)'
    )

    logger.debug(f"사용 정규식 패턴: {pattern}")

    for match in re.finditer(pattern, yaml_content):
        image = match.group(1)
        logger.debug(f"발견된 이미지: {image}")
        images.add(image)

    logger.info(f"명령줄 인수에서 {len(images)}개 이미지 발견")
    return sorted(images)
