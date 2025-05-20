# CLI-ONPREM

인프라 엔지니어를 위한 반복 작업 자동화를 위한 Typer 기반 Python CLI 도구입니다. 간단하고 효율적인 명령어로 작업 생산성을 높여줍니다.

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
uv sync --locked --all-extras --dev
pipx install -e . --force
```

## 사용법

```bash
# 도움말 보기
cli-onprem --help

# 인사 명령어
cli-onprem greet hello [이름]

# 디렉토리 스캔
cli-onprem scan directory 경로 [--verbose]
```

## 개발

이 프로젝트는 다음을 사용합니다:
- 패키지 관리를 위한 `uv`
- 코드 품질을 위한 `pre-commit` 훅
- 린팅 및 포맷팅을 위한 `ruff`, `black`, `mypy`
- CI/CD를 위한 GitHub Actions

### 개발 환경 설정

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
- [인사 명령어](docs/greet_ko.md)
- [스캔 명령어](docs/scan_ko.md)

## 라이선스

MIT 라이선스
