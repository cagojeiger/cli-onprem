# ☁️ s3-share 명령어

> 💡 **빠른 시작**: `cli-onprem s3-share init-credential`

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

`s3-share` 명령어는 AWS S3를 활용한 안전한 파일 공유 및 동기화 솔루션을 제공합니다.
프로파일 기반 자격증명 관리, 증분 동기화, presigned URL 생성 등의 기능을 통해 효율적인 파일 관리를 지원합니다.

### 주요 특징

- ✨ **프로파일 기반 관리**: 여러 AWS 계정과 버킷을 프로파일로 구분하여 관리
- ✨ **증분 동기화**: MD5 체크섬 기반으로 변경된 파일만 업로드하여 효율성 향상
- ✨ **안전한 공유**: presigned URL을 통한 임시 접근 권한 제공
- ✨ **자동 완성**: 버킷, 프리픽스, 프로파일 자동 완성 지원
- ✨ **보안 강화**: 자격증명 파일 권한 제어 (600)

## 사용 시나리오

이 명령어는 다음과 같은 상황에서 유용합니다:

1. **팀 협업**: 대용량 파일을 팀원들과 안전하게 공유
2. **백업 및 아카이브**: 로컬 파일을 S3로 자동 백업
3. **CI/CD 파이프라인**: 빌드 아티팩트를 S3에 저장 및 배포
4. **다중 환경 관리**: 개발/스테이징/프로덕션 환경별 S3 버킷 관리

## 사용법

### 기본 문법

```bash
cli-onprem s3-share <command> [OPTIONS]
```

### 빠른 예제

```bash
# 1단계: 자격증명 설정
cli-onprem s3-share init-credential

# 2단계: 버킷 설정
cli-onprem s3-share init-bucket

# 3단계: 파일 동기화
cli-onprem s3-share sync ./myfiles
```

## 옵션

### 하위 명령어

| 명령어 | 설명 | 용도 |
|--------|------|------|
| `init-credential` | AWS 자격증명 설정 | 초기 설정 |
| `init-bucket` | S3 버킷 및 프리픽스 설정 | 초기 설정 |
| `sync` | 로컬 폴더와 S3 동기화 | 파일 업로드 |
| `presign` | presigned URL 생성 | 파일 공유 |

## 예제

### 🎯 기본 설정 예제

#### 1. init-credential - 자격증명 설정

```bash
# 기본 프로파일 생성
cli-onprem s3-share init-credential
# 프로파일 'default_profile' 자격증명 설정 중...
# AWS Access Key? ***
# AWS Secret Key? ***
# Region? [us-west-2]: 

# 특정 프로파일 생성
cli-onprem s3-share init-credential --profile production
```

**옵션**:
- `--profile TEXT`: 프로파일 이름 (기본값: `default_profile`)
- `--overwrite/--no-overwrite`: 기존 프로파일 덮어쓰기 여부

#### 2. init-bucket - 버킷 설정

```bash
# 기본 프로파일에 버킷 설정
cli-onprem s3-share init-bucket
# 프로파일 'default_profile' 버킷 설정 중...
# Bucket? my-company-backup
# Prefix? [/]: project-files/

# 특정 프로파일에 버킷 설정
cli-onprem s3-share init-bucket --profile production --bucket prod-bucket --prefix releases/
```

**옵션**:
- `--profile TEXT`: 프로파일 이름
- `--bucket TEXT`: S3 버킷 이름 (자동완성 지원)
- `--prefix TEXT`: S3 프리픽스 (자동완성 지원)

### 🚀 실무 활용 예제

#### 3. sync - 파일 동기화

```bash
# 기본 동기화
cli-onprem s3-share sync ./documents
# 결과: cli-onprem-20250524-documents/ 경로로 업로드

# 고급 옵션과 함께 동기화
cli-onprem s3-share sync ./build-artifacts \
  --profile production \
  --prefix releases/v1.2.3/ \
  --parallel 10 \
  --delete
```

**옵션**:
- `--bucket TEXT`: 동기화할 S3 버킷
- `--prefix TEXT`: 동기화 대상 S3 프리픽스
- `--delete/--no-delete`: 원격에 없는 파일 삭제 여부
- `--parallel INTEGER`: 병렬 업로드 처리 개수
- `--profile TEXT`: 사용할 프로파일 이름

#### 4. presign - URL 생성

```bash
# 폴더 내 모든 파일에 대한 presigned URL 생성
cli-onprem s3-share presign --select-path cli-onprem-20250524-documents

# 단일 파일 URL 생성
cli-onprem s3-share presign --select-path cli-onprem-20250524-report.pdf \
  --expiry 7200 \
  --output sharing-urls.csv
```

**옵션**:
- `--select-path TEXT`: presign URL을 생성할 경로 (자동완성 지원)
- `--output TEXT`: CSV 출력 파일 경로
- `--expiry INTEGER`: URL 만료 시간(초), 기본값: 3600
- `--profile TEXT`: 사용할 프로파일 이름

