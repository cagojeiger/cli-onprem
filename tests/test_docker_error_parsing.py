"""Docker 에러 파싱 테스트."""

from cli_onprem.services.docker import _is_retryable_error, _parse_docker_error


def test_parse_auth_error():
    """인증 오류 파싱."""
    stderr = "Error: denied: requested access to the resource is denied"
    result = _parse_docker_error(stderr, "private/image:latest")

    assert "접근 권한이 없습니다" in result
    assert "docker login" in result
    assert "private/image:latest" in result


def test_parse_unauthorized_error():
    """unauthorized 오류 파싱."""
    stderr = "Error: unauthorized: authentication required"
    result = _parse_docker_error(stderr, "myregistry.io/app:v1")

    assert "접근 권한이 없습니다" in result
    assert "로그인하세요" in result


def test_parse_not_found_error():
    """이미지 없음 오류 파싱."""
    stderr = "Error: manifest for nginx:nonexistent not found"
    result = _parse_docker_error(stderr, "nginx:nonexistent")

    assert "찾을 수 없습니다" in result
    assert "태그가 존재하는지" in result
    assert "nginx:nonexistent" in result


def test_parse_manifest_unknown_error():
    """manifest unknown 오류 파싱."""
    stderr = "Error: manifest unknown: manifest unknown"
    result = _parse_docker_error(stderr, "example/app:latest")

    assert "찾을 수 없습니다" in result
    assert "이미지 이름을 확인" in result


def test_parse_network_timeout_error():
    """네트워크 타임아웃 오류 파싱."""
    stderr = (
        "Error: net/http: request canceled while waiting for connection "
        "(Client.Timeout exceeded)"
    )
    result = _parse_docker_error(stderr, "nginx:latest")

    assert "네트워크 오류" in result
    assert "인터넷 연결을 확인" in result
    assert "nginx:latest" in result


def test_parse_connection_error():
    """연결 오류 파싱."""
    stderr = (
        "Error: Get https://registry-1.docker.io/v2/: dial tcp: "
        "lookup registry-1.docker.io: no such host"
    )
    result = _parse_docker_error(stderr, "redis:alpine")

    assert "네트워크 오류" in result
    assert "VPN이나 프록시" in result


def test_parse_disk_full_error():
    """디스크 공간 부족 오류 파싱."""
    stderr = (
        "Error: failed to register layer: write /var/lib/docker: "
        "no space left on device"
    )
    result = _parse_docker_error(stderr, "postgres:14")

    assert "디스크 공간 부족" in result
    assert "docker system prune" in result
    assert "postgres:14" in result


def test_parse_generic_error():
    """일반 오류 파싱 (특정 패턴 없음)."""
    stderr = "Error: some unknown error occurred"
    result = _parse_docker_error(stderr, "myapp:v1.0")

    assert "이미지 작업 실패" in result
    assert "myapp:v1.0" in result
    assert "some unknown error occurred" in result


def test_is_retryable_timeout():
    """타임아웃은 재시도 가능."""
    stderr = "Error: timeout exceeded while pulling image"
    assert _is_retryable_error(stderr) is True


def test_is_retryable_connection_refused():
    """connection refused는 재시도 가능."""
    stderr = "Error: connection refused to registry"
    assert _is_retryable_error(stderr) is True


def test_is_retryable_connection_reset():
    """connection reset은 재시도 가능."""
    stderr = "Error: connection reset by peer"
    assert _is_retryable_error(stderr) is True


def test_is_retryable_service_unavailable():
    """service unavailable은 재시도 가능."""
    stderr = "Error: 503 Service Unavailable"
    assert _is_retryable_error(stderr) is True


def test_is_retryable_rate_limit():
    """rate limit은 재시도 가능."""
    stderr = "Error: too many requests, please try again later"
    assert _is_retryable_error(stderr) is True


def test_is_retryable_network_generic():
    """일반 network 키워드는 재시도 가능."""
    stderr = "Error: network is unreachable"
    assert _is_retryable_error(stderr) is True


def test_is_not_retryable_auth_error():
    """인증 오류는 재시도 불가능."""
    stderr = "Error: denied: requested access to the resource is denied"
    assert _is_retryable_error(stderr) is False


def test_is_not_retryable_not_found():
    """not found는 재시도 불가능."""
    stderr = "Error: manifest for nginx:fake not found"
    assert _is_retryable_error(stderr) is False


def test_is_not_retryable_disk_full():
    """디스크 부족은 재시도 불가능."""
    stderr = "Error: no space left on device"
    assert _is_retryable_error(stderr) is False


def test_is_not_retryable_generic():
    """알 수 없는 오류는 재시도 불가능."""
    stderr = "Error: some random error"
    assert _is_retryable_error(stderr) is False


def test_case_insensitive_matching():
    """대소문자 구분 없이 매칭."""
    stderr_upper = "Error: TIMEOUT EXCEEDED"
    stderr_mixed = "Error: Connection Refused"

    assert _is_retryable_error(stderr_upper) is True
    assert _is_retryable_error(stderr_mixed) is True
