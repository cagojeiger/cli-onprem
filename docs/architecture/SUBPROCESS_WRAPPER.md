# Subprocess 래퍼 설계 문서

> **접근법**: 최소주의 (Minimalist Approach)
> **원칙**: 오캄의 면도날 - 복잡한 추상화보다 간단하고 효과적인 해결책

## 목차

- [설계 철학](#설계-철학)
- [구현 범위](#구현-범위)
- [API 설계](#api-설계)
- [마이그레이션 가이드](#마이그레이션-가이드)
- [사용 예제](#사용-예제)

## 설계 철학

### 왜 최소주의인가?

Gemini Agent의 조언:
> "복잡한 Circuit Breaker나 의존성 주입을 도입하기 전에, 기본적인 것부터 철저히 해야 합니다."

현재 문제:
- ❌ subprocess 호출 패턴 불일치
- ❌ 타임아웃 없음 → 무한 대기 가능
- ❌ 로깅 없음 → 디버깅 어려움
- ❌ 에러 컨텍스트 부족

최소주의 해결책:
- ✅ 타임아웃 기본값 제공
- ✅ 명령어 로깅 자동화
- ✅ TimeoutExpired 예외 처리
- ✅ 환경변수로 설정 가능

**하지 않는 것** (YAGNI - You Aren't Gonna Need It):
- ❌ Circuit Breaker
- ❌ 의존성 주입
- ❌ Protocol/추상 클래스
- ❌ 자동 재시도 (서비스 레벨에서 필요한 곳만)
- ❌ 진행률 추적 (Rich 라이브러리가 이미 제공)

## 구현 범위

### 현재 `utils/shell.py`

```python
def run_command(
    cmd: List[str],
    check: bool = True,
    capture_output: bool = False,
    text: bool = True,
    **kwargs: Any,
) -> subprocess.CompletedProcess[str]:
    """셸 명령을 실행합니다."""
    return subprocess.run(
        cmd,
        check=check,
        capture_output=capture_output,
        text=text,
        **kwargs
    )
```

**문제점**:
1. 타임아웃 없음
2. 명령어가 로깅되지 않음
3. TimeoutExpired가 그대로 전파됨

### 개선된 `utils/shell.py`

```python
import logging
import os
import subprocess
from typing import Any, List, Optional

from cli_onprem.core.errors import CommandError

logger = logging.getLogger(__name__)

# 환경변수로 설정 가능한 기본값
DEFAULT_TIMEOUT = int(os.getenv("CLI_ONPREM_TIMEOUT", "300"))  # 5분
LONG_TIMEOUT = int(os.getenv("CLI_ONPREM_LONG_TIMEOUT", "1800"))  # 30분


def run_command(
    cmd: List[str],
    check: bool = True,
    capture_output: bool = False,
    text: bool = True,
    timeout: Optional[int] = DEFAULT_TIMEOUT,
    **kwargs: Any,
) -> subprocess.CompletedProcess[str]:
    """셸 명령을 실행합니다.

    타임아웃과 로깅이 기본적으로 적용됩니다.

    Args:
        cmd: 실행할 명령과 인자 리스트
        check: 실패 시 예외 발생 여부 (기본값: True)
        capture_output: 출력 캡처 여부 (기본값: False)
        text: 텍스트 모드 사용 여부 (기본값: True)
        timeout: 타임아웃(초). None이면 무제한. 기본값: 300초 (5분)
        **kwargs: subprocess.run()에 전달할 추가 인자

    Returns:
        subprocess.CompletedProcess 객체

    Raises:
        CommandError: 타임아웃 또는 명령 실행 실패 시 (check=True인 경우)
        subprocess.CalledProcessError: 명령 실행 실패 시 (check=True인 경우)

    Examples:
        >>> # 빠른 명령 (30초 타임아웃)
        >>> result = run_command(["docker", "info"], timeout=30)
        >>>
        >>> # 긴 명령 (타임아웃 없음)
        >>> result = run_command(["tar", "-czf", "large.tar.gz", "data/"], timeout=None)
        >>>
        >>> # 환경변수로 타임아웃 설정
        >>> # CLI_ONPREM_TIMEOUT=600 cli-onprem docker-tar save ...
    """
    # 명령어 로깅 (verbose 모드일 때만 상세하게)
    cmd_str = " ".join(cmd)
    logger.debug(f"실행 명령: {cmd_str}")
    if timeout:
        logger.debug(f"타임아웃: {timeout}초")

    try:
        result = subprocess.run(
            cmd,
            check=check,
            capture_output=capture_output,
            text=text,
            timeout=timeout,
            **kwargs
        )

        # 성공 로그
        logger.debug(f"명령 완료: {cmd[0]} (exit code: {result.returncode})")
        return result

    except subprocess.TimeoutExpired as e:
        # 타임아웃을 사용자 친화적인 에러로 변환
        error_msg = (
            f"명령 실행 시간 초과 ({timeout}초)\n\n"
            f"실행 명령: {cmd_str}\n\n"
            f"해결 방법:\n"
            f"  1. 더 긴 시간이 필요하면 환경변수를 설정하세요:\n"
            f"     CLI_ONPREM_TIMEOUT={timeout * 2} cli-onprem ...\n"
            f"  2. 또는 처리할 데이터 크기를 줄이세요"
        )

        logger.error(f"타임아웃 발생: {cmd_str}")

        raise CommandError(
            error_msg,
            command=cmd,
        ) from e

    except subprocess.CalledProcessError as e:
        # CalledProcessError는 그대로 전파 (서비스 레벨에서 처리)
        logger.error(f"명령 실패: {cmd_str} (exit code: {e.returncode})")
        raise
```

## API 설계

### 함수 시그니처

```python
def run_command(
    cmd: List[str],
    check: bool = True,
    capture_output: bool = False,
    text: bool = True,
    timeout: Optional[int] = DEFAULT_TIMEOUT,  # 핵심 변경점
    **kwargs: Any,
) -> subprocess.CompletedProcess[str]:
```

### 타임아웃 정책

| 작업 유형 | 권장 타임아웃 | 이유 |
|----------|--------------|------|
| 빠른 확인 (`docker info`, `helm version`) | 30초 | 즉시 응답해야 함 |
| 이미지 pull/push | 1800초 (30분) | 큰 이미지 고려 |
| tar 압축/해제 | `None` 또는 3600초 | 파일 크기에 따라 |
| Helm template | 300초 (5분) | 복잡한 차트 고려 |
| S3 sync | 1800초 (30분) | 네트워크 속도에 따라 |

### 환경변수

사용자가 타임아웃을 조정할 수 있도록:

```bash
# 기본 타임아웃 변경
export CLI_ONPREM_TIMEOUT=600  # 10분

# 긴 작업 타임아웃 변경
export CLI_ONPREM_LONG_TIMEOUT=3600  # 1시간

# 사용
cli-onprem docker-tar save large-image:latest
```

### 로깅 레벨

- `DEBUG`: 모든 명령어와 타임아웃 정보
- `INFO`: (사용 안 함)
- `WARNING`: 재시도 시도 시
- `ERROR`: 타임아웃 또는 실패 시

## 마이그레이션 가이드

### 패턴 1: 직접 subprocess 호출 → run_command()

**Before**:
```python
# services/docker.py
result = subprocess.run(
    ["docker", "inspect", reference],
    capture_output=True,
    text=True,
)
```

**After**:
```python
# services/docker.py
from cli_onprem.utils.shell import run_command

result = run_command(
    ["docker", "inspect", reference],
    capture_output=True,
    timeout=30,  # 빠른 확인
)
```

### 패턴 2: 타임아웃 없는 긴 작업

**Before**:
```python
# services/docker.py
subprocess.run(
    ["docker", "pull", "--platform", arch, reference],
    check=True,
    capture_output=True,
    text=True,
)
```

**After**:
```python
# services/docker.py
from cli_onprem.utils.shell import run_command, LONG_TIMEOUT

run_command(
    ["docker", "pull", "--platform", arch, reference],
    capture_output=True,
    timeout=LONG_TIMEOUT,  # 30분
)
```

### 패턴 3: 타임아웃이 필요 없는 경우

**Before**:
```python
# services/archive.py
subprocess.run(
    ["tar", "-xzf", "huge-file.tar.gz"],
    check=True,
)
```

**After**:
```python
# services/archive.py
from cli_onprem.utils.shell import run_command

run_command(
    ["tar", "-xzf", "huge-file.tar.gz"],
    timeout=None,  # 무제한
)
```

### 패턴 4: 기존 run_command() 호출

**Before**:
```python
# services/helm.py
from cli_onprem.utils import shell

result = shell.run_command(
    cmd,
    capture_output=True,
)
```

**After**:
```python
# services/helm.py
from cli_onprem.utils.shell import run_command

result = run_command(
    cmd,
    capture_output=True,
    timeout=600,  # 명시적으로 타임아웃 지정
)
```

## 사용 예제

### 예제 1: Docker Daemon 확인

```python
def check_docker_daemon() -> None:
    """Docker daemon 상태 확인 (빠른 확인)"""
    try:
        run_command(
            ["docker", "info"],
            capture_output=True,
            timeout=10,  # 10초면 충분
        )
    except subprocess.CalledProcessError as e:
        raise DependencyError(f"Docker daemon 연결 실패: {e.stderr}")
    except CommandError as e:
        # 타임아웃
        raise DependencyError(
            "Docker daemon이 응답하지 않습니다. "
            "Docker Desktop을 시작하세요."
        )
```

### 예제 2: 큰 이미지 다운로드

```python
def pull_image(reference: str, arch: str) -> None:
    """큰 이미지 다운로드 (긴 타임아웃)"""
    from cli_onprem.utils.shell import run_command, LONG_TIMEOUT

    try:
        run_command(
            ["docker", "pull", "--platform", arch, reference],
            capture_output=True,
            timeout=LONG_TIMEOUT,  # 30분
        )
    except subprocess.CalledProcessError as e:
        raise CommandError(f"이미지 다운로드 실패: {e.stderr}")
```

### 예제 3: 사용자 정의 타임아웃

```python
def custom_operation(data_size_gb: int) -> None:
    """데이터 크기에 따라 타임아웃 조정"""
    # 1GB당 5분 할당
    timeout = data_size_gb * 300

    run_command(
        ["process-data", f"--size={data_size_gb}"],
        timeout=timeout,
    )
```

### 예제 4: 타임아웃 없음 (사용자 제어)

```python
def interactive_command() -> None:
    """사용자 입력이 필요한 명령 (타임아웃 없음)"""
    run_command(
        ["helm", "install", "--interactive"],
        timeout=None,  # 사용자가 입력할 때까지 대기
    )
```

## 에러 처리

### 타임아웃 에러

```python
try:
    run_command(["slow-command"], timeout=10)
except CommandError as e:
    # e.message: "명령 실행 시간 초과 (10초)..."
    # e.command: ["slow-command"]
    console.print(f"[red]{e}[/red]")
```

### 명령 실패 에러

```python
try:
    run_command(["docker", "pull", "nonexistent:image"])
except subprocess.CalledProcessError as e:
    # 서비스 레벨에서 처리
    stderr = e.stderr
    # ... 에러 파싱 ...
```

## 테스트

### 단위 테스트

```python
# tests/test_shell.py
import pytest
from cli_onprem.utils.shell import run_command
from cli_onprem.core.errors import CommandError


def test_run_command_success():
    """정상 실행"""
    result = run_command(["echo", "test"], capture_output=True)
    assert result.returncode == 0
    assert "test" in result.stdout


def test_run_command_timeout():
    """타임아웃 발생"""
    with pytest.raises(CommandError, match="시간 초과"):
        run_command(["sleep", "10"], timeout=1)


def test_run_command_no_timeout():
    """타임아웃 없음"""
    result = run_command(["sleep", "1"], timeout=None)
    assert result.returncode == 0


def test_run_command_custom_timeout():
    """사용자 정의 타임아웃"""
    with pytest.raises(CommandError):
        run_command(["sleep", "5"], timeout=2)
```

### 통합 테스트

```python
# tests/test_docker_integration.py
def test_docker_pull_with_timeout(monkeypatch):
    """실제 Docker pull (타임아웃 설정)"""
    # 환경변수 설정
    monkeypatch.setenv("CLI_ONPREM_TIMEOUT", "1800")

    # 작은 이미지로 테스트
    result = run_command(
        ["docker", "pull", "alpine:latest"],
        capture_output=True,
    )

    assert result.returncode == 0
```

## 성능 고려사항

### 오버헤드

최소주의 접근법의 오버헤드:
- 로깅: 무시할 수 있는 수준 (~1ms)
- 타임아웃 설정: 무시할 수 있는 수준
- 예외 변환: 실패 시에만 발생

### 메모리

- subprocess는 기본 Python subprocess 그대로 사용
- 추가 메모리 사용 없음

## 향후 확장 (필요한 경우)

현재는 최소주의 접근이지만, 필요하다면 다음을 추가할 수 있습니다:

### Phase 2: 진행률 표시

```python
def run_command_with_progress(
    cmd: List[str],
    progress: Progress,
    task_id: TaskID,
    **kwargs
) -> subprocess.CompletedProcess[str]:
    """진행률 표시와 함께 실행"""
    # stdout/stderr를 스트리밍하며 progress 업데이트
    pass
```

### Phase 3: 자동 재시도

```python
def run_command_with_retry(
    cmd: List[str],
    max_retries: int = 3,
    retry_on: Optional[List[str]] = None,
    **kwargs
) -> subprocess.CompletedProcess[str]:
    """재시도 로직이 있는 실행"""
    # 특정 오류 패턴에 대해 자동 재시도
    pass
```

하지만 **현재는 필요하지 않습니다** (YAGNI).

## 결론

최소주의 접근법의 장점:
- ✅ 즉시 적용 가능 (복잡한 리팩토링 불필요)
- ✅ 기존 코드와 호환
- ✅ 테스트 용이
- ✅ 유지보수 간단
- ✅ 오버엔지니어링 방지

핵심 개선:
- ✅ 타임아웃 → 무한 대기 방지
- ✅ 로깅 → 디버깅 용이
- ✅ 에러 변환 → 사용자 친화적

---

**작성일**: 2025-01-30
**버전**: 1.0
**상태**: 설계 완료, 구현 대기