### 📝 출력 예시

**sync 명령어 출력**:
```
📁 Syncing ./documents to s3://my-bucket/project-files/cli-onprem-20250524-documents/
✅ Uploaded: report.pdf (2.1 MB)
⏭️  Skipped: readme.txt (unchanged)
✅ Uploaded: data.json (156 KB)
📊 Summary: 2 uploaded, 1 skipped, 0 failed
```

**presign 명령어 출력**:
```
📋 Generated presigned URLs:
report.pdf: https://my-bucket.s3.amazonaws.com/project-files/cli-onprem-20250524-documents/report.pdf?AWSAccessKeyId=...
data.json: https://my-bucket.s3.amazonaws.com/project-files/cli-onprem-20250524-documents/data.json?AWSAccessKeyId=...
```

## 고급 기능

### 프로파일 기반 관리

여러 AWS 계정이나 환경을 프로파일로 구분하여 관리할 수 있습니다:

```bash
# 개발 환경 설정
cli-onprem s3-share init-credential --profile dev
cli-onprem s3-share init-bucket --profile dev --bucket dev-bucket

# 스테이징 환경 설정  
cli-onprem s3-share init-credential --profile staging
cli-onprem s3-share init-bucket --profile staging --bucket staging-bucket

# 프로덕션 환경 설정
cli-onprem s3-share init-credential --profile prod
cli-onprem s3-share init-bucket --profile prod --bucket prod-bucket

# 환경별 동기화
cli-onprem s3-share sync ./app --profile dev
cli-onprem s3-share sync ./release --profile prod
```

### 증분 동기화 메커니즘

MD5 체크섬을 기반으로 변경된 파일만 업로드합니다:

```bash
# 첫 번째 동기화: 모든 파일 업로드
cli-onprem s3-share sync ./data
# ✅ Uploaded: file1.txt, file2.txt, file3.txt

# 파일 수정 후 두 번째 동기화: 변경된 파일만 업로드
echo "new content" >> ./data/file1.txt
cli-onprem s3-share sync ./data
# ✅ Uploaded: file1.txt
# ⏭️  Skipped: file2.txt (unchanged)
# ⏭️  Skipped: file3.txt (unchanged)
```

### 자동 경로 생성

업로드 시 자동으로 날짜 기반 경로가 생성됩니다:

```bash
cli-onprem s3-share sync ./myproject
# S3 경로: s3://bucket/prefix/cli-onprem-20250524-myproject/

cli-onprem s3-share sync ./report.pdf  
# S3 경로: s3://bucket/prefix/cli-onprem-20250524-report.pdf
```

## 문제 해결

### 자주 발생하는 문제

#### ❌ 오류: `AWS credentials not found`

**원인**: 자격증명이 설정되지 않음

**해결 방법**:
```bash
# 자격증명 설정
cli-onprem s3-share init-credential --profile your-profile
```

#### ❌ 오류: `Bucket not found or access denied`

**원인**: 버킷이 존재하지 않거나 접근 권한 부족

**해결 방법**:
1. 버킷 이름 확인
2. AWS 콘솔에서 버킷 존재 및 권한 확인
3. 올바른 리전 설정 확인

#### ❌ 오류: `Profile 'xxx' bucket not configured`

**원인**: init-bucket 명령을 실행하지 않음

**해결 방법**:
```bash
# 버킷 설정 실행
cli-onprem s3-share init-bucket --profile xxx
```

### 디버깅 팁

- 💡 자격증명 파일 위치: `~/.cli-onprem/credential.yaml`
- 💡 파일 권한 확인: `ls -la ~/.cli-onprem/credential.yaml` (600이어야 함)
- 💡 AWS CLI와 호환: 동일한 자격증명 사용 가능

## 관련 명령어

- 📌 [`docker-tar`](./docker_tar.md) - Docker 이미지를 tar로 저장 후 S3 업로드
- 📌 [`helm-local`](./helm-local.md) - Helm 차트 파일을 S3로 공유
- 📌 [`tar-fat32`](./tar-fat32.md) - 분할된 파일을 S3로 업로드

---

<details>
<summary>📚 추가 참고 자료</summary>

- [AWS S3 버킷 정책 설정](https://docs.aws.amazon.com/s3/latest/userguide/bucket-policies.html)
- [AWS IAM 사용자 생성 가이드](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_users_create.html)
- [S3 presigned URL 보안 가이드](https://docs.aws.amazon.com/s3/latest/userguide/PresignedUrlUploadObject.html)

</details>

<details>
<summary>🔄 변경 이력</summary>

- v0.11.0: presign 명령어 추가, 자동완성 기능 강화
- v0.10.0: 증분 동기화 성능 개선, 프로파일 관리 기능 추가
- v0.9.0: 초기 릴리즈

</details>