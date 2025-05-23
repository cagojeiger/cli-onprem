"""CLI-ONPREM을 위한 Helm 차트 관련 명령어."""

from __future__ import annotations

import logging
import pathlib
import shutil
import subprocess
import sys
import tarfile
import tempfile
from typing import Any, Set

import typer
import yaml
from rich.console import Console
from typing_extensions import Annotated

context_settings = {
    "ignore_unknown_options": True,  # Always allow unknown options
    "allow_extra_args": True,  # Always allow extra args
}

app = typer.Typer(
    help="Helm 차트 관련 작업 수행",
    context_settings=context_settings,
)
console = Console()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stderr,  # 로그를 stderr로 출력
)
logger = logging.getLogger(__name__)

ImageSet = Set[str]


def check_helm_cli_installed() -> None:
    """Helm CLI가 설치되어 있는지 확인합니다.

    설치되어 있지 않은 경우 안내 메시지를 출력하고 프로그램을 종료합니다.
    """
    if shutil.which("helm") is None:
        console.print("[bold red]오류: Helm CLI가 설치되어 있지 않습니다[/bold red]")
        console.print(
            "[yellow]Helm CLI 설치 방법: https://helm.sh/ko/docs/intro/install/[/yellow]"
        )
        raise typer.Exit(code=1)


def extract_chart(chart_archive: pathlib.Path, dest_dir: pathlib.Path) -> pathlib.Path:
    """차트 아카이브를 지정된 디렉토리에 추출하고 차트 루트를 반환합니다.

    Args:
        chart_archive: 추출할 .tgz 형식의 Helm 차트 아카이브
        dest_dir: 추출 대상 디렉토리

    Returns:
        추출된 차트의 루트 디렉토리

    Raises:
        RuntimeError: 예상치 못한 차트 구조일 경우
    """
    logger.info(f"차트 아카이브 추출 중: {chart_archive}")
    with tarfile.open(chart_archive, "r:gz") as tar:
        tar.extractall(dest_dir)

    roots = [p for p in dest_dir.iterdir() if p.is_dir()]
    if len(roots) != 1:
        raise RuntimeError(
            f"Unexpected chart archive structure: {len(roots)} top‑level entries found."
        )
    logger.info(f"차트 루트 디렉토리: {roots[0]}")
    return roots[0]


def prepare_chart(chart_path: pathlib.Path, workdir: pathlib.Path) -> pathlib.Path:
    """압축된 차트 또는 디렉토리 형태의 차트를 준비합니다.

    Args:
        chart_path: .tgz 아카이브 또는 차트 디렉토리 경로
        workdir: 작업 디렉토리

    Returns:
        차트 루트 디렉토리

    Raises:
        FileNotFoundError: 차트 디렉토리가 존재하지 않을 경우
        ValueError: 유효하지 않은 차트 형식이나 구조일 경우
    """
    logger.info(f"차트 준비 중: {chart_path}")

    if chart_path.is_dir():
        if not chart_path.exists():
            raise FileNotFoundError(f"차트 디렉토리가 존재하지 않습니다: {chart_path}")

        if not (chart_path / "Chart.yaml").exists():
            raise ValueError(f"유효한 Helm 차트 디렉토리가 아닙니다: {chart_path}")

        logger.info(f"디렉토리 차트 사용: {chart_path}")
        return chart_path

    elif chart_path.is_file() and chart_path.suffix in [".tgz", ".tar.gz"]:
        logger.info(f"압축된 차트 사용: {chart_path}")
        return extract_chart(chart_path, workdir)

    else:
        raise ValueError(
            f"지원하지 않는 차트 형식입니다: {chart_path} "
            f"(디렉토리 또는 .tgz 파일만 지원)"
        )


