"""셸 명령 실행 유틸리티."""

import os
import subprocess
from typing import Any, List, Optional

from cli_onprem.core.errors import CommandError

# 타임아웃 기본값 (환경 변수로 재정의 가능)
QUICK_TIMEOUT = int(os.getenv("CLI_ONPREM_QUICK_TIMEOUT", "30"))  # 30초
DEFAULT_TIMEOUT = int(os.getenv("CLI_ONPREM_TIMEOUT", "300"))  # 5분
MEDIUM_TIMEOUT = int(os.getenv("CLI_ONPREM_MEDIUM_TIMEOUT", "600"))  # 10분
LONG_TIMEOUT = int(os.getenv("CLI_ONPREM_LONG_TIMEOUT", "1800"))  # 30분
VERY_LONG_TIMEOUT = int(os.getenv("CLI_ONPREM_VERY_LONG_TIMEOUT", "3600"))  # 60분


def run_command(
    cmd: List[str],
    check: bool = True,
    capture_output: bool = False,
    text: bool = True,
    timeout: Optional[int] = DEFAULT_TIMEOUT,
    **kwargs: Any,
) -> subprocess.CompletedProcess[str]:
    """셸 명령을 실행합니다.

    Args:
        cmd: 실행할 명령어 리스트
        check: 오류 시 예외 발생 여부
        capture_output: 출력 캡처 여부
        text: 텍스트 모드 사용 여부
        timeout: 타임아웃 (초). None이면 무제한 대기
        **kwargs: subprocess.run에 전달할 추가 인자

    Returns:
        실행 결과

    Raises:
        subprocess.CalledProcessError: check=True이고 명령이 실패한 경우
        CommandError: 타임아웃 발생 시
    """
    try:
        return subprocess.run(
            cmd,
            check=check,
            capture_output=capture_output,
            text=text,
            timeout=timeout,
            **kwargs,
        )
    except subprocess.TimeoutExpired as e:
        # 친절한 에러 메시지 (해결 방법 포함)
        cmd_str = " ".join(cmd[:3])
        if len(cmd) > 3:
            cmd_str += "..."
        raise CommandError(
            f"명령어가 {timeout}초 후 타임아웃되었습니다: {cmd_str}\n"
            "💡 힌트: 대용량 작업의 경우 CLI_ONPREM_LONG_TIMEOUT=7200 으로 "
            "시간을 늘려보세요."
        ) from e


def check_command_exists(command: str) -> bool:
    """명령어가 시스템에 존재하는지 확인합니다.

    Args:
        command: 확인할 명령어

    Returns:
        명령어 존재 여부
    """
    import shutil

    return shutil.which(command) is not None
