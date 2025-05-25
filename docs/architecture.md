# CLI-ONPREM 아키텍처

## 개요

CLI-ONPREM은 함수형 프로그래밍 접근 방식을 따르며 명확한 관심사 분리를 통해 간단하고 테스트 가능하며 유지보수가 쉬운 구조를 지향합니다.

## 디렉토리 구조

```
src/cli_onprem/
├── core/                      # 핵심 프레임워크 기능
│   ├── __init__.py
│   ├── errors.py             # 에러 처리 함수 및 타입
│   ├── logging.py            # 로깅 설정
│   └── types.py              # 공통 타입 정의
│
├── utils/                     # 순수 유틸리티 함수
│   ├── __init__.py
│   ├── shell.py              # 셸 명령 실행
│   ├── file.py               # 파일 작업
│   ├── formatting.py         # 출력 포맷팅
│   ├── fs.py                 # 파일시스템 작업
│   └── hash.py               # 해시 계산 (MD5, SHA256)
│
├── services/                  # 도메인별 비즈니스 로직
│   ├── __init__.py
│   ├── docker.py             # Docker 관련 함수
│   ├── helm.py               # Helm 관련 함수
│   ├── s3.py                 # AWS S3 작업
│   ├── archive.py            # 압축 및 분할 함수
│   └── credential.py         # AWS 자격증명 관리
│
├── commands/                  # CLI 명령어 (얇은 레이어)
│   ├── __init__.py
│   ├── docker_tar.py         # Docker tar 명령
│   ├── helm_local.py         # Helm 로컬 작업
│   ├── s3_share.py           # S3 공유 기능
│   └── tar_fat32.py          # FAT32 호환 압축
│
├── libs/                      # 외부 라이브러리 래퍼 (현재 비어있음)
│
└── __main__.py               # 진입점
```

## 설계 원칙

### 1. 함수형 프로그래밍
- 부작용이 없는 순수 함수 선호
- 전역 상태 대신 명시적 매개변수 사용
- 상태 변경 대신 값 반환
- 복잡한 작업은 작은 함수들의 조합으로 구성

### 2. 관심사 분리
- **Commands**: 서비스 호출을 조율하는 얇은 CLI 레이어
- **Services**: 도메인별 비즈니스 로직
- **Utils**: 범용 유틸리티 함수
- **Core**: 프레임워크 수준의 기능

### 3. 의존성 방향
```
Commands → Services → Utils
    ↓          ↓        ↓
          Core ←────────┘
```

### 4. 타입 안전성
- 모든 함수에 타입 힌트 사용
- 복잡한 데이터 구조는 TypedDict 활용
- Any 타입보다 명시적 타입 선호

## 모듈별 책임

### Core 레이어 (`core/`)
모든 명령어에서 공유하는 프레임워크 수준의 기능:
- 중앙화된 에러 처리 (CustomError, ErrorContext)
- 로깅 설정 및 관리
- 공통 타입 정의 (ImageReference, S3Config 등)

### Utils 레이어 (`utils/`)
어디서든 사용할 수 있는 순수 유틸리티 함수:
- **shell.py**: `run_command()`, `check_command_exists()`
- **file.py**: `ensure_dir()`, `read_yaml()`, `write_yaml()`, `extract_tar()`
- **formatting.py**: `format_json()`, `format_list()`
- **fs.py**: `find_completable_paths()`, `find_pack_directories()`, `create_size_marker()`, `generate_restore_script()`, `make_executable()`
- **hash.py**: `calculate_file_md5()`, `calculate_file_sha256()`, `verify_file_md5()`, `verify_file_sha256()`

### Services 레이어 (`services/`)
관심사별로 구성된 도메인 특화 비즈니스 로직:

#### docker.py
```python
- check_docker_installed() -> None
- normalize_image_name(image: str) -> str
- extract_images_from_yaml(yaml_content: str, normalize: bool = True) -> list[str]
- parse_image_reference(reference: str) -> tuple[str, str, str, str]
- generate_tar_filename(image: str, tag: str, arch: str, extension: str = "tar") -> str
- check_image_exists(reference: str) -> bool
- pull_image(reference: str, arch: str = "linux/amd64", max_retries: int = 3) -> None
- save_image(reference: str, output_path: str) -> None
- save_image_to_stdout(reference: str) -> None
- list_local_images() -> list[str]
```

#### helm.py
```python
- check_helm_installed() -> None
- extract_chart(archive_path: Path, dest_dir: Path) -> Path
- prepare_chart(chart_path: Path, workdir: Path) -> Path
- update_dependencies(chart_dir: Path) -> None
- render_template(chart_path: Path, values_files: list[Path] = None, include_crds: bool = True) -> str
```

