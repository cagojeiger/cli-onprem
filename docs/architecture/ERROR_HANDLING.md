# 에러 핸들링 가이드

> CLI 도구가 외부 도구를 래핑할 때 가장 중요한 것은 **실패를 예측하고 명확하게 처리**하는 것입니다.

## 목차

- [에러 핸들링 원칙](#에러-핸들링-원칙)
- [에러 계층 구조](#에러-계층-구조)
- [에러 파싱 패턴](#에러-파싱-패턴)
- [사용자 친화적 메시지](#사용자-친화적-메시지)
- [재시도 전략](#재시도-전략)
- [테스트 전략](#테스트-전략)

## 에러 핸들링 원칙

### 1. Fail Fast (빠른 실패)

❌ **나쁜 예**: 작업 시작 후 실패 발견
```python
def save_images(images: List[str]):
    for img in images:
        pull_image(img)  # 15번째 이미지에서 Docker daemon 다운 발견
```

✅ **좋은 예**: 작업 전 사전 검증
```python
def save_images(images: List[str]):
    check_docker_daemon()  # 즉시 실패 발견
    check_disk_space(required_gb=50)

    for img in images:
        pull_image(img)
```

### 2. 명확한 에러 메시지

❌ **나쁜 예**: 기술적 에러 그대로 노출
```
Error: Command '['docker', 'pull', 'nginx']' returned non-zero exit status 1.
```

✅ **좋은 예**: 컨텍스트와 해결 방법 제공
```
이미지 다운로드 실패: nginx:latest

원인: Docker daemon에 연결할 수 없습니다.

해결 방법:
  1. Docker Desktop을 시작하세요
  2. 상태 확인: docker info
  3. 재시작이 필요하면: sudo systemctl restart docker

실행 명령: docker pull --platform linux/amd64 nginx:latest
```

### 3. 에러 분류

모든 에러를 동일하게 취급하지 마세요:

| 에러 유형 | 재시도 | 사용자 조치 | 예시 |
|----------|--------|------------|------|
| **Transient** (일시적) | ✅ 자동 재시도 | 대기 | 네트워크 타임아웃, 레이트 리밋 |
| **Permanent** (영구적) | ❌ 재시도 무의미 | 수정 필요 | 잘못된 자격증명, 리소스 없음 |
| **Dependency** (의존성) | ❌ 재시도 무의미 | 설치/설정 필요 | Docker 미설치, AWS CLI 없음 |

## 에러 계층 구조

### 현재 구조

```python
# src/cli_onprem/core/errors.py

class CLIError(Exception):
    """모든 CLI 에러의 베이스 클래스"""

class CommandError(CLIError):
    """명령 실행 실패"""

class DependencyError(CLIError):
    """외부 도구 의존성 문제"""
```

### 개선된 구조

```python
# src/cli_onprem/core/errors.py

from typing import Optional, List


class CLIError(Exception):
    """모든 CLI 에러의 베이스 클래스.

    Attributes:
        message: 사용자에게 표시할 에러 메시지
        exit_code: 프로그램 종료 코드 (기본값: 1)
    """

    def __init__(self, message: str, exit_code: int = 1):
        super().__init__(message)
        self.message = message
        self.exit_code = exit_code

    def __str__(self) -> str:
        return self.message


class CommandError(CLIError):
    """외부 명령 실행 실패.

    Docker, Helm, AWS CLI 등 외부 도구 호출이 실패했을 때 발생합니다.

    Attributes:
        command: 실행된 명령어 (디버깅용)
        stderr: 명령의 stderr 출력 (디버깅용)
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
        """사용자 친화적인 에러 메시지 생성."""
        msg = self.message

        # 실행된 명령어 추가
        if self.command:
            msg += f"\n\n실행 명령:\n  {' '.join(self.command)}"

        # stderr 추가 (너무 길면 잘라냄)
        if self.stderr:
            stderr_lines = self.stderr.strip().split('\n')
            if len(stderr_lines) > 20:
                msg += f"\n\n상세 오류 (마지막 20줄):\n"
                msg += '\n'.join(stderr_lines[-20:])
            else:
                msg += f"\n\n상세 오류:\n{self.stderr}"

        return msg


class TransientError(CommandError):
    """일시적인 오류 (재시도 가능).

    네트워크 타임아웃, 일시적인 서비스 장애, 레이트 리밋 등
    잠시 후 재시도하면 성공할 수 있는 오류입니다.

    자동화 스크립트에서 이 에러를 잡아 재시도 로직을 구현할 수 있습니다:

    Example:
        >>> for attempt in range(3):
        >>>     try:
        >>>         pull_image("nginx:latest")
        >>>         break
        >>>     except TransientError:
        >>>         if attempt < 2:
        >>>             time.sleep(2 ** attempt)
        >>>         else:
        >>>             raise
    """
    pass


class PermanentError(CommandError):
    """영구적인 오류 (재시도 불필요).

    잘못된 자격증명, 존재하지 않는 리소스, 권한 부족 등
    재시도해도 성공할 수 없는 오류입니다.

    사용자가 문제를 수정하지 않는 한 계속 실패합니다.

    Example:
        >>> try:
        >>>     pull_image("nonexistent:image")
        >>> except PermanentError as e:
        >>>     # 재시도하지 말고 즉시 실패
        >>>     console.print(f"[red]{e}[/red]")
        >>>     raise typer.Exit(1)
    """
    pass


class DependencyError(CLIError):
    """외부 도구 의존성 문제.

    Docker, Helm, AWS CLI 등이 설치되지 않았거나
    실행할 수 없을 때 발생합니다.

    Example:
        >>> try:
        >>>     check_docker_installed()
        >>> except DependencyError as e:
        >>>     console.print(f"[yellow]설치 필요:[/yellow] {e}")
        >>>     raise typer.Exit(2)  # 의존성 오류는 exit code 2
    """
    pass
```

## 에러 파싱 패턴

### Docker 에러 파싱

```python
# src/cli_onprem/services/docker.py

def _parse_docker_error(stderr: str, reference: str) -> tuple[str, type]:
    """Docker CLI 에러를 분석하여 사용자 친화적 메시지와 에러 타입 반환.

    Args:
        stderr: Docker CLI의 stderr 출력
        reference: 작업 대상 이미지 (예: nginx:latest)

    Returns:
        (error_message, error_class) 튜플
        - error_message: 한국어 설명 + 해결 방법
        - error_class: TransientError | PermanentError
    """
    stderr_lower = stderr.lower()

    # === 영구적 오류 (PermanentError) ===

    # 1. 인증/권한 문제
    if any(word in stderr_lower for word in ["denied", "unauthorized", "forbidden"]):
        message = (
            f"이미지 접근 권한이 없습니다: {reference}\n\n"
            f"원인:\n"
            f"  - Private 레지스트리에 로그인하지 않았습니다\n"
            f"  - 또는 해당 이미지에 대한 권한이 없습니다\n\n"
            f"해결 방법:\n"
            f"  1. 레지스트리에 로그인:\n"
            f"     docker login [레지스트리주소]\n"
            f"  2. 이미지 이름과 조직을 확인하세요\n"
            f"  3. 관리자에게 권한을 요청하세요"
        )
        return message, PermanentError

    # 2. 이미지/태그 없음
    if any(word in stderr_lower for word in ["not found", "manifest unknown", "no such"]):
        message = (
            f"이미지를 찾을 수 없습니다: {reference}\n\n"
            f"원인:\n"
            f"  - 이미지 이름 또는 태그가 잘못되었습니다\n"
            f"  - 또는 레지스트리에 해당 이미지가 없습니다\n\n"
            f"해결 방법:\n"
            f"  1. 이미지 이름 확인 (오타 검사)\n"
            f"  2. 태그 확인 (latest, v1.0 등)\n"
            f"  3. Docker Hub에서 검색:\n"
            f"     https://hub.docker.com/search?q={reference.split(':')[0]}"
        )
        return message, PermanentError

    # 3. 디스크 공간 부족
    if any(word in stderr_lower for word in ["no space", "disk full", "insufficient"]):
        message = (
            f"디스크 공간 부족: {reference}\n\n"
            f"원인:\n"
            f"  - 이미지를 저장할 공간이 부족합니다\n\n"
            f"해결 방법:\n"
            f"  1. 디스크 공간 확인: df -h\n"
            f"  2. 사용하지 않는 Docker 리소스 정리:\n"
            f"     docker system prune -a\n"
            f"  3. 오래된 이미지 삭제:\n"
            f"     docker images | grep months"
        )
        return message, PermanentError

    # === 일시적 오류 (TransientError) ===

    # 4. 네트워크 문제
    if any(word in stderr_lower for word in [
        "timeout", "network", "connection",
        "dial tcp", "i/o timeout", "connection refused"
    ]):
        message = (
            f"네트워크 오류: {reference}\n\n"
            f"원인:\n"
            f"  - 네트워크 연결이 불안정합니다\n"
            f"  - 또는 레지스트리가 일시적으로 응답하지 않습니다\n\n"
            f"해결 방법:\n"
            f"  1. 인터넷 연결 확인\n"
            f"  2. VPN 또는 프록시 설정 확인\n"
            f"  3. Docker Hub 상태 확인:\n"
            f"     https://status.docker.com\n"
            f"  4. 잠시 후 다시 시도하세요 (자동 재시도 중...)"
        )
        return message, TransientError

    # 5. Rate Limiting
    if any(word in stderr_lower for word in ["too many requests", "rate limit", "429"]):
        message = (
            f"레이트 리밋: {reference}\n\n"
            f"원인:\n"
            f"  - Docker Hub 다운로드 제한에 걸렸습니다\n"
            f"  - 익명 사용자: 6시간당 100회\n"
            f"  - 로그인 사용자: 6시간당 200회\n\n"
            f"해결 방법:\n"
            f"  1. Docker Hub에 로그인: docker login\n"
            f"  2. 잠시 후 다시 시도하세요 (자동 재시도 중...)\n"
            f"  3. Pro 계정을 고려하세요 (무제한)"
        )
        return message, TransientError

    # 6. 서비스 장애 (5xx 오류)
    if any(word in stderr_lower for word in ["503", "500", "502", "504", "service unavailable"]):
        message = (
            f"서비스 일시 장애: {reference}\n\n"
            f"원인:\n"
            f"  - Docker Hub 또는 레지스트리가 일시적으로 장애입니다\n\n"
            f"해결 방법:\n"
            f"  1. 상태 페이지 확인: https://status.docker.com\n"
            f"  2. 잠시 후 다시 시도하세요 (자동 재시도 중...)"
        )
        return message, TransientError

    # === 기타 오류 (기본값: PermanentError) ===
    message = (
        f"Docker 작업 실패: {reference}\n\n"
        f"상세 오류:\n{stderr}"
    )
    return message, PermanentError


# 사용 예시
def pull_image(reference: str, arch: str, max_retries: int = 3) -> None:
    """이미지 다운로드 (에러 파싱 적용)"""
    cmd = ["docker", "pull", "--platform", arch, reference]

    for attempt in range(1, max_retries + 1):
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=1800)
            return  # 성공

        except subprocess.CalledProcessError as e:
            stderr = e.stderr or ""

            # 에러 파싱
            friendly_msg, error_class = _parse_docker_error(stderr, reference)

            # TransientError이고 재시도 가능하면 재시도
            if error_class == TransientError and attempt < max_retries:
                wait_time = 2 ** attempt
                logging.warning(f"재시도 {attempt}/{max_retries} ({wait_time}초 후)")
                time.sleep(wait_time)
                continue

            # 실패: 적절한 에러 타입으로 raise
            raise error_class(
                friendly_msg,
                command=cmd,
                stderr=stderr
            )
```

### Helm 에러 파싱

```python
# src/cli_onprem/services/helm.py

def _parse_helm_error(stderr: str, chart_path: str) -> tuple[str, type]:
    """Helm CLI 에러 파싱."""
    stderr_lower = stderr.lower()

    # 차트 파일 없음
    if "no such file" in stderr_lower or "not found" in stderr_lower:
        message = (
            f"Helm 차트를 찾을 수 없습니다: {chart_path}\n\n"
            f"해결 방법:\n"
            f"  1. 파일 경로를 확인하세요\n"
            f"  2. 차트가 압축(.tgz)되어 있는지 확인하세요\n"
            f"  3. 현재 디렉토리: {os.getcwd()}"
        )
        return message, PermanentError

    # YAML 구문 오류
    if "yaml" in stderr_lower and ("parse" in stderr_lower or "unmarshal" in stderr_lower):
        message = (
            f"YAML 파일 구문 오류: {chart_path}\n\n"
            f"해결 방법:\n"
            f"  1. values.yaml 파일을 확인하세요\n"
            f"  2. YAML 린터로 검증: yamllint values.yaml\n"
            f"  3. 들여쓰기와 콜론(:) 뒤 공백을 확인하세요"
        )
        return message, PermanentError

    # 네트워크 오류 (차트 다운로드 시)
    if any(word in stderr_lower for word in ["timeout", "connection", "network"]):
        message = (
            f"차트 다운로드 실패: {chart_path}\n\n"
            f"해결 방법:\n"
            f"  1. 네트워크 연결을 확인하세요\n"
            f"  2. Helm 레포지토리를 업데이트: helm repo update\n"
            f"  3. 잠시 후 다시 시도하세요"
        )
        return message, TransientError

    # 기본
    message = f"Helm 작업 실패: {chart_path}\n\n상세 오류:\n{stderr}"
    return message, PermanentError
```

### AWS S3 에러 파싱

```python
# src/cli_onprem/services/s3.py

from botocore.exceptions import ClientError


def _parse_s3_error(error: ClientError, operation: str) -> tuple[str, type]:
    """boto3 S3 에러 파싱.

    Args:
        error: boto3의 ClientError
        operation: 작업 설명 (예: "버킷 생성", "파일 업로드")

    Returns:
        (error_message, error_class) 튜플
    """
    error_code = error.response["Error"]["Code"]
    error_message = error.response["Error"]["Message"]

    # 자격증명 문제
    if error_code in ["InvalidAccessKeyId", "SignatureDoesNotMatch"]:
        message = (
            f"AWS 자격증명 오류\n\n"
            f"원인:\n"
            f"  - Access Key 또는 Secret Key가 잘못되었습니다\n\n"
            f"해결 방법:\n"
            f"  1. 자격증명 재설정: cli-onprem s3-share init-credential\n"
            f"  2. 또는 AWS CLI로 설정: aws configure\n"
            f"  3. IAM에서 Access Key 확인"
        )
        return message, PermanentError

    # 권한 부족
    if error_code in ["AccessDenied", "Forbidden"]:
        message = (
            f"S3 권한 부족\n\n"
            f"원인:\n"
            f"  - IAM 사용자에게 {operation} 권한이 없습니다\n\n"
            f"해결 방법:\n"
            f"  1. IAM 정책을 확인하세요\n"
            f"  2. 필요한 권한: s3:PutObject, s3:GetObject 등\n"
            f"  3. 관리자에게 권한을 요청하세요\n\n"
            f"상세:\n  {error_message}"
        )
        return message, PermanentError

    # 버킷 없음
    if error_code == "NoSuchBucket":
        message = (
            f"S3 버킷을 찾을 수 없습니다\n\n"
            f"원인:\n"
            f"  - 버킷이 존재하지 않거나 삭제되었습니다\n"
            f"  - 또는 리전이 잘못되었습니다\n\n"
            f"해결 방법:\n"
            f"  1. 버킷 이름을 확인하세요\n"
            f"  2. 버킷 생성: cli-onprem s3-share init-bucket\n"
            f"  3. AWS 콘솔에서 버킷 확인:\n"
            f"     https://s3.console.aws.amazon.com/s3/buckets"
        )
        return message, PermanentError

    # 토큰 만료
    if error_code in ["ExpiredToken", "TokenRefreshRequired"]:
        message = (
            f"AWS 토큰 만료\n\n"
            f"원인:\n"
            f"  - 세션 토큰이 만료되었습니다 (MFA 사용 시 흔함)\n\n"
            f"해결 방법:\n"
            f"  1. 자격증명 재설정: cli-onprem s3-share init-credential\n"
            f"  2. MFA 사용 시 새 세션 토큰 발급:\n"
            f"     aws sts get-session-token --serial-number arn:... --token-code 123456"
        )
        return message, PermanentError

    # 네트워크 오류
    if error_code in ["RequestTimeout", "ServiceUnavailable"]:
        message = (
            f"{operation} 일시 실패\n\n"
            f"원인:\n"
            f"  - 네트워크 타임아웃 또는 S3 일시 장애\n\n"
            f"해결 방법:\n"
            f"  - 잠시 후 다시 시도하세요 (자동 재시도 중...)"
        )
        return message, TransientError

    # 기본
    message = f"{operation} 실패\n\n상세 오류:\n  {error_code}: {error_message}"
    return message, PermanentError
```

## 사용자 친화적 메시지

### 메시지 구조

좋은 에러 메시지의 구조:

```
[상황 요약]
원인:
  - 문제의 근본 원인
해결 방법:
  1. 구체적인 조치 1
  2. 구체적인 조치 2
  3. 추가 정보 링크

[선택사항: 실행 명령]
[선택사항: 상세 오류]
```

### 예시

#### ❌ 나쁜 메시지
```
Error: operation failed
Command returned exit code 1
```

#### ✅ 좋은 메시지
```
Docker 이미지 다운로드 실패: nginx:latest

원인:
  - Docker daemon이 응답하지 않습니다

해결 방법:
  1. Docker Desktop을 시작하세요
  2. 상태 확인: docker info
  3. 재시작: sudo systemctl restart docker (Linux)

실행 명령:
  docker pull --platform linux/amd64 nginx:latest

상세 오류:
  Cannot connect to the Docker daemon at unix:///var/run/docker.sock.
  Is the docker daemon running?
```

## 재시도 전략

### 어떤 에러를 재시도해야 하는가?

```python
def _is_retryable(error_class: type) -> bool:
    """에러가 재시도 가능한지 확인"""
    return error_class == TransientError
```

### 재시도 로직 패턴

```python
def operation_with_retry(
    operation: Callable,
    max_retries: int = 3,
    backoff_factor: int = 2,
) -> Any:
    """재시도 로직이 있는 작업 실행.

    Args:
        operation: 실행할 함수
        max_retries: 최대 재시도 횟수
        backoff_factor: Exponential backoff 배수

    Raises:
        마지막 시도의 예외
    """
    for attempt in range(1, max_retries + 1):
        try:
            return operation()

        except TransientError as e:
            if attempt < max_retries:
                wait_time = backoff_factor ** attempt
                logging.warning(
                    f"일시적 오류 발생. {wait_time}초 후 재시도 "
                    f"({attempt}/{max_retries})"
                )
                time.sleep(wait_time)
                continue
            else:
                # 마지막 시도 실패
                logging.error(f"최대 재시도 횟수 초과: {e}")
                raise

        except (PermanentError, DependencyError):
            # 재시도 불가능한 에러는 즉시 발생
            raise
```

## 테스트 전략

### 에러 파싱 테스트

```python
# tests/test_error_parsing.py

def test_parse_docker_auth_error():
    """Docker 인증 에러 파싱"""
    stderr = "Error: denied: requested access to the resource is denied"

    message, error_class = _parse_docker_error(stderr, "private/image:latest")

    assert error_class == PermanentError
    assert "접근 권한이 없습니다" in message
    assert "docker login" in message


def test_parse_docker_network_error():
    """Docker 네트워크 에러 파싱"""
    stderr = "Error: net/http: TLS handshake timeout"

    message, error_class = _parse_docker_error(stderr, "nginx:latest")

    assert error_class == TransientError
    assert "네트워크" in message
    assert "재시도" in message
```

### 재시도 로직 테스트

```python
# tests/test_retry_logic.py

def test_retry_on_transient_error(mocker):
    """TransientError는 재시도됨"""
    mock_operation = mocker.Mock(
        side_effect=[
            TransientError("네트워크 타임아웃"),
            TransientError("네트워크 타임아웃"),
            "success"  # 3번째 시도에서 성공
        ]
    )

    result = operation_with_retry(mock_operation, max_retries=3)

    assert result == "success"
    assert mock_operation.call_count == 3


def test_no_retry_on_permanent_error(mocker):
    """PermanentError는 재시도하지 않음"""
    mock_operation = mocker.Mock(
        side_effect=PermanentError("이미지 없음")
    )

    with pytest.raises(PermanentError):
        operation_with_retry(mock_operation, max_retries=3)

    assert mock_operation.call_count == 1  # 한 번만 호출
```

## 명령 레벨 에러 처리

### 일관된 패턴

```python
# src/cli_onprem/commands/docker_tar.py

@app.command()
def save(...):
    """Docker 이미지 저장"""
    init_logging(quiet=quiet, verbose=verbose)

    try:
        # Health check
        check_docker_daemon()

        # 작업 수행
        for image in images:
            pull_image(image, arch)
            save_image(image, output_dir)

        console.print("[green]✓[/green] 완료")

    except DependencyError as e:
        # 의존성 오류 (exit code: 2)
        console.print(f"[yellow]의존성 오류:[/yellow]\n{e}")
        raise typer.Exit(code=2)

    except (TransientError, PermanentError) as e:
        # 명령 실행 오류 (exit code: 1)
        console.print(f"[red]오류:[/red]\n{e}")
        raise typer.Exit(code=1)

    except Exception as e:
        # 예상치 못한 오류 (exit code: 1)
        console.print(f"[red]예상치 못한 오류:[/red]\n{e}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(code=1)
```

## 결론

### 핵심 원칙

1. **Fail Fast** - 작업 전에 사전 검증
2. **명확한 분류** - Transient vs Permanent vs Dependency
3. **친화적 메시지** - 원인 + 해결 방법
4. **적절한 재시도** - 일시적 오류만 재시도
5. **디버깅 정보** - 명령어와 stderr 포함

### 체크리스트

에러 핸들링 구현 시:
- [ ] 에러를 Transient/Permanent로 분류했는가?
- [ ] 사용자 친화적인 한국어 메시지를 제공하는가?
- [ ] 구체적인 해결 방법을 제시하는가?
- [ ] 디버깅에 필요한 정보(명령어, stderr)를 포함하는가?
- [ ] 재시도가 필요한 경우 적절한 로직을 구현했는가?
- [ ] 테스트를 작성했는가?

---

**작성일**: 2025-01-30
**버전**: 1.0
**관련 문서**: [SUBPROCESS_WRAPPER.md](SUBPROCESS_WRAPPER.md), [REFACTORING.md](../../REFACTORING.md)
