# S3 공유 명령어

`s3-share` 명령어는 AWS S3 버킷에 접근하기 위한 자격증명을 관리하는 기능을 제공합니다.

## 목적

AWS S3 버킷에 접근하기 위한 자격증명을 안전하게 관리하고, 여러 프로파일을 통해 다양한 S3 버킷에 접근할 수 있도록 합니다.

## 사용법

```bash
# 기본 사용법 (default_profile 생성)
cli-onprem s3-share init

# 특정 프로파일 생성
cli-onprem s3-share init --profile staging

# 기존 프로파일 덮어쓰기
cli-onprem s3-share init --profile production --overwrite
```

## 서브커맨드

### init

`~/.cli-onprem/credential.yaml` 파일을 생성하거나 갱신합니다.

#### 옵션

| 옵션 | 설명 |
|------|------|
| `--profile TEXT` | 생성·수정할 프로파일 이름 (기본값: `default_profile`) |
| `--overwrite/--no-overwrite` | 동일 프로파일 존재 시 덮어쓸지 여부 (기본값: `--no-overwrite`) |
| `--bucket TEXT` | S3 버킷 (자동완성 지원) |
| `--prefix TEXT` | S3 프리픽스 (자동완성 지원, 폴더 단위로 단계별 탐색) |

## 예제

### 기본 프로파일 생성

```bash
cli-onprem s3-share init
AWS Access Key? ···
AWS Secret Key? ···
Region? [us-west-2]: 
Bucket? my-bucket
Prefix? backups/
자격증명 저장됨: 프로파일 "default_profile"
```

> 참고: Region의 기본값은 `us-west-2`로 설정되어 있습니다.

### 특정 프로파일 생성

```bash
cli-onprem s3-share init --profile staging
AWS Access Key? ···
AWS Secret Key? ···
Region? us-west-2
Bucket? staging-artifacts
Prefix? releases/
자격증명 저장됨: 프로파일 "staging"
```

### 기존 프로파일 덮어쓰기

```bash
cli-onprem s3-share init --profile production --overwrite
AWS Access Key? ···
AWS Secret Key? ···
Region? us-east-1
Bucket? production-data
Prefix? archives/
자격증명 저장됨: 프로파일 "production"
```

## 자격증명 파일 구조

`~/.cli-onprem/credential.yaml` 파일은 다음과 같은 구조로 저장됩니다:

```yaml
default_profile:
  aws_access_key: AKIAIOSFODNN7EXAMPLE
  aws_secret_key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
  region: us-west-2
  bucket: my-bucket
  prefix: backups/
staging:
  aws_access_key: AKIAI44QH8DHBEXAMPLE
  aws_secret_key: je7MtGbClwBF/2Zp9Utk/h3yCo8nvbEXAMPLEKEY
  region: us-west-2
  bucket: staging-artifacts
  prefix: releases/
```

## 보안

자격증명 파일은 생성 시 권한이 600(소유자만 읽기/쓰기 가능)으로 설정되어 다른 사용자가 접근할 수 없도록 보호됩니다.

## 오류 처리

다음과 같은 경우 명령어는 오류 코드(1)와 함께 종료됩니다:
- 자격증명 파일 로드 실패
- 자격증명 파일 저장 실패

## 자동완성 기능

CLI-ONPREM은 쉘 자동완성 기능을 지원합니다:

1. 쉘 자동완성 활성화:
```bash
cli-onprem --install-completion [bash|zsh|fish]
```

2. 명령어 자동완성:
`s3-share` 명령어 사용 시 Tab 키를 누르면 서브커맨드와 옵션이 자동으로 제안됩니다.

3. S3 버킷 및 프리픽스 자동완성:
```bash
# 버킷 자동완성
cli-onprem s3-share init --bucket <Tab>

# 프리픽스 자동완성 (폴더 단위로 단계별 탐색)
cli-onprem s3-share init --prefix <Tab>
cli-onprem s3-share init --prefix folder1/<Tab>
cli-onprem s3-share init --prefix folder1/folder2/<Tab>
```

> 참고: 프리픽스 자동완성은 폴더 구조를 단계별로 탐색할 수 있도록 구현되어 있습니다. 사용자가 경로를 입력할 때마다 현재 경로의 하위 폴더와 파일만 표시됩니다.
