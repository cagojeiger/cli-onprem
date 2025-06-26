"""CLI-ONPREM을 위한 Helm 차트 관련 명령어."""

from __future__ import annotations

import pathlib
import subprocess
import tempfile

import typer
from rich.console import Console
from typing_extensions import Annotated

from cli_onprem.core.errors import handle_error
from cli_onprem.core.logging import init_logging, set_log_level
from cli_onprem.core.types import CONTEXT_SETTINGS
from cli_onprem.services import docker, helm
from cli_onprem.utils import formatting

app = typer.Typer(
    help="Helm 차트 관련 작업 수행",
    context_settings=CONTEXT_SETTINGS,
)
console = Console()


def complete_chart_path(incomplete: str) -> list[str]:
    """차트 경로 자동완성: .tgz 파일과 유효한 차트 디렉토리 제안"""

    def fetch_chart_paths() -> list[str]:
        from pathlib import Path

        matches = []

        # .tgz 파일 찾기
        for path in Path(".").glob("*.tgz"):
            matches.append(str(path))

        # 차트 디렉토리 찾기 (Chart.yaml 포함)
        for path in Path(".").iterdir():
            if path.is_dir() and (path / "Chart.yaml").exists():
                matches.append(str(path))

        return matches

    matches = fetch_chart_paths()
    return [m for m in matches if m.startswith(incomplete)]


def complete_values_file(incomplete: str) -> list[str]:
    """values 파일 자동완성: yaml 파일 제안"""

    def fetch_values_files() -> list[str]:
        from pathlib import Path

        matches = []
        for path in Path(".").glob("*.yaml"):
            if path.is_file():
                matches.append(str(path))
        return matches

    matches = fetch_values_files()
    return [m for m in matches if m.startswith(incomplete)]


# CLI Options
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
SKIP_DEPENDENCY_UPDATE_OPTION = typer.Option(
    False,
    "--skip-dependency-update",
    help="차트 의존성 업데이트를 건너뛰고 빠르게 실행",
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
    skip_dependency_update: bool = SKIP_DEPENDENCY_UPDATE_OPTION,
) -> None:
    """Helm 차트에서 사용되는 Docker 이미지 참조를 추출합니다.

    .tgz 형식의 압축된 차트 아카이브 또는 압축이 풀린 차트 디렉토리를
    처리할 수 있습니다.
    추가 values 파일을 지정하여 이미지 버전 등의 설정을 적용할 수 있습니다.

    출력은 기본적으로 각 줄마다 하나의 이미지 참조를 표시하며,
    --json 옵션을 사용하면 JSON 배열 형식으로 출력됩니다.
    """
    # 로깅 초기화
    init_logging()

    if quiet:
        set_log_level("ERROR")

    try:
        # Helm CLI 확인
        helm.check_helm_installed()

        with tempfile.TemporaryDirectory() as tmp:
            workdir = pathlib.Path(tmp)

            # 차트 준비
            chart_root = helm.prepare_chart(chart, workdir)

            # 의존성 업데이트
            if not skip_dependency_update:
                helm.update_dependencies(chart_root)

            # 템플릿 렌더링
            rendered = helm.render_template(chart_root, values)

            # 이미지 추출
            images = docker.extract_images_from_yaml(rendered, normalize=not raw)

            if images:
                # 출력
                if json_output:
                    console.print(formatting.format_json(images))
                else:
                    for image in images:
                        console.print(image)
            else:
                console.print("[bold red]이미지 필드를 찾을 수 없음[/bold red]")
                raise typer.Exit(code=1)

    except FileNotFoundError as e:
        handle_error(e)
    except ValueError as e:
        handle_error(e)
    except subprocess.CalledProcessError as e:
        handle_error(Exception(f"명령어 실행 실패: {e}"))
    except Exception as e:
        handle_error(e)