#### s3.py
```python
- create_s3_client(aws_access_key: str, aws_secret_key: str, region: str) -> Any
- list_buckets(s3_client: Any) -> list[str]
- list_objects(s3_client: Any, bucket: str, prefix: str = "", max_keys: int = 1000) -> list[dict]
- upload_file(s3_client: Any, file_path: Path, bucket: str, key: str, callback: Any = None) -> None
- delete_objects(s3_client: Any, bucket: str, keys: list[str]) -> dict[str, Any]
- generate_presigned_url(s3_client: Any, bucket: str, key: str, expires_in: int = 3600) -> str
- head_object(s3_client: Any, bucket: str, key: str) -> dict[str, Any]
- sync_to_s3(s3_client: Any, local_path: Path, bucket: str, prefix: str = "", exclude_patterns: list[str] = None, force: bool = False) -> None
- generate_s3_path(src_path: Path, s3_prefix: str) -> str
```

#### archive.py
```python
- create_tar_archive(input_path: Path, output_path: Path, parent_dir: Path) -> None
- split_file(file_path: Path, part_size: str, output_dir: Path = None, max_parts: int = 999) -> list[Path]
- calculate_sha256_manifest(pack_dir: Path, glob_pattern: str = "*") -> list[tuple[str, str]]
- write_manifest_file(manifest: list[tuple[str, str]], output_path: Path) -> None
- verify_manifest(manifest_path: Path) -> None
- merge_files(parts_dir: Path, output_path: Path, pattern: str = "*") -> None
- extract_tar_archive(archive_path: Path, extract_to: Path, strip_components: int = 0) -> None
- get_directory_size_mb(path: Path) -> int
```

#### credential.py
```python
- get_config_dir() -> Path
- get_credential_path() -> Path
- ensure_config_directory() -> Path
- load_credentials() -> dict[str, dict[str, str]]
- save_credentials(credentials: dict[str, dict[str, str]]) -> None
- get_profile_credentials(profile: str, check_aws: bool = True, check_bucket: bool = False) -> dict[str, str]
- create_or_update_profile(profile: str, **kwargs) -> None
- list_profiles() -> list[str]
- profile_exists(profile: str) -> bool
```

### Commands 레이어 (`commands/`)
다음 작업을 수행하는 얇은 조율 레이어:
1. Typer를 사용한 CLI 인터페이스 정의
2. 입력값 검증
3. 서비스 함수 호출
4. 출력 포맷팅
5. 우아한 에러 처리

## 예시: helm-local 리팩토링

### Before (모놀리식)
```python
# commands/helm_local.py (486줄)
def extract_images(...):
    # CLI 설정
    # Helm 확인
    # 차트 추출
    # 템플릿 렌더링
    # 이미지 파싱
    # 정규화
    # 출력 포맷팅
    # 에러 처리
    # ... 모든 것이 하나의 함수에
```

### After (모듈화)
```python
# commands/helm_local.py (얇은 레이어)
from cli_onprem.services import helm, docker
from cli_onprem.utils import formatting

@app.command()
def extract_images(
    chart: Path,
    values: list[Path] = [],
    json_output: bool = False,
    raw: bool = False
) -> None:
    """Helm 차트에서 Docker 이미지 추출."""
    
    # 서비스 조율
    helm.check_helm_installed()
    
    with tempfile.TemporaryDirectory() as workdir:
        chart_path = helm.prepare_chart(chart, Path(workdir))
        helm.update_dependencies(chart_path)
        
        rendered = helm.render_template(chart_path, values)
        images = docker.extract_images_from_yaml(rendered, normalize=not raw)
        
        # 출력 포맷팅
        if json_output:
            typer.echo(formatting.format_json(images))
        else:
            for image in images:
                typer.echo(image)
```

## 테스트 전략

### 단위 테스트
- 각 서비스 함수를 독립적으로 테스트
- 외부 의존성(Docker, Helm, AWS) 모킹
- 공통 테스트 데이터는 pytest fixture 사용

### 통합 테스트
- 명령어 조율 테스트
- 서비스 간 상호작용 검증
- 파일 작업은 임시 디렉토리 사용

### 테스트 구조 예시
```python
# tests/services/test_helm.py
def test_render_template():
    # 단일 함수를 독립적으로 테스트
    
# tests/services/test_docker.py  
def test_normalize_image_name():
    # 다양한 입력으로 순수 함수 테스트

# tests/commands/test_helm_local.py
def test_extract_images_command():
    # 모킹된 서비스로 전체 명령어 테스트
```

## 장점

1. **유지보수성**: 레이어 간 명확한 경계
2. **테스트 용이성**: 각 함수를 독립적으로 테스트 가능
3. **재사용성**: 여러 명령어에서 서비스 공유 가능
4. **확장성**: 새로운 명령어나 서비스 추가 용이
5. **단순성**: 복잡한 클래스 계층 구조 없음
6. **타입 안전성**: 더 나은 IDE 지원을 위한 완전한 타입 커버리지

## 마이그레이션 가이드

기존 명령어를 리팩토링할 때:

1. 비즈니스 로직 식별 → `services/`로 이동
2. 유틸리티 추출 → `utils/`로 이동
3. CLI 정의는 `commands/`에 유지
4. 테스트의 import 경로 업데이트
5. 하위 호환성 보장

## 향후 고려사항

- 기능 확장을 위한 플러그인 시스템
- 동시 작업을 위한 비동기 지원
- 설정 관리 시스템
- 국제화 지원