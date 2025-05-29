"""Helm 차트에서 Docker 이미지 참조를 추출하는 명령어."""

import json
import pathlib
import tempfile
from typing import List, Optional

import typer

from cli_onprem.core.logging import get_logger
from cli_onprem.services import docker, helm
from cli_onprem.services.docker_args import extract_images_from_args

app = typer.Typer(
    help="Helm 차트 관련 로컬 작업",
    no_args_is_help=True,
)

logger = get_logger("commands.helm_local_args")

chart_arg = typer.Argument(
    ...,
    help="Helm 차트 경로 (.tgz 아카이브 또는 디렉토리)",
    exists=True,
)

values_option = typer.Option(
    [],
    "--values",
    "-f",
    help="추가 values 파일 (여러 개 지정 가능)",
)

json_option = typer.Option(
    False,
    "--json",
    help="JSON 형식으로 출력",
)

quiet_option = typer.Option(
    False,
    "--quiet",
    "-q",
    help="로그 메시지 숨기기",
)

raw_option = typer.Option(
    False,
    "--raw",
    help="이미지 이름 정규화 없이 원본 출력",
)

registry_patterns_option = typer.Option(
    None,
    "--registry-pattern",
    "-r",
    help="명령줄 인수에서 이미지를 추출할 때 사용할 레지스트리 패턴 "
    "(여러 개 지정 가능)",
)


@app.command()
def extract_images(
    chart: pathlib.Path = chart_arg,
    values: List[pathlib.Path] = values_option,
    json_output: bool = json_option,
    quiet: bool = quiet_option,
    raw: bool = raw_option,
    registry_patterns: Optional[List[str]] = registry_patterns_option,
) -> None:
    """Helm 차트에서 Docker 이미지 참조를 추출합니다.

    이 명령어는 Helm 차트를 분석하여 사용되는 모든 Docker 이미지 참조를 추출합니다.
    기본 이미지 필드와 명령줄 인수에서 이미지 참조를 모두 찾습니다.
    """
    if quiet:
        logger.setLevel("ERROR")

    helm.check_helm_installed()

    with tempfile.TemporaryDirectory() as workdir:
        chart_path = helm.prepare_chart(chart, pathlib.Path(workdir))

        helm.update_dependencies(chart_path)

        rendered = helm.render_template(chart_path, values)

        images = docker.extract_images_from_yaml(rendered, normalize=not raw)

        arg_images = extract_images_from_args(rendered, registry_patterns)

        all_images = sorted(set(images) | set(arg_images))

        if json_output:
            typer.echo(json.dumps(all_images, indent=2))
        else:
            for image in all_images:
                typer.echo(image)
