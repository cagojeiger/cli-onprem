# Tar-Fat32 명령어

`tar-fat32` 명령어는 파일 또는 디렉터리를 압축하고 지정된 크기의 조각으로 분할하여 나중에 쉽게 복원할 수 있는 기능을 제공합니다.

## 사용법

```bash
# 압축 및 분할
cli-onprem tar-fat32 pack <경로> [--chunk-size <크기>]

# 복원
cli-onprem tar-fat32 restore <경로.pack> [--purge]
# 또는
<경로.pack>/restore.sh [--purge]
```

## 서브커맨드

### pack

파일 또는 디렉터리를 압축하고 분할하여 저장합니다.

#### 옵션

- `<경로>`: 필수. 압축할 파일 또는 디렉터리 경로.
- `--chunk-size`, `-c <크기>`: 선택 사항. 조각 크기 (예: `3G`, `500M`). 기본값: `3G`.

#### 산출물 구조

```
<basename>.pack/
├─ parts/0000.part …
├─ manifest.sha256
├─ restore.sh
├─ <압축크기>_MB (빈 파일)
```

### restore

압축된 파일을 복원합니다.

#### 옵션

- `<경로.pack>`: 필수. 복원할 .pack 디렉터리 경로.
- `--purge`: 선택 사항. 성공 복원 시 .pack 폴더 삭제.

## 예제

### 기본 사용법

```bash
# 기본 압축 (3GB 조각 크기)
cli-onprem tar-fat32 pack 대용량_영상.mkv
# 출력: 대용량_영상.mkv.pack/ 디렉터리 생성

# 조각 크기 지정
cli-onprem tar-fat32 pack 데이터_폴더 -c 500M
# 출력: 데이터_폴더.pack/ 디렉터리 생성

# 복원 (중간 파일만 정리)
cli-onprem tar-fat32 restore 대용량_영상.mkv.pack
# 또는
cd 대용량_영상.mkv.pack && ./restore.sh
# 출력: 대용량_영상.mkv가 상위 디렉터리에 복원됨, .pack 디렉터리는 남아있음

# 복원 후 완전 정리
cli-onprem tar-fat32 restore 대용량_영상.mkv.pack --purge
# 또는
cd 대용량_영상.mkv.pack && ./restore.sh --purge
# 출력: 대용량_영상.mkv가 상위 디렉터리에 복원됨, .pack 디렉터리는 삭제됨
```

### 상세 예시

#### 3GB 조각으로 분할

```bash
tar-fat32 pack movie.iso -c 3G
```

분할 후 구조:

```
movie.iso.pack/
├─ parts/
│  ├─ 0000.part
│  ├─ 0001.part
│  ├─ 0002.part
│  └─ 0003.part
├─ manifest.sha256
├─ restore.sh
└─ size.txt
```

#### 복원 과정

```bash
cd movie.iso.pack
./restore.sh
```

복원 완료 후 최종 구조:

```
movie.iso.pack/
│
├─ parts/
│   └─ …
├─ manifest.sha256
├─ restore.sh
└─ size.txt

movie.iso          ← 상위 디렉터리에 원본이 생성되었음
```

## 무결성 검증

모든 조각 파일에 대해 SHA256 해시가 생성되어 `manifest.sha256` 파일에 저장됩니다. 복원 과정에서 이 해시를 사용하여 자동으로 무결성을 검증합니다.

## 오류 처리

다음과 같은 경우 명령어는 오류 코드(1)와 함께 종료됩니다:
- 지정된 입력 경로가 존재하지 않는 경우
- 출력 디렉터리가 이미 존재하는 경우
- 압축, 분할 또는 해시 생성 중 오류가 발생한 경우
- 무결성 검증에 실패한 경우 (복원 시)

## 자동완성 기능

CLI-ONPREM은 쉘 자동완성 기능을 지원합니다:

1. 쉘 자동완성 활성화:
```bash
cli-onprem --install-completion [bash|zsh|fish]
```

2. 경로 자동완성:
`pack` 및 `restore` 명령어 사용 시 Tab 키를 누르면 파일/디렉토리 목록이 자동으로 제안됩니다.
