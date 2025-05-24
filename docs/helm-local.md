# ⚓ helm-local 명령어

> 💡 **빠른 시작**: `cli-onprem helm-local extract-images ./mychart.tgz`

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

`helm-local` 명령어는 Helm 차트에서 사용되는 모든 Docker 이미지 참조를 분석하고 추출합니다.
오프라인 환경 배포 준비, 보안 스캔, 의존성 분석 등에 유용하며, 다양한 values 파일을 지원합니다.

### 주요 특징

- ✨ **다중 형식 지원**: .tgz 아카이브 및 디렉토리 차트 모두 지원
- ✨ **다중 values 파일**: 여러 values 파일을 동시에 적용하여 정확한 이미지 추출
- ✨ **이미지 이름 정규화**: 표준화된 형태로 이미지 이름 출력
- ✨ **유연한 출력 형식**: 텍스트, JSON 형식 지원
- ✨ **의존성 처리**: 차트 의존성 자동 업데이트 및 처리

## 사용 시나리오

이 명령어는 다음과 같은 상황에서 유용합니다:

1. **오프라인 환경 준비**: Helm 차트 배포 전 필요한 모든 이미지 사전 다운로드
2. **보안 스캔**: 사용할 이미지 목록을 추출하여 보안 취약점 검사
3. **의존성 분석**: 프로덕션 환경에서 사용할 이미지 목록 파악
4. **CI/CD 파이프라인**: 자동화된 이미지 백업 및 배포 프로세스

## 사용법

### 기본 문법

```bash
cli-onprem helm-local extract-images <chart-path> [OPTIONS]
```

### 빠른 예제

```bash
# 가장 기본적인 사용법
cli-onprem helm-local extract-images ./nginx-chart.tgz
```

## 옵션

### 필수 인자

| 인자 | 설명 | 형식 | 예시 |
|------|------|------|------|
| `<chart-path>` | Helm 차트 경로 | 파일(.tgz) 또는 디렉토리 | `./mychart.tgz` |

### 선택 옵션

| 옵션 | 약어 | 설명 | 기본값 | 예시 |
|------|------|------|--------|------|
| `--values` | `-f` | 추가 values 파일 (여러 개 지정 가능) | - | `-f prod.yaml -f secrets.yaml` |
| `--json` | - | JSON 배열 형식으로 출력 | `false` | `--json` |
| `--quiet` | `-q` | 로그 메시지 숨기기 | `false` | `--quiet` |
| `--raw` | - | 이미지 이름 정규화 없이 원본 출력 | `false` | `--raw` |

## 예제

### 🎯 기본 사용 예제

```bash
# 예제 1: 기본 차트 이미지 추출
cli-onprem helm-local extract-images nginx-13.2.0.tgz
# 결과: docker.io/library/nginx:1.25.4

# 예제 2: 디렉토리 차트에서 추출
cli-onprem helm-local extract-images ./wordpress-chart/
# 결과: 여러 이미지 목록 출력

# 예제 3: JSON 형식 출력
cli-onprem helm-local extract-images prometheus-22.6.1.tgz --json
# 결과: ["docker.io/prom/prometheus:v2.45.0", "docker.io/jimmidyson/configmap-reload:v0.8.0"]
```

### 🚀 실무 활용 예제

#### 1. 프로덕션 환경 이미지 추출

```bash
# 프로덕션 values 파일을 적용하여 실제 사용할 이미지만 추출
cli-onprem helm-local extract-images ./myapp-chart.tgz \
  -f values-prod.yaml \
  -f values-secrets.yaml \
  --quiet

# 결과 확인
# registry.company.com/myapp/api:v1.2.3
# registry.company.com/myapp/worker:v1.2.3
# docker.io/library/redis:7.2-alpine
```

#### 2. 이미지 자동 백업 파이프라인

```bash
# 스크립트에서 사용: 이미지 추출 후 자동 저장
#!/bin/bash
CHART_PATH="./microservices-chart.tgz"
BACKUP_DIR="/backup/images"

# 이미지 목록 추출 및 백업
cli-onprem helm-local extract-images "$CHART_PATH" -f prod-values.yaml | \
  xargs -I {} cli-onprem docker-tar save {} --destination "$BACKUP_DIR"
```

#### 3. 보안 스캔 자동화

```bash
# JSON 형식으로 추출하여 보안 스캔 도구에 전달
IMAGES=$(cli-onprem helm-local extract-images ./app-chart.tgz --json)

# Trivy를 사용한 보안 스캔
echo "$IMAGES" | jq -r '.[]' | while read image; do
  echo "Scanning $image..."
  trivy image "$image"
done
```

