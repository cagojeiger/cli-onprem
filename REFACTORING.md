# CLI-ONPREM 리팩토링 가이드

> 이 문서는 Claude Code, API Design Reviewer, Gemini Agent의 종합 분석을 바탕으로 작성되었습니다.

## 📋 목차

- [분석 요약](#분석-요약)
- [1단계: 보안 + 안정성](#1단계-보안--안정성)
- [작업 우선순위](#작업-우선순위)
- [파일별 수정 사항](#파일별-수정-사항)
- [테스트 전략](#테스트-전략)
- [참고 문서](#참고-문서)

## 분석 요약

### 핵심 문제점

**사용자 피드백**: "래핑해서 사용하는 거라서 관련 툴들의 안정성에 따라서 사용성 여부가 달라지는 것 같아"

이 도구는 Docker, Helm, AWS CLI, tar 등 외부 도구를 감싸는(wrapping) 구조입니다. 현재 아키텍처의 주요 문제:

1. **외부 도구 장애가 사용자에게 직접 전달됨** - 에러 메시지 불친절, 컨텍스트 부족
2. **타임아웃 없음** - 작업이 무한정 대기할 수 있음
3. **일관성 없는 에러 처리** - 같은 상황이 다르게 처리됨
4. **재시도 로직 부족** - 일시적 네트워크 오류에 취약
5. **보안 취약점** - Shell command injection 가능

### 3개 에이전트 분석 결과

#### 1. Explore Agent - 코드베이스 분석
- **보안**: `archive.py` 2곳에서 shell injection 취약점
- **안정성**: 타임아웃 없음, 재시도는 pull_image()에만 존재
- **테스트**: 타임아웃/보안 테스트 누락

#### 2. Gemini Agent - 아키텍처 전략
- **핵심 조언**: SDK/API 우선 사용, subprocess는 최후의 수단
- **추천**: 어댑터 패턴, 사전 검증, 견고한 에러 변환
- **경고**: 복잡한 추상화보다 간단하고 확실한 해결책 우선

#### 3. API Design Reviewer - 인터페이스 분석
- **장점**: 계층 구조 명확, 타입 힌트 우수
- **단점**: subprocess 호출 패턴 불일치, 에러 컨텍스트 부족
- **제안**: ExternalCommand 클래스로 통합

### 아키텍처 강점
- ✅ 명확한 계층 구조 (Commands → Services → Utils)
- ✅ 타입 힌트 전반적으로 사용
- ✅ 에러 계층 구조 (CLIError → CommandError/DependencyError)

### 아키텍처 약점
- ❌ subprocess 호출 패턴 불일치
- ❌ 에러 처리 일관성 부족
- ❌ 재시도 로직 중복/부족
- ❌ 외부 도구 Health Check 없음

## 1단계: 보안 + 안정성

> **선택된 접근법**: 최소주의 (타임아웃 + 로깅 중심)
> **AWS 전략**: 현재 유지 (boto3/CLI 혼용)

### 작업 범위

1. **보안 취약점 수정** ⚠️ 최우선
2. **타임아웃 추가** ⚠️ 최우선
3. **에러 핸들링 개선** 🔴 높음
4. **Health Check 추가** 🟡 중간
5. **재시도 로직 개선** 🟡 중간

## 작업 우선순위

### ⚠️ 최우선 (Critical)

#### 1. Shell Command Injection 수정

**위험도**: 🔴 Critical
**영향**: 보안 취약점, 악의적 입력 시 임의 명령 실행 가능

**파일**: `src/cli_onprem/services/archive.py`

**문제 1**: Line 122-126
```python
# ❌ BEFORE (취약)
def calculate_sha256_manifest(directory: Path, pattern: str = "*.tar.gz.*") -> str:
    cmd = f"cd {directory} && sha256sum {pattern}"
    result = subprocess.run(
        ["sh", "-c", cmd],  # 🚨 Shell injection 가능
        capture_output=True,
        text=True,
    )
```

**해결책**:
```python
# ✅ AFTER (안전)
def calculate_sha256_manifest(directory: Path, pattern: str = "*.tar.gz.*") -> str:
    import glob
    import hashlib

    files = sorted(glob.glob(str(directory / pattern)))
    if not files:
        raise CommandError(f"패턴과 일치하는 파일이 없습니다: {pattern}")

    checksums = []
    for file_path in files:
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        checksums.append(f"{sha256.hexdigest()}  {Path(file_path).name}")

    return "\n".join(checksums)
```

**문제 2**: Line 192-195
```python
# ❌ BEFORE (취약)
def merge_files(directory: Path, pattern: str, output_file: Path) -> None:
    cmd = f"cat {directory}/{pattern} > {output_file}"
    subprocess.run(["sh", "-c", cmd], check=True)  # 🚨 Shell injection
```

**해결책**:
```python
# ✅ AFTER (안전)
def merge_files(directory: Path, pattern: str, output_file: Path) -> None:
    import glob

    files = sorted(glob.glob(str(directory / pattern)))
    if not files:
        raise CommandError(f"병합할 파일이 없습니다: {pattern}")

    with open(output_file, 'wb') as outfile:
        for file_path in files:
            with open(file_path, 'rb') as infile:
                outfile.write(infile.read())
```

**테스트 추가**:
```python
# tests/test_archive_security.py
def test_shell_injection_prevention():
    """Shell injection 시도가 실패하는지 확인"""
    malicious_pattern = "*.tar; rm -rf /"
    with pytest.raises(CommandError):
        calculate_sha256_manifest(Path("/tmp"), malicious_pattern)
```

---

#### 2. 타임아웃 기본값 추가

**위험도**: 🔴 Critical
**영향**: 작업이 무한정 대기하여 시스템 리소스 고갈

**파일**: `src/cli_onprem/utils/shell.py`

**문제**: Line 7-31
```python
# ❌ BEFORE (타임아웃 없음)
def run_command(
    cmd: List[str],
    check: bool = True,
    capture_output: bool = False,
    text: bool = True,
    **kwargs: Any,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        check=check,
        capture_output=capture_output,
        text=text,
        **kwargs
    )
```

**해결책**:
```python
# ✅ AFTER (기본 타임아웃 추가)
import os
from typing import Optional

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

    Args:
        cmd: 실행할 명령과 인자 리스트
        check: 실패 시 예외 발생 여부
        capture_output: 출력 캡처 여부
        text: 텍스트 모드 사용 여부
        timeout: 타임아웃(초). None이면 무제한. 기본값은 환경변수 또는 300초.
        **kwargs: subprocess.run()에 전달할 추가 인자

    Returns:
        subprocess.CompletedProcess 객체

    Raises:
        CommandError: 타임아웃 또는 명령 실행 실패 시
    """
    try:
        return subprocess.run(
            cmd,
            check=check,
            capture_output=capture_output,
            text=text,
            timeout=timeout,
            **kwargs
        )
    except subprocess.TimeoutExpired as e:
        raise CommandError(
            f"명령 실행 시간 초과 ({timeout}초): {' '.join(cmd)}\n"
            f"더 긴 시간이 필요하면 CLI_ONPREM_TIMEOUT 환경변수를 설정하세요.",
            command=cmd,
        ) from e
```

**주요 subprocess 호출 업데이트**:

1. `services/docker.py` 모든 호출:
   - `check_image_exists()` (line 366): `timeout=30` (빠른 확인)
   - `pull_image()` (line 391): `timeout=1800` (큰 이미지 고려)
   - `save_image()` (line 428): `timeout=1800` (큰 이미지 고려)

2. `services/helm.py` 모든 호출:
   - `update_dependencies()` (line 94): `timeout=600` (차트 다운로드)
   - `render_template()` (line 143): `timeout=300` (템플릿 렌더링)

3. `services/archive.py` 모든 호출:
   - tar 작업: `timeout=LONG_TIMEOUT` (큰 파일)
   - sha256sum: `timeout=600` (파일 크기에 따라)

---

### 🔴 높은 우선순위

#### 3. 에러 컨텍스트 추가

**파일**: `src/cli_onprem/core/errors.py`

**문제**: Line 11-16
```python
# ❌ BEFORE (컨텍스트 부족)
class CommandError(CLIError):
    """명령 실행 중 발생하는 에러."""
    pass
```

**해결책**:
```python
# ✅ AFTER (상세한 컨텍스트)
from typing import Optional, List

class CommandError(CLIError):
    """명령 실행 중 발생하는 에러.

    외부 도구(docker, helm, aws, tar 등) 실행 실패 시 발생합니다.
    명령어와 stderr를 포함하여 디버깅을 돕습니다.
    """

    def __init__(
        self,
        message: str,
        command: Optional[List[str]] = None,
        stderr: Optional[str] = None,
        exit_code: int = 1,
    ):
        super().__init__(message, exit_code)
        self.command = command
        self.stderr = stderr

    def __str__(self) -> str:
        msg = super().__str__()

        if self.command:
            msg += f"\n\n실행 명령:\n  {' '.join(self.command)}"

        if self.stderr:
            # stderr가 너무 길면 마지막 20줄만
            stderr_lines = self.stderr.strip().split('\n')
            if len(stderr_lines) > 20:
                stderr_display = '\n'.join(stderr_lines[-20:])
                msg += f"\n\n상세 오류 (마지막 20줄):\n{stderr_display}"
            else:
                msg += f"\n\n상세 오류:\n{self.stderr}"

        return msg


class TransientError(CommandError):
    """일시적인 오류로 재시도 가능.

    네트워크 타임아웃, 레이트 리밋, 일시적인 서비스 장애 등.
    자동화 스크립트에서 이 오류를 잡아 재시도할 수 있습니다.
    """
    pass


class PermanentError(CommandError):
    """영구적인 오류로 재시도 불필요.

    잘못된 자격증명, 존재하지 않는 리소스, 권한 부족 등.
    재시도해도 성공할 수 없는 오류입니다.
    """
    pass
```

---

#### 4. Docker 에러 메시지 파싱

**파일**: `src/cli_onprem/services/docker.py`

**추가**: 새로운 함수
```python
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
    if any(word in stderr_lower for word in ["timeout", "network", "connection"]):
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
```

**적용**: `pull_image()` 수정 (line 414)
```python
# ❌ BEFORE
raise CommandError(f"이미지 다운로드 실패: {last_error}")

# ✅ AFTER
friendly_message = _parse_docker_error(last_error, reference)
raise CommandError(
    friendly_message,
    command=cmd,
    stderr=last_error
)
```

---

### 🟡 중간 우선순위

#### 5. Health Check 추가

**파일**: `src/cli_onprem/services/docker.py`

**추가**: 새로운 함수
```python
def check_docker_daemon() -> None:
    """Docker daemon이 실행 중이고 응답하는지 확인.

    명령 실행 전에 호출하여 조기 실패(fail-fast)를 구현합니다.

    Raises:
        DependencyError: Docker daemon 연결 실패 시
    """
    try:
        subprocess.run(
            ["docker", "info"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,  # 빠른 확인
        )
    except subprocess.TimeoutExpired:
        raise DependencyError(
            "Docker daemon이 응답하지 않습니다 (10초 타임아웃).\n\n"
            "해결 방법:\n"
            "  1. Docker Desktop을 시작하세요\n"
            "  2. 시스템 서비스 상태 확인: sudo systemctl status docker\n"
            "  3. Docker Desktop 재시작을 시도하세요"
        )
    except subprocess.CalledProcessError as e:
        stderr = e.stderr or ""
        if "permission denied" in stderr.lower():
            raise DependencyError(
                "Docker daemon 접근 권한이 없습니다.\n\n"
                "해결 방법:\n"
                "  1. 사용자를 docker 그룹에 추가: sudo usermod -aG docker $USER\n"
                "  2. 로그아웃 후 다시 로그인\n"
                "  3. 또는 sudo로 실행하세요"
            )
        else:
            raise DependencyError(
                f"Docker daemon에 연결할 수 없습니다.\n\n"
                f"상세 오류:\n{stderr}"
            )
    except FileNotFoundError:
        raise DependencyError(
            "Docker가 설치되어 있지 않습니다.\n\n"
            "해결 방법:\n"
            "  1. Docker Desktop 설치: https://www.docker.com/get-started\n"
            "  2. 또는 Docker Engine 설치 (Linux)"
        )
```

**적용**: `commands/docker_tar.py` 수정
```python
@app.command()
def save(...):
    """Docker 이미지를 tar 파일로 저장합니다."""
    init_logging(quiet=quiet, verbose=verbose)

    try:
        check_docker_installed()  # 기존: 바이너리만 확인
        check_docker_daemon()     # 추가: daemon 응답 확인

        # ... 나머지 로직
```

---

#### 6. 재시도 로직 개선

**파일**: `src/cli_onprem/services/docker.py`

**문제**: `pull_image()` (line 396-413)는 "timeout"만 재시도

**해결책**:
```python
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


def pull_image(
    reference: str,
    arch: str = "linux/amd64",
    max_retries: int = 3,
) -> None:
    """이미지를 다운로드합니다 (재시도 로직 포함).

    네트워크 관련 일시적 오류는 자동으로 재시도합니다.
    """
    cmd = ["docker", "pull", "--platform", arch, reference]

    last_error = ""
    for attempt in range(1, max_retries + 1):
        try:
            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                timeout=1800,  # 30분
            )
            return  # 성공

        except subprocess.CalledProcessError as e:
            last_error = e.stderr or ""

            # 재시도 가능한 에러인지 확인
            if attempt < max_retries and _is_retryable_error(last_error):
                wait_time = 2 ** attempt  # Exponential backoff: 2, 4, 8초
                logging.warning(
                    f"이미지 다운로드 실패 (시도 {attempt}/{max_retries}). "
                    f"{wait_time}초 후 재시도... 오류: {last_error[:100]}"
                )
                time.sleep(wait_time)
                continue

            # 재시도 불가능하거나 마지막 시도면 예외 발생
            friendly_message = _parse_docker_error(last_error, reference)

            if _is_retryable_error(last_error):
                raise TransientError(
                    friendly_message,
                    command=cmd,
                    stderr=last_error
                )
            else:
                raise PermanentError(
                    friendly_message,
                    command=cmd,
                    stderr=last_error
                )
```

---

## 파일별 수정 사항

### 수정이 필요한 파일 목록

| 파일 | 우선순위 | 변경 유형 | 설명 |
|------|---------|-----------|------|
| `src/cli_onprem/services/archive.py` | ⚠️ Critical | 보안 수정 | Shell injection 제거 (2곳) |
| `src/cli_onprem/utils/shell.py` | ⚠️ Critical | 타임아웃 추가 | 기본 타임아웃 300초 |
| `src/cli_onprem/core/errors.py` | 🔴 High | 에러 개선 | CommandError 컨텍스트 추가 |
| `src/cli_onprem/services/docker.py` | 🔴 High | 에러+재시도 | 에러 파싱, 재시도 개선 |
| `src/cli_onprem/commands/docker_tar.py` | 🟡 Medium | Health check | check_docker_daemon() 호출 |
| `tests/test_archive_security.py` | 🔴 High | 보안 테스트 | Shell injection 테스트 추가 |
| `tests/test_timeout.py` | 🟡 Medium | 타임아웃 테스트 | 타임아웃 동작 검증 |

### 상세 수정 위치

#### `src/cli_onprem/services/archive.py`
```
Line 105-140: calculate_sha256_manifest() 전체 재작성
  - subprocess + shell → Python hashlib
  - glob으로 파일 패턴 매칭

Line 170-210: merge_files() 전체 재작성
  - subprocess + shell → Python file I/O
  - 바이너리 모드로 파일 병합
```

#### `src/cli_onprem/utils/shell.py`
```
Line 1-5: 임포트 추가
  - import os
  - from typing import Optional

Line 7-31: run_command() 시그니처 변경
  - timeout 파라미터 추가 (기본값: 300)
  - TimeoutExpired 예외 처리
  - 환경변수 지원 (CLI_ONPREM_TIMEOUT)
```

#### `src/cli_onprem/core/errors.py`
```
Line 11-28: CommandError 클래스 확장
  - command, stderr 필드 추가
  - __str__() 메서드 오버라이드

Line 30-40: TransientError 클래스 추가 (새로운)
Line 42-52: PermanentError 클래스 추가 (새로운)
```

#### `src/cli_onprem/services/docker.py`
```
Line 60-110: _parse_docker_error() 함수 추가 (새로운)
Line 112-140: _is_retryable_error() 함수 추가 (새로운)
Line 142-175: check_docker_daemon() 함수 추가 (새로운)

Line 379-450: pull_image() 함수 재작성
  - 재시도 로직 개선
  - 에러 파싱 적용
  - TransientError/PermanentError 구분

Line 366-376: check_image_exists() 타임아웃 추가
  - timeout=30

Line 428-434: save_image() 타임아웃 추가
  - timeout=1800
```

#### `src/cli_onprem/commands/docker_tar.py`
```
Line 38-43: save() 명령 시작 부분
  - check_docker_daemon() 호출 추가
```

---

## 테스트 전략

### 새로운 테스트 파일

#### `tests/test_archive_security.py`
```python
"""Archive 보안 테스트"""
import pytest
from pathlib import Path
from cli_onprem.services.archive import calculate_sha256_manifest, merge_files
from cli_onprem.core.errors import CommandError


def test_sha256_no_shell_injection(tmp_path):
    """Shell injection 시도가 실패하는지 확인"""
    malicious_pattern = "*.tar; rm -rf /"

    with pytest.raises(CommandError, match="패턴과 일치하는 파일이 없습니다"):
        calculate_sha256_manifest(tmp_path, malicious_pattern)


def test_merge_no_shell_injection(tmp_path):
    """병합 시 shell injection 시도가 실패하는지 확인"""
    malicious_pattern = "*.part; cat /etc/passwd"
    output = tmp_path / "output.tar"

    with pytest.raises(CommandError, match="병합할 파일이 없습니다"):
        merge_files(tmp_path, malicious_pattern, output)


def test_sha256_calculates_correctly(tmp_path):
    """SHA256 해시가 올바르게 계산되는지 확인"""
    # 테스트 파일 생성
    file1 = tmp_path / "test.tar.gz.001"
    file1.write_text("Hello World")

    result = calculate_sha256_manifest(tmp_path, "*.tar.gz.*")

    assert "test.tar.gz.001" in result
    assert len(result.split()[0]) == 64  # SHA256 길이
```

#### `tests/test_timeout.py`
```python
"""타임아웃 테스트"""
import pytest
import subprocess
from cli_onprem.utils.shell import run_command
from cli_onprem.core.errors import CommandError


def test_timeout_expires():
    """타임아웃이 제대로 동작하는지 확인"""
    with pytest.raises(CommandError, match="명령 실행 시간 초과"):
        # sleep 명령으로 타임아웃 테스트
        run_command(["sleep", "10"], timeout=1)


def test_timeout_not_expired():
    """타임아웃 내에 완료되면 정상 동작"""
    result = run_command(["echo", "test"], timeout=10)
    assert result.returncode == 0


def test_default_timeout_applied():
    """기본 타임아웃이 적용되는지 확인"""
    # 기본값(300초)보다 긴 작업은 실패해야 함
    with pytest.raises(CommandError):
        run_command(["sleep", "400"])  # timeout 파라미터 없음
```

#### `tests/test_docker_error_parsing.py`
```python
"""Docker 에러 파싱 테스트"""
import pytest
from cli_onprem.services.docker import _parse_docker_error


def test_parse_auth_error():
    """인증 오류 파싱"""
    stderr = "Error: denied: requested access to the resource is denied"
    result = _parse_docker_error(stderr, "private/image:latest")

    assert "접근 권한이 없습니다" in result
    assert "docker login" in result


def test_parse_not_found_error():
    """이미지 없음 오류 파싱"""
    stderr = "Error: manifest for nginx:nonexistent not found"
    result = _parse_docker_error(stderr, "nginx:nonexistent")

    assert "찾을 수 없습니다" in result
    assert "태그가 존재하는지" in result


def test_parse_network_error():
    """네트워크 오류 파싱"""
    stderr = "Error: net/http: request canceled while waiting for connection"
    result = _parse_docker_error(stderr, "nginx:latest")

    assert "네트워크 오류" in result
    assert "인터넷 연결을 확인" in result
```

### 기존 테스트 수정

**`tests/test_docker_tar.py`**
- `test_pull_image_*` 테스트들: `command`, `stderr` 파라미터 추가
- 타임아웃 관련 모킹 추가

**`tests/test_helm_local.py`**
- 타임아웃 관련 모킹 추가

---

## 체크리스트

작업 완료 시 아래 항목을 확인하세요:

### 코드 변경
- [ ] `archive.py` shell injection 2곳 수정
- [ ] `shell.py` 타임아웃 기본값 추가
- [ ] `errors.py` CommandError 컨텍스트 추가
- [ ] `errors.py` TransientError/PermanentError 추가
- [ ] `docker.py` 에러 파싱 함수 추가
- [ ] `docker.py` 재시도 로직 개선
- [ ] `docker.py` health check 함수 추가
- [ ] `docker_tar.py` health check 호출 추가

### 테스트
- [ ] `test_archive_security.py` 작성
- [ ] `test_timeout.py` 작성
- [ ] `test_docker_error_parsing.py` 작성
- [ ] 기존 테스트 모두 통과
- [ ] pytest -q 성공

### 문서
- [ ] REFACTORING.md (이 문서) 작성 완료
- [ ] docs/architecture/SUBPROCESS_WRAPPER.md 작성
- [ ] docs/architecture/ERROR_HANDLING.md 작성
- [ ] CHANGELOG.md 업데이트

### 린팅
- [ ] SKIP=uv-lock uv run pre-commit run --all-files 통과
- [ ] mypy src --strict --no-warn-unused-ignores 통과

---

## 참고 문서

### 내부 문서
- [Subprocess 래퍼 설계](docs/architecture/SUBPROCESS_WRAPPER.md) - 최소주의 접근법 상세 설계
- [에러 핸들링 가이드](docs/architecture/ERROR_HANDLING.md) - 에러 처리 패턴
- [CLAUDE.md](CLAUDE.md) - 프로젝트 전반 개발 가이드

### 외부 참고
- [OWASP Command Injection](https://owasp.org/www-community/attacks/Command_Injection)
- [Python subprocess Security](https://docs.python.org/3/library/subprocess.html#security-considerations)
- [Effective Error Handling in Python](https://realpython.com/python-exceptions/)

### 분석 결과 원본
이 문서는 다음 에이전트들의 분석을 종합하여 작성되었습니다:
- Explore Agent: 코드베이스 전반 분석 (149개 함수, 23개 파일)
- Gemini Agent: 아키텍처 전략 및 오캄의 면도날 관점 조언
- API Design Reviewer: CLI 인터페이스 및 서비스 API 리뷰

---

## 다음 단계 (2단계, 3단계)

현재는 1단계(보안+안정성)만 다룹니다. 추후 단계:

### 2단계: 아키텍처 개선 (향후)
- ExternalCommand 클래스 도입
- Circuit Breaker 패턴
- 의존성 주입 (테스트 용이성)

### 3단계: 코드 품질 (향후)
- 긴 함수 분리 (`normalize_image_name`, `sync_to_s3`, `presign`)
- AWS S3 통합 일관성 (boto3 vs CLI 선택)
- 진행률 표시 개선

---

**작성일**: 2025-01-30
**버전**: 1.0 (1단계 리팩토링)
**작성자**: Claude Code + API Design Reviewer + Gemini Agent