def helm_dependency_update(chart_dir: pathlib.Path) -> None:
    """차트 디렉토리에 대해 helm dependency update 명령을 실행합니다.

    의존성이 없는 경우에도 오류를 발생시키지 않습니다.

    Args:
        chart_dir: Helm 차트 디렉토리
    """
    logger.info(f"차트 의존성 업데이트: {chart_dir}")
    subprocess.run(
        ["helm", "dependency", "update", str(chart_dir)],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    logger.info("의존성 업데이트 완료")


def helm_template(chart_dir: pathlib.Path, values_files: list[pathlib.Path]) -> str:
    """차트 디렉토리에 대해 helm template 명령을 실행하고 렌더링된 매니페스트를
    반환합니다.

    Args:
        chart_dir: Helm 차트 디렉토리
        values_files: 추가 values 파일 목록

    Returns:
        렌더링된 Kubernetes 매니페스트

    Raises:
        FileNotFoundError: values 파일이 존재하지 않을 경우
        subprocess.CalledProcessError: helm template 명령 실행 실패 시
    """
    cmd: list[str] = ["helm", "template", "dummy", str(chart_dir)]

    if values_files:
        logger.info(
            f"지정된 values 파일 사용: {', '.join(str(v) for v in values_files)}"
        )
        for vf in values_files:
            abs_path = vf if vf.is_absolute() else pathlib.Path.cwd() / vf
            if not abs_path.exists():
                raise FileNotFoundError(f"Values 파일을 찾을 수 없습니다: {vf}")
            cmd.extend(["-f", str(abs_path)])
    else:
        default_values = chart_dir / "values.yaml"
        if default_values.exists():
            logger.info(f"기본 values.yaml 파일 사용: {default_values}")
            cmd.extend(["-f", str(default_values)])
        else:
            logger.info("사용 가능한 values 파일 없음")

    logger.info(f"차트 템플릿 렌더링 중: {chart_dir}")
    logger.info(f"실행 명령어: {' '.join(cmd)}")

    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return result.stdout


def _add_repo_tag_digest(
    images: ImageSet, repo: str, tag: str | None, digest: str | None
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
        if "/" in remaining_part:
            normalized = f"docker.io/{remaining_part}"
        else:
            normalized = f"docker.io/library/{remaining_part}"

    if has_digest:
        return f"{normalized}@{digest_part}"
    else:
        return f"{normalized}:{tag_part}"


def collect_images(rendered_yaml: str) -> list[str]:
    """렌더링된 YAML 문서에서 이미지 참조를 파싱하고 중복 제거된 정렬 목록을 반환합니다.

    Args:
        rendered_yaml: 렌더링된 Kubernetes 매니페스트

    Returns:
        정렬된 이미지 목록
    """
    logger.info("렌더링된 매니페스트에서 이미지 수집 중")
    images: ImageSet = set()
    doc_count = 0

    for doc in yaml.safe_load_all(rendered_yaml):
        if doc is not None:
            doc_count += 1
            _traverse(doc, images)

    logger.info(f"총 {doc_count}개 문서 처리, {len(images)}개 고유 이미지 발견")

    normalized_images = {normalize_image_name(img) for img in images}
    logger.info(f"표준화 후 {len(normalized_images)}개 고유 이미지 남음")

    return sorted(normalized_images)


def complete_chart_path(incomplete: str) -> list[str]:
    """차트 경로 자동완성: .tgz 파일과 유효한 차트 디렉토리 제안"""

    def fetch_chart_paths() -> list[str]:
        import json
        from pathlib import Path

        matches = []

        for path in Path(".").glob("*"):
            if path.is_dir():
                if (path / "Chart.yaml").exists():
                    matches.append(str(path))
                else:
                    for subdir in path.glob("*/Chart.yaml"):
                        matches.append(str(subdir.parent))

        for path in Path(".").glob("*.tgz"):
            if path.is_file():
                matches.append(str(path))

        if shutil.which("helm") is not None:
            try:
                result = subprocess.run(
                    ["helm", "list", "-o", "json"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                releases = json.loads(result.stdout)
                for release in releases:
                    chart_name = release.get("chart", "")
                    if chart_name:
                        matches.append(chart_name)
            except Exception:
                pass

        return matches

    from cli_onprem.libs.cache import get_cached_data

    matches = get_cached_data("helm_chart_paths", fetch_chart_paths, ttl=300)

    return [m for m in matches if m.startswith(incomplete)]


CHART_ARG = Annotated[
    pathlib.Path,
    typer.Argument(
        ...,
        help="Helm 차트 아카이브(.tgz) 또는 디렉토리 경로",
        autocompletion=complete_chart_path,
    ),
]


def complete_values_file(incomplete: str) -> list[str]:
    """values 파일 자동완성: yaml 파일 제안"""

    def fetch_values_files() -> list[str]:
        from pathlib import Path

        matches = []
        for path in Path(".").glob("*.yaml"):
            if path.is_file():
                matches.append(str(path))
        return matches

    from cli_onprem.libs.cache import get_cached_data

    matches = get_cached_data("helm_values_files", fetch_values_files, ttl=300)

    return [m for m in matches if m.startswith(incomplete)]


VALUES_OPTION = typer.Option(
    [],
    "--values",
    "-f",
    help="추가 values.yaml 파일 경로",
    autocompletion=complete_values_file,
)
QUIET_OPTION = typer.Option(
    False, "--quiet", "-q", help="로그 메시지 출력 안함 (stderr)"
)
JSON_OPTION = typer.Option(False, "--json", help="JSON 배열 형식으로 출력")
RAW_OPTION = typer.Option(
    False, "--raw", help="이미지 이름 표준화 없이 원본 그대로 출력"
)


@app.command()
def extract_images(
    chart: Annotated[
        pathlib.Path,
        typer.Argument(
            help="Helm 차트 아카이브(.tgz) 또는 디렉토리 경로",
            autocompletion=complete_chart_path,
        ),
    ],
    values: list[pathlib.Path] = VALUES_OPTION,
    quiet: bool = QUIET_OPTION,
    json_output: bool = JSON_OPTION,
    raw: bool = RAW_OPTION,
) -> None:
    """Helm 차트에서 사용되는 Docker 이미지 참조를 추출합니다.

    .tgz 형식의 압축된 차트 아카이브 또는 압축이 풀린 차트 디렉토리를
    처리할 수 있습니다.
    추가 values 파일을 지정하여 이미지 버전 등의 설정을 적용할 수 있습니다.

    출력은 기본적으로 각 줄마다 하나의 이미지 참조를 표시하며,
    --json 옵션을 사용하면 JSON 배열 형식으로 출력됩니다.
    """
    if quiet:
        logging.getLogger().setLevel(logging.ERROR)

    check_helm_cli_installed()  # Helm CLI 의존성 확인
    logger.info(f"스크립트 시작: 차트={chart}, values 파일={values or '없음'}")

    with tempfile.TemporaryDirectory() as tmp:
        workdir = pathlib.Path(tmp)
        logger.info(f"임시 작업 디렉토리 생성: {workdir}")

        try:
            chart_root = prepare_chart(chart, workdir)

            helm_dependency_update(chart_root)
            rendered = helm_template(chart_root, values)
            logger.info(f"매니페스트 렌더링 완료: {len(rendered)} 바이트")

            images = collect_images(rendered)

            if images:
                logger.info(f"이미지 추출 완료: {len(images)}개 발견")
                if json_output:
                    import json

                    console.print(json.dumps(images))
                else:
                    for image in images:
                        console.print(image)
            else:
                console.print("[bold red]이미지 필드를 찾을 수 없음[/bold red]")
                raise typer.Exit(code=1)
        except FileNotFoundError as e:
            console.print(f"[bold red]오류: 파일을 찾을 수 없습니다: {e}[/bold red]")
            raise typer.Exit(code=1) from e
        except ValueError as e:
            console.print(f"[bold red]오류: 잘못된 입력 값: {e}[/bold red]")
            raise typer.Exit(code=1) from e
        except subprocess.CalledProcessError as e:
            console.print(f"[bold red]오류: 명령어 실행 실패: {e}[/bold red]")
            raise typer.Exit(code=1) from e
        except Exception as e:
            console.print(f"[bold red]오류 발생: {e}[/bold red]")
            raise typer.Exit(code=1) from None
