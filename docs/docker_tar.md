# 🐳 docker-tar 명령어

> 💡 **빠른 시작**: `cli-onprem docker-tar save nginx:latest`

## 📋 목차

- [개요](#개요)
- [사용 시나리오](#사용-시나리오)
- [사용법](#사용법)
- [옵션](#옵션)
- [예제](#예제)
- [고급 기능](#고급-기능)
- [문제 해결](#문제-해결)
- [관련 명령어](#관련-명령어)

## 개요

`docker-tar` 명령어는 Docker 이미지를 표준화된 이름의 tar 파일로 저장하는 기능을 제공합니다. 
오프라인 환경에서 Docker 이미지를 배포하거나 백업할 때 유용하며, 멀티 아키텍처 지원과 자동 재시도 기능을 포함합니다.

### 주요 특징

- ✨ **멀티 아키텍처 지원**: linux/amd64, linux/arm64 아키텍처별 이미지 저장
- ✨ **스마트 파일명 생성**: 레지스트리, 네임스페이스, 태그, 아키텍처 기반 표준화된 파일명
- ✨ **자동 재시도 기능**: 네트워크 오류 시 자동으로 재시도하여 안정성 향상
- ✨ **스트리밍 지원**: stdout 출력으로 파이프라인 처리 가능
- ✨ **안전한 덮어쓰기**: --force 옵션으로 기존 파일 보호

## 사용 시나리오

이 명령어는 다음과 같은 상황에서 유용합니다:

1. **오프라인 환경 배포**: 인터넷이 제한된 환경에서 Docker 이미지 전달
2. **백업 및 아카이브**: 중요한 Docker 이미지의 백업 생성
3. **CI/CD 파이프라인**: 빌드된 이미지를 아티팩트로 저장
4. **멀티 아키텍처 배포**: ARM64, AMD64 등 다양한 아키텍처용 이미지 준비

## 사용법

### 기본 문법

```bash
cli-onprem docker-tar save <reference> [OPTIONS]
```

### 빠른 예제

```bash
# 가장 기본적인 사용법
cli-onprem docker-tar save nginx:latest
```

## 옵션

### 필수 인자

| 인자 | 설명 | 형식 | 예시 |
|------|------|------|------|
| `<reference>` | Docker 이미지 레퍼런스 | `[registry/][namespace/]image[:tag]` | `nginx:latest` |

### 선택 옵션

| 옵션 | 약어 | 설명 | 기본값 | 예시 |
|------|------|------|--------|------|
| `--arch` | - | 대상 아키텍처 지정 | `linux/amd64` | `--arch linux/arm64` |
| `--destination` | `-d` | 저장 위치 (디렉토리 또는 파일 경로) | 현재 디렉토리 | `-d /backup` |
| `--force` | `-f` | 기존 파일 덮어쓰기 허용 | `false` | `--force` |
| `--quiet` | `-q` | 에러 메시지만 출력 | `false` | `--quiet` |
| `--dry-run` | - | 실제 저장 없이 파일명만 출력 | `false` | `--dry-run` |
| `--verbose` | `-v` | 상세 디버그 로그 출력 | `false` | `--verbose` |

### 고급 옵션

| 옵션 | 설명 | 사용 시 주의사항 |
|------|------|-----------------|
| `--stdout` | tar 스트림을 표준 출력으로 내보냄 | 파이프라인 사용 시에만 권장, 파일로 저장되지 않음 |

## 예제

### 🎯 기본 사용 예제

```bash
# 예제 1: 기본 이미지 저장
cli-onprem docker-tar save nginx:1.25.4
# 결과: ./nginx__1.25.4__linux_amd64.tar 생성

# 예제 2: ARM64 아키텍처 이미지 저장
cli-onprem docker-tar save alpine:3.20 --arch linux/arm64
# 결과: ./alpine__3.20__linux_arm64.tar 생성

# 예제 3: 특정 디렉토리에 저장
cli-onprem docker-tar save redis:7.2 --destination /var/backup
# 결과: /var/backup/redis__7.2__linux_amd64.tar 생성
```

### 🚀 실무 활용 예제

#### 1. 프라이빗 레지스트리 이미지 백업

```bash
# 프라이빗 레지스트리 이미지 저장
cli-onprem docker-tar save registry.company.com/myapp/api:v1.2.3 \
  --destination /backup/images \
  --force

# 결과 확인
ls -la /backup/images/
# registry.company.com__myapp__api__v1.2.3__linux_amd64.tar
```

#### 2. 멀티 아키텍처 이미지 일괄 백업

```bash
# 스크립트에서 사용
#!/bin/bash
IMAGES=("nginx:latest" "redis:7.2" "postgres:15")
ARCHITECTURES=("linux/amd64" "linux/arm64")

for image in "${IMAGES[@]}"; do
  for arch in "${ARCHITECTURES[@]}"; do
    cli-onprem docker-tar save "$image" --arch "$arch" --destination ./backup
  done
done
```

#### 3. 압축과 함께 스트리밍 저장

```bash
# 파이프라인과 함께 사용
cli-onprem docker-tar save ubuntu:22.04 --stdout | gzip > ubuntu__22.04__linux_amd64.tar.gz

# S3에 직접 업로드
cli-onprem docker-tar save myapp:latest --stdout | \
  aws s3 cp - s3://my-bucket/images/myapp__latest__linux_amd64.tar
```

### 📝 출력 예시

```
INFO: Pulling image nginx:latest for platform linux/amd64...
INFO: Image pulled successfully
INFO: Saving image to nginx__latest__linux_amd64.tar...
INFO: Image saved successfully (142.3 MB)
```

## 고급 기능

### 스마트 파일명 생성 규칙

Docker 이미지 레퍼런스를 표준화된 파일명으로 변환합니다:

```bash
# 변환 규칙 예시
docker.io/library/nginx:latest     → nginx__latest__linux_amd64.tar
ghcr.io/bitnami/redis:7.2.4       → ghcr.io__bitnami__redis__7.2.4__linux_amd64.tar
registry.k8s.io/pause:3.9         → registry.k8s.io__pause__3.9__linux_amd64.tar
```

**변환 규칙**:
- 필드 구분자: `__` (더블 언더스코어)
- 슬래시(`/`) → 언더스코어(`_`)로 치환
- `docker.io` 레지스트리는 생략
- `library` 네임스페이스는 생략

### 자동 재시도 메커니즘

네트워크 불안정 환경에서도 안정적으로 동작하도록 자동 재시도 기능을 제공합니다:

```bash
# 재시도 로직이 포함된 상세 로그 확인
cli-onprem docker-tar save large-image:latest --verbose
```

## 문제 해결

### 자주 발생하는 문제

#### ❌ 오류: `Error response from daemon: pull access denied`

**원인**: Docker 레지스트리 인증 실패

**해결 방법**:
```bash
# Docker 로그인 후 재시도
docker login registry.example.com
cli-onprem docker-tar save registry.example.com/private/image:latest
```

#### ❌ 오류: `No space left on device`

**원인**: 디스크 용량 부족

**해결 방법**:
1. 디스크 용량 확인: `df -h`
2. 불필요한 Docker 이미지 정리: `docker system prune`
3. 다른 디스크로 저장 위치 변경: `--destination /other/disk/path`

#### ❌ 오류: `manifest unknown: manifest unknown`

**원인**: 지정된 태그나 아키텍처가 존재하지 않음

**해결 방법**:
```bash
# 사용 가능한 태그 확인
docker manifest inspect nginx:latest

# 다른 아키텍처 시도
cli-onprem docker-tar save nginx:latest --arch linux/amd64
```

### 디버깅 팁

- 💡 `--verbose` 옵션을 사용하여 상세 로그 확인
- 💡 `--dry-run` 옵션으로 실제 실행 전 테스트
- 💡 `--quiet` 옵션으로 스크립트에서 에러만 캡처

## 관련 명령어

- 📌 [`helm-local`](./helm-local.md) - Helm 차트에서 이미지 추출 후 docker-tar로 저장
- 📌 [`s3-share`](./s3-share.md) - 저장된 tar 파일을 S3로 업로드하여 공유
- 📌 [`tar-fat32`](./tar-fat32.md) - 큰 Docker 이미지를 FAT32 호환 형태로 분할

---

<details>
<summary>📚 추가 참고 자료</summary>

- [Docker 멀티 아키텍처 빌드 가이드](https://docs.docker.com/build/building/multi-platform/)
- [Docker 이미지 레이어 최적화](https://docs.docker.com/develop/dev-best-practices/)

</details>

<details>
<summary>🔄 변경 이력</summary>

- v0.11.0: 목적지 디렉토리 지원 추가
- v0.10.0: 멀티 아키텍처 지원 및 자동 재시도 기능 추가
- v0.9.0: 초기 릴리즈

</details>