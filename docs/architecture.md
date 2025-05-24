# CLI-ONPREM 아키텍처

## 개요

CLI-ONPREM은 함수형 프로그래밍 접근 방식을 따르며 명확한 관심사 분리를 통해 간단하고 테스트 가능하며 유지보수가 쉬운 구조를 지향합니다.

## 디렉토리 구조

```
src/cli_onprem/
├── core/                      # 핵심 프레임워크 기능
│   ├── __init__.py
│   ├── cli.py                # CLI 헬퍼 함수
│   ├── errors.py             # 에러 처리 함수 및 타입
│   ├── logging.py            # 로깅 설정
│   └── types.py              # 공통 타입 정의
│
├── utils/                     # 순수 유틸리티 함수
│   ├── __init__.py
│   ├── shell.py              # 셸 명령 실행
│   ├── file.py               # 파일 작업
│   ├── formatting.py         # 출력 포맷팅
│   └── validation.py         # 입력 검증
│
├── services/                  # 도메인별 비즈니스 로직
│   ├── __init__.py
│   ├── docker.py             # Docker 관련 함수
│   ├── helm.py               # Helm 관련 함수
│   ├── s3.py                 # AWS S3 작업
│   └── archive.py            # 압축 및 분할 함수
│
├── commands/                  # CLI 명령어 (얇은 레이어)
│   ├── __init__.py
│   ├── docker_tar.py         # Docker tar 명령
│   ├── helm_local.py         # Helm 로컬 작업
│   ├── s3_share.py           # S3 공유 기능
│   └── tar_fat32.py          # FAT32 호환 압축
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
- CLI 컨텍스트 및 설정 관리
- 중앙화된 에러 처리
- 로깅 설정
- 공통 타입 정의

### Utils 레이어 (`utils/`)
어디서든 사용할 수 있는 순수 유틸리티 함수:
- **shell.py**: `run_command()`, `check_command_exists()`
- **file.py**: `safe_write()`, `ensure_dir()`, `read_yaml()`
- **formatting.py**: `format_json()`, `format_table()`, `format_csv()`
- **validation.py**: `validate_path()`, `validate_image_name()`

### Services 레이어 (`services/`)
관심사별로 구성된 도메인 특화 비즈니스 로직:

#### docker.py
```python
- check_docker_installed() -> None
- pull_image(reference: str, platform: str = None) -> None
- save_image(reference: str, output_path: Path) -> None
- parse_image_reference(reference: str) -> ImageReference
- normalize_image_name(image: str) -> str
- extract_images_from_yaml(yaml_content: str, normalize: bool = True) -> list[str]
```

#### helm.py
```python
- check_helm_installed() -> None
- extract_chart(archive_path: Path, dest_dir: Path) -> Path
- prepare_chart(chart_path: Path, workdir: Path) -> Path
- update_dependencies(chart_dir: Path) -> None
- render_template(chart_path: Path, values_files: list[Path] = None) -> str
```

#### s3.py
```python
- create_client(profile: dict) -> boto3.client
- sync_files(client, local_path: Path, bucket: str, prefix: str, **options) -> None
- generate_presigned_url(client, bucket: str, key: str, expires_in: int) -> str
- calculate_md5(file_path: Path) -> str
- list_objects(client, bucket: str, prefix: str) -> list[dict]
```

#### archive.py
```python
- compress_path(path: Path, output: Path) -> None
- split_file(file_path: Path, chunk_size: str, output_dir: Path) -> list[Path]
- create_manifest(parts: list[Path], output_path: Path) -> None
- verify_integrity(manifest_path: Path) -> bool
- generate_restore_script(purge: bool = False) -> str
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