# Helm 명령어

Helm 차트에서 Docker 이미지 참조를 추출하는 명령어입니다.

## 목적

Helm 차트(.tgz 아카이브 또는 디렉토리)에서 사용되는 모든 Docker 이미지 참조(저장소 + 태그 또는 다이제스트)를 추출합니다. 이 기능은 컨테이너 이미지 관리, 보안 스캔, 의존성 분석 등에 유용합니다.

## 사용법

```bash
# 기본 사용법
cli-onprem helm extract-images <차트_경로>

# 추가 values 파일 지정
cli-onprem helm extract-images <차트_경로> -f values-prod.yaml -f secrets.yaml

# JSON 형식으로 출력
cli-onprem helm extract-images <차트_경로> --json

# 로그 메시지 숨기기
cli-onprem helm extract-images <차트_경로> --quiet
```

## 옵션

| 옵션 | 설명 |
|------|------|
| `<차트_경로>` | Helm 차트 아카이브(.tgz) 또는 디렉토리 경로 (필수) |
| `-f, --values <파일>` | 추가 values.yaml 파일 경로 (여러 번 사용 가능) |
| `-q, --quiet` | 로그 메시지 출력 안함 (stderr) |
| `--json` | JSON 배열 형식으로 출력 |
| `--raw` | 이미지 이름 표준화 없이 원본 그대로 출력 |

## 예제

### 압축된 차트에서 이미지 추출

```bash
cli-onprem helm extract-images nginx-13.2.0.tgz
```

출력:
```
docker.io/library/nginx:1.25.4
```

### 추가 values 파일 사용

```bash
cli-onprem helm extract-images wordpress-15.2.35.tgz -f prod-values.yaml -f secrets.yaml
```

출력:
```
docker.io/bitnami/wordpress:6.2.1
docker.io/bitnami/mariadb:10.11.2
```

### JSON 형식으로 출력

```bash
cli-onprem helm extract-images prometheus-22.6.1.tgz --json
```

출력:
```json
["docker.io/prom/prometheus:v2.45.0", "docker.io/jimmidyson/configmap-reload:v0.8.0"]
```

### docker-tar save 명령어와 함께 사용

추출한 이미지를 `docker-tar save` 명령어로 저장하려면 파이프라인과 `xargs`를 사용할 수 있습니다:

```bash
# 모든 이미지를 추출하여 tar 파일로 저장
cli-onprem helm extract-images nginx-13.2.0.tgz | xargs -n1 cli-onprem docker-tar save -o /path/to/images/

# 특정 values 파일을 적용하여 이미지 추출 후 저장
cli-onprem helm extract-images wordpress-15.2.35.tgz -f prod-values.yaml | xargs -n1 cli-onprem docker-tar save -o /path/to/images/
```

이 방식으로 Helm 차트에서 사용되는 모든 이미지를 자동으로 추출하여 tar 파일로 저장할 수 있습니다.

## 작동 방식

1. 차트 아카이브를 임시 디렉토리에 추출하거나 차트 디렉토리를 직접 사용
2. `helm dependency update` 명령으로 차트 의존성 업데이트
3. `helm template` 명령으로 차트를 렌더링하여 Kubernetes 매니페스트 생성
4. 렌더링된 매니페스트에서 이미지 참조 추출
5. 이미지 이름 표준화 및 중복 제거
6. 정렬된 이미지 목록 출력

## 자동완성 기능

CLI-ONPREM은 쉘 자동완성 기능을 지원합니다:

1. 쉘 자동완성 활성화:
```bash
cli-onprem --install-completion [bash|zsh|fish]
```

2. 차트 경로 자동완성:
`extract-images` 명령어 사용 시 Tab 키를 누르면 현재 디렉토리의 `.tgz` 파일과 디렉토리 목록이 자동으로 제안됩니다.
