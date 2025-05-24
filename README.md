# CLI-ONPREM

인프라 엔지니어를 위한 반복 작업 자동화를 위한 Typer 기반 Python CLI 도구입니다.

## 🚀 주요 기능

### 🐳 Docker 이미지 관리
- **docker-tar**: Docker 이미지를 표준화된 tar 파일로 저장
  - 멀티 아키텍처 지원 (amd64/arm64)
  - 자동 재시도 기능
  - 스마트 파일명 생성

### 📦 Helm 차트 분석
- **helm-local**: Helm 차트에서 Docker 이미지 목록 추출
  - .tgz 아카이브 및 디렉토리 지원
  - 다중 values 파일 적용
  - 이미지 이름 정규화

### ☁️ S3 동기화 및 공유
- **s3-share**: AWS S3와 로컬 파일 동기화
  - 프로파일 기반 자격증명 관리
  - 증분 동기화 (MD5 체크섬)
  - Presigned URL 생성

### 📂 대용량 파일 분할
- **tar-fat32**: FAT32 호환 파일 분할 압축
  - 무결성 검증 (SHA256)
  - 자동 복원 스크립트 생성
  - 설정 가능한 청크 크기

## 설치

```bash
# PyPI에서 설치
pipx install cli-onprem

# 또는 소스에서 설치
git clone https://github.com/cagojeiger/cli-onprem.git
cd cli-onprem
pipx install -e . --force
```

소스에서 설치할 때 일반 사용자는 위 명령어만 실행하면 됩니다.

## 사용법

### 기본 명령어

```bash
# 도움말 보기
cli-onprem --help

# 쉘 자동완성 활성화
cli-onprem --install-completion

# 특정 쉘에 대해 자동완성 활성화
cli-onprem --install-completion bash  # 또는 zsh, fish
```

### 빠른 시작 예제

```bash
# Docker 이미지를 tar로 저장
cli-onprem docker-tar save nginx:latest

# Helm 차트에서 이미지 목록 추출
cli-onprem helm-local extract-images ./mychart.tgz

# S3에 파일 동기화
cli-onprem s3-share sync ./mydata --bucket mybucket

# 대용량 파일 분할 압축
cli-onprem tar-fat32 pack ./large-file --chunk-size 2G
```

## 📚 Commands

### 🐳 docker-tar

Docker 이미지를 tar 파일로 저장하여 오프라인 환경에서 사용할 수 있도록 합니다.

```bash
cli-onprem docker-tar save <image> [options]
```

**주요 옵션:**
- `--arch`: 특정 아키텍처 선택 (기본: 모든 아키텍처)
- `--destination, -d`: 저장 디렉토리 지정
- `--force, -f`: 기존 파일 덮어쓰기
- `--dry-run`: 실제 저장 없이 시뮬레이션

자세한 사용법은 [docker-tar 문서](docs/docker_tar.md)를 참조하세요.

### ⚓ helm-local

Helm 차트에서 사용하는 모든 Docker 이미지를 분석하고 추출합니다.

```bash
cli-onprem helm-local extract-images <chart-path> [options]
```

**주요 옵션:**
- `--values, -f`: 커스텀 values 파일 지정 (여러 개 가능)
- `--json`: JSON 형식으로 출력
- `--raw`: 정규화 없이 원본 이미지 이름 출력

자세한 사용법은 [helm-local 문서](docs/helm-local.md)를 참조하세요.

### ☁️ s3-share

AWS S3를 활용한 안전한 파일 공유 및 동기화 솔루션입니다.

```bash
cli-onprem s3-share <command> [options]
```

**하위 명령어:**
- `init-credential`: AWS 자격 증명 설정
- `init-bucket`: S3 버킷 초기화
- `sync`: 파일 동기화 (증분 백업)
- `presign`: 임시 다운로드 URL 생성

자세한 사용법은 [s3-share 문서](docs/s3-share.md)를 참조하세요.

### 📦 tar-fat32

FAT32 파일 시스템의 4GB 제한을 우회하여 대용량 파일을 분할 압축합니다.

```bash
cli-onprem tar-fat32 <command> [options]
```

**하위 명령어:**
- `pack`: 파일/디렉토리를 분할 압축
- `restore`: 분할된 파일 복원

**주요 기능:**
- SHA256 무결성 검증
- 자동 복원 스크립트 생성
- 진행률 표시

자세한 사용법은 [tar-fat32 문서](docs/tar-fat32.md)를 참조하세요.

## 🛠️ 개발

이 프로젝트는 다음을 사용합니다:
- 패키지 관리를 위한 `uv`
- 코드 품질을 위한 `pre-commit` 훅
- 린팅 및 포맷팅을 위한 `ruff`, `black`, `mypy`
- CI/CD를 위한 GitHub Actions

### 개발 환경 설정

개발에 필요한 의존성은 다음과 같이 설치합니다:

```bash
# 저장소 복제
git clone https://github.com/cagojeiger/cli-onprem.git
cd cli-onprem

# 의존성 설치
uv sync --locked --all-extras --dev

# pre-commit 훅 설치
pre-commit install
```

### 테스트 실행

```bash
pytest
```

## 📖 문서

각 명령어에 대한 자세한 문서는 `docs/` 디렉토리에서 확인할 수 있습니다:
- [Docker Tar 명령어](docs/docker_tar.md)
- [Helm Local 명령어](docs/helm-local.md)
- [S3 공유 명령어](docs/s3-share.md)
- [Tar-Fat32 명령어](docs/tar-fat32.md)
- [PyPI 등록 과정](docs/pypi.md)
- [버전 관리 방식](docs/versioning.md)

## 라이선스

MIT 라이선스
