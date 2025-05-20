# PyPI 등록 과정

이 문서는 CLI-ONPREM 패키지를 PyPI에 등록하는 과정을 설명합니다.

## 사전 준비 사항

- pyproject.toml 파일이 올바르게 구성되어 있어야 합니다.
- GitHub Actions 워크플로우가 설정되어 있어야 합니다.
- PyPI 및 TestPyPI 계정이 필요합니다.

## PyPI 등록 절차

### 1. API 토큰 발급

1. PyPI 계정 생성 및 2FA 활성화
   - [PyPI 웹사이트](https://pypi.org)에서 계정 생성
   - 계정 설정에서 2FA 활성화

2. API 토큰 발급
   - PyPI: [https://pypi.org/manage/account/#api-tokens](https://pypi.org/manage/account/#api-tokens)
   - TestPyPI: [https://test.pypi.org/manage/account/#api-tokens](https://test.pypi.org/manage/account/#api-tokens)

### 2. GitHub Secrets 설정

GitHub 저장소의 Settings → Secrets → Actions에 다음 시크릿을 추가합니다:

- `PYPI_API_TOKEN`: PyPI API 토큰
- `TEST_PYPI_API_TOKEN`: TestPyPI API 토큰

### 3. 자동 배포 워크플로우

프로젝트는 GitHub Actions를 통해 자동으로 배포됩니다. 워크플로우 파일(`.github/workflows/release.yml`)이 이미 설정되어 있습니다:

```yaml
name: Release

on:
  push:
    branches:
      - main

permissions:
  contents: write
  id-token: write

jobs:
  release:
    runs-on: ubuntu-latest
    concurrency: release
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Set up uv
        uses: astral-sh/setup-uv@v1

      - name: Install dependencies
        run: |
          uv sync --locked --all-extras --dev

      - name: Python Semantic Release
        id: release
        run: |
          uv run semantic-release publish
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and publish to TestPyPI
        if: steps.release.outputs.released == 'true'
        run: |
          uv run python -m build
          uv run twine upload --repository-url https://test.pypi.org/legacy/ dist/*
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.TEST_PYPI_API_TOKEN }}

      - name: Build and publish to PyPI
        if: steps.release.outputs.released == 'true'
        run: |
          uv run python -m build
          uv run twine upload dist/*
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
```

### 4. 배포 과정

1. 코드 변경 및 커밋
   - 커밋 메시지는 [Conventional Commits](https://www.conventionalcommits.org/) 형식을 따릅니다.
   - 자세한 내용은 [버전 관리 문서](versioning_ko.md)를 참조하세요.

2. PR 생성 및 병합
   - 변경 사항을 PR로 생성하고 main 브랜치에 병합합니다.

3. 자동 배포
   - main 브랜치에 병합되면 GitHub Actions가 자동으로 실행됩니다.
   - 버전이 자동으로 업데이트되고 PyPI에 배포됩니다.

### 5. 배포 확인

- TestPyPI: [https://test.pypi.org/project/cli-onprem/](https://test.pypi.org/project/cli-onprem/)
- PyPI: [https://pypi.org/project/cli-onprem/](https://pypi.org/project/cli-onprem/)

## 수동 배포 방법

자동 배포가 실패한 경우 수동으로 배포할 수 있습니다:

```bash
# 의존성 설치
uv sync --locked --all-extras --dev

# 빌드
python -m build

# TestPyPI에 배포
twine upload --repository-url https://test.pypi.org/legacy/ dist/*

# PyPI에 배포
twine upload dist/*
```

## 문제 해결

- **인증 오류**: GitHub Secrets가 올바르게 설정되었는지 확인합니다.
- **빌드 오류**: 로컬에서 빌드를 테스트하여 문제를 해결합니다.
- **버전 충돌**: 이미 존재하는 버전으로 배포할 수 없습니다. 버전을 업데이트해야 합니다.
