"""Helm 관련 비즈니스 로직."""

import pathlib
import subprocess
from typing import List, Optional

from cli_onprem.core.errors import check_command_installed
from cli_onprem.core.logging import get_logger
from cli_onprem.utils import file, shell

logger = get_logger("services.helm")


def check_helm_installed() -> None:
    """Helm CLI가 설치되어 있는지 확인합니다.

    Raises:
        typer.Exit: Helm이 설치되어 있지 않은 경우
    """
    check_command_installed("helm", "https://helm.sh/docs/intro/install/")


def extract_chart(archive_path: pathlib.Path, dest_dir: pathlib.Path) -> pathlib.Path:
    """압축된 Helm 차트를 추출하고 차트 루트 디렉토리를 반환합니다.

    Args:
        archive_path: 차트 아카이브 경로 (.tgz)
        dest_dir: 추출할 대상 디렉토리

    Returns:
        차트 루트 디렉토리 경로

    Raises:
        ValueError: 차트 디렉토리를 찾을 수 없는 경우
    """
    logger.info(f"차트 추출 중: {archive_path} → {dest_dir}")

    # tar 파일 추출
    file.extract_tar(archive_path, dest_dir)

    # 차트 루트 디렉토리 찾기 (Chart.yaml이 있는 디렉토리)
    for item in dest_dir.iterdir():
        if item.is_dir() and (item / "Chart.yaml").exists():
            logger.info(f"차트 루트 발견: {item}")
            return item

    raise ValueError(f"차트 디렉토리를 찾을 수 없습니다 (Chart.yaml 없음): {dest_dir}")


def prepare_chart(chart_path: pathlib.Path, workdir: pathlib.Path) -> pathlib.Path:
    """차트 경로를 준비합니다.

    디렉토리인 경우 그대로 사용하고, 아카이브인 경우 추출합니다.

    Args:
        chart_path: 차트 경로 (디렉토리 또는 .tgz 파일)
        workdir: 작업 디렉토리 (아카이브 추출 시 사용)

    Returns:
        사용 가능한 차트 디렉토리 경로

    Raises:
        ValueError: 지원하지 않는 차트 형식인 경우
    """
    if chart_path.is_dir():
        # 유효한 차트 디렉토리인지 확인
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


def update_dependencies(chart_dir: pathlib.Path) -> None:
    """차트 디렉토리에 대해 helm dependency update 명령을 실행합니다.

    의존성이 없는 경우에도 오류를 발생시키지 않습니다.

    Args:
        chart_dir: Helm 차트 디렉토리
    """
    logger.info(f"차트 의존성 업데이트: {chart_dir}")

    shell.run_command(
        ["helm", "dependency", "update", str(chart_dir)],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    logger.info("의존성 업데이트 완료")


def render_template(
    chart_dir: pathlib.Path, values_files: Optional[List[pathlib.Path]] = None
) -> str:
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
    cmd: List[str] = ["helm", "template", "dummy", str(chart_dir)]

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

    result = shell.run_command(cmd, capture_output=True)
    return result.stdout if result.stdout else ""
