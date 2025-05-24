# Docker Tar 명령어

`docker-tar` 명령어는 Docker 이미지를 표준화된 이름의 tar 파일로 저장하는 기능을 제공합니다.

## 사용법

```bash
cli-onprem docker-tar save <reference> [OPTIONS]
```

## 옵션

- `<reference>`: 필수. 컨테이너 이미지 레퍼런스 (형식: `[<registry>/][<namespace>/]<image>[:<tag>]`).
- `--arch <os/arch>`: 선택 사항. 추출 플랫폼 지정. 허용 값은 `linux/amd64` 또는 `linux/arm64`이며 기본값은 `linux/amd64`.
- `--output`, `-o <dir|file>`: 선택 사항. 저장 위치(디렉터리 또는 완전한 경로). 기본값: 현재 작업 디렉터리.
- `--stdout`: 선택 사항. tar 스트림을 표준 출력으로 내보냄 (파이프용).
- `--force`, `-f`: 선택 사항. 동일 이름 파일 덮어쓰기. 기본값: False.
- `--quiet`, `-q`: 선택 사항. 에러만 출력. 기본값: False.
- `--dry-run`: 선택 사항. 실제 저장하지 않고 파일명만 출력. 기본값: False.
- `--verbose`, `-v`: 선택 사항. DEBUG 로그 출력. 기본값: False.

## 왜 --arch 옵션을 사용하나

Docker 태그는 하나의 digest만 가리키므로 동일한 태그를 서로 다른 아키텍처로
`docker pull`하면 태그가 마지막에 받은 아키텍처로 덮어써집니다. 예를 들어
`linux/amd64` 이미지를 받은 뒤 같은 태그를 `linux/arm64`로 다시 받으면 태그가
arm64 digest로 갱신되어 이후 해당 태그를 실행할 때 잘못된 바이너리가 실행될 수
있습니다. 또한 이전 아키텍처의 레이어가 dangling 상태로 남을 수 있습니다.

`docker-tar`은 이러한 문제를 피하기 위해 항상 `docker pull --platform`을 호출해
특정 아키텍처 이미지를 직접 가져옵니다. 이 동작은 잘못된 바이너리 실행을
방지하고 불필요한 dangling 레이어가 생기는 것을 막아 줍니다.

## 파일명 형식

저장된 파일은 다음 형식의 이름을 가집니다:
```
[reg__][ns__]image__tag__arch.tar
```

- 필드 사이의 구분자는 `__`(더블 언더스코어)로 고정됩니다.
- 필드 내부의 `/`는 `_`로 치환됩니다.
- 레지스트리가 `docker.io`인 경우 파일명에서 생략됩니다.
- 네임스페이스가 `library`인 경우 파일명에서 생략됩니다.

## 예제

```bash
# 기본 저장
cli-onprem docker-tar save nginx:1.25.4
# 출력: ./nginx__1.25.4__amd64.tar 생성

# 플랫폼 지정 저장
cli-onprem docker-tar save ghcr.io/bitnami/redis:7.2.4 --arch linux/arm64
# 출력: ./ghcr.io__bitnami__redis__7.2.4__arm64.tar 생성

# 절대 경로 지정
cli-onprem docker-tar save alpine:3.20 --output /var/backup
# 출력: /var/backup/alpine__3.20__amd64.tar 생성

# 파이프-압축
cli-onprem docker-tar save nginx:1.25.4 --stdout | gzip > /abs/path/nginx__1.25.4__amd64.tar.gz
# 출력: /abs/path/nginx__1.25.4__amd64.tar.gz 생성, 중간 파일 없음

# 드라이 런
cli-onprem docker-tar save redis:7.2 --dry-run
# 출력: redis__7.2__amd64.tar 예정 메시지만 출력
```

## 오류 처리

다음과 같은 경우 명령어는 오류 코드(1)와 함께 종료됩니다:
- Docker 명령어 실행 중 오류가 발생한 경우
- 이미지 레퍼런스가 유효하지 않은 경우

## 자동완성 기능

CLI-ONPREM은 쉘 자동완성 기능을 지원합니다:

1. 쉘 자동완성 활성화:
```bash
cli-onprem --install-completion [bash|zsh|fish]
```

2. 이미지 레퍼런스 자동완성:
`save` 명령어 사용 시 Tab 키를 누르면 로컬 Docker에 있는 이미지 목록이 자동으로 제안됩니다.
