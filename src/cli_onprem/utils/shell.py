"""셸 명령 실행 유틸리티."""

import subprocess
from typing import Any, List


def run_command(
    cmd: List[str],
    check: bool = True,
    capture_output: bool = False,
    text: bool = True,
    **kwargs: Any,
) -> subprocess.CompletedProcess[str]:
    """셸 명령을 실행합니다.

    Args:
        cmd: 실행할 명령어 리스트
        check: 오류 시 예외 발생 여부
        capture_output: 출력 캡처 여부
        text: 텍스트 모드 사용 여부
        **kwargs: subprocess.run에 전달할 추가 인자

    Returns:
        실행 결과

    Raises:
        subprocess.CalledProcessError: check=True이고 명령이 실패한 경우
    """
    return subprocess.run(
        cmd, check=check, capture_output=capture_output, text=text, **kwargs
    )


def check_command_exists(command: str) -> bool:
    """명령어가 시스템에 존재하는지 확인합니다.

    Args:
        command: 확인할 명령어

    Returns:
        명령어 존재 여부
    """
    import shutil

    return shutil.which(command) is not None
