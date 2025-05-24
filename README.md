# CLI-ONPREM

인프라 엔지니어를 위한 반복 작업 자동화를 위한 Typer 기반 Python CLI 도구입니다.

## 기능

- 간단하고 직관적인 명령줄 인터페이스
- 색상과 서식이 있는 풍부한 텍스트 출력
- 디렉토리 스캔 및 보고
- 포괄적인 문서화

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

```bash
# 도움말 보기
cli-onprem --help

# 쉘 자동완성 활성화
cli-onprem --install-completion

# 특정 쉘에 대해 자동완성 활성화
cli-onprem --install-completion bash  # 또는 zsh, fish
```

## 개발

이 프로젝트는 다음을 사용합니다:
- 패키지 관리를 위한 `uv`
- 코드 품질을 위한 `pre-commit` 훅
- 린팅 및 포맷팅을 위한 `ruff`, `black`, `mypy`
- CI/CD를 위한 GitHub Actions

## 개발 환경 설정

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

## 문서

각 명령어에 대한 자세한 문서는 `docs/` 디렉토리에서 확인할 수 있습니다:
- [Helm Local 명령어](docs/helm-local.md)
- [Docker Tar 명령어](docs/docker_tar.md)
- [Tar-Fat32 명령어](docs/tar-fat32.md)
- [S3 공유 명령어](docs/s3-share.md)
- [PyPI 등록 과정](docs/pypi.md)
- [버전 관리 방식](docs/versioning.md)

## 라이선스

MIT 라이선스