#### 4. 다중 환경 이미지 비교

```bash
# 개발/스테이징/프로덕션 환경별 이미지 목록 생성
cli-onprem helm-local extract-images ./chart.tgz -f values-dev.yaml > images-dev.txt
cli-onprem helm-local extract-images ./chart.tgz -f values-staging.yaml > images-staging.txt
cli-onprem helm-local extract-images ./chart.tgz -f values-prod.yaml > images-prod.txt

# 차이점 분석
diff images-dev.txt images-prod.txt
```

### 📝 출력 예시

**텍스트 형식 (기본)**:
```
docker.io/bitnami/wordpress:6.2.1
docker.io/bitnami/mariadb:10.11.2
docker.io/bitnami/apache-exporter:1.0.1
```

**JSON 형식**:
```json
[
  "docker.io/bitnami/wordpress:6.2.1",
  "docker.io/bitnami/mariadb:10.11.2",
  "docker.io/bitnami/apache-exporter:1.0.1"
]
```

## 고급 기능

### 다중 Values 파일 처리

여러 values 파일을 순서대로 적용하여 정확한 이미지 구성을 추출합니다:

```bash
# 우선순위: base < environment < secrets
cli-onprem helm-local extract-images ./chart.tgz \
  -f values-base.yaml \
  -f values-production.yaml \
  -f values-secrets.yaml
```

**적용 순서**:
1. 차트 기본 values.yaml
2. -f 옵션으로 지정한 파일들 (순서대로)
3. 나중에 지정된 값이 이전 값을 덮어씀

### 이미지 이름 정규화

추출된 이미지 이름을 표준화된 형태로 변환합니다:

```bash
# 원본 형태 (--raw 옵션)
nginx                           # 차트에서 그대로
bitnami/wordpress:6.2.1        # 네임스페이스 포함

# 정규화된 형태 (기본)
docker.io/library/nginx:latest # 레지스트리와 태그 추가
docker.io/bitnami/wordpress:6.2.1 # 레지스트리 추가
```

### 의존성 차트 처리

하위 차트(subchart)의 이미지도 자동으로 포함됩니다:

```bash
# Chart.yaml에 dependencies가 있는 경우 자동 처리
cli-onprem helm-local extract-images ./parent-chart.tgz
# 결과에 parent chart + subchart 이미지 모두 포함
```

## 문제 해결

### 자주 발생하는 문제

#### ❌ 오류: `failed to download chart dependencies`

**원인**: 차트 의존성을 다운로드할 수 없음

**해결 방법**:
```bash
# 인터넷 연결 확인 후 재시도
helm repo update
cli-onprem helm-local extract-images ./chart.tgz
```

#### ❌ 오류: `values file not found`

**원인**: 지정한 values 파일이 존재하지 않음

**해결 방법**:
```bash
# 파일 경로 확인
ls -la values-prod.yaml

# 상대 경로로 다시 시도
cli-onprem helm-local extract-images ./chart.tgz -f ./config/values-prod.yaml
```

#### ❌ 경고: `found no images in rendered templates`

**원인**: 차트에서 이미지를 찾을 수 없음

**해결 방법**:
1. values 파일 내용 확인
2. 차트 템플릿에 이미지 정의가 있는지 확인
3. `--raw` 옵션으로 정규화 없이 확인

### 디버깅 팁

- 💡 `helm template` 명령어로 렌더링 결과 직접 확인
- 💡 `--raw` 옵션으로 원본 이미지 이름 확인
- 💡 여러 values 파일 사용 시 우선순위 주의

## 관련 명령어

- 📌 [`docker-tar`](./docker_tar.md) - 추출된 이미지를 tar 파일로 저장
- 📌 [`s3-share`](./s3-share.md) - 이미지 목록을 S3로 공유
- 📌 [`tar-fat32`](./tar-fat32.md) - 큰 이미지를 FAT32 호환 형태로 분할

---

<details>
<summary>📚 추가 참고 자료</summary>

- [Helm 차트 개발 가이드](https://helm.sh/docs/chart_template_guide/)
- [Helm Values 파일 작성법](https://helm.sh/docs/chart_template_guide/values_files/)
- [Kubernetes 이미지 정책](https://kubernetes.io/docs/concepts/containers/images/)

</details>

<details>
<summary>🔄 변경 이력</summary>

- v0.11.0: 다중 values 파일 지원 강화
- v0.10.0: JSON 출력 형식 추가, 이미지 정규화 개선
- v0.9.0: 초기 릴리즈

</details>