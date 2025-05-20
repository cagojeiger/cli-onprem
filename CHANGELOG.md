# CHANGELOG


## v0.2.0 (2025-05-20)

### Bug Fixes

- Ci 실패 수정 및 이미지 자동 풀링 기능 추가
  ([`176d3be`](https://github.com/cagojeiger/cli-onprem/commit/176d3bef3bb6c0d60e5d015f0c4889e636e3c184))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

### Chores

- 초기 버전 태그 추가
  ([`9af7204`](https://github.com/cagojeiger/cli-onprem/commit/9af720457deb788bc6ef7f1a301e1c73b405f6b4))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

### Code Style

- 코드 포맷팅 수정
  ([`0909f6e`](https://github.com/cagojeiger/cli-onprem/commit/0909f6e6a721f0bfd1f8390a6ab66abc28b4f99c))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

### Documentation

- **readme**: Pipx 설치 명령어 수정 및 한글 문서 제거
  ([`da1e762`](https://github.com/cagojeiger/cli-onprem/commit/da1e7624341f1bb3386b05f893d42c942b638fbd))

- README.md의 소스 설치 명령어를 pipx install -e . --force로 수정 - docs/README_KO.md 파일 삭제

### Features

- Docker-tar save 명령어 구현
  ([`3d167c3`](https://github.com/cagojeiger/cli-onprem/commit/3d167c3364d13cabb97223e11a2f4de41ebc933c))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- 작별 인사 명령어 추가
  ([`b1ab1f3`](https://github.com/cagojeiger/cli-onprem/commit/b1ab1f351ce0403d80d4aeac0250beb9cc519dd9))

Co-Authored-By: 강희용 <cagojeiger@naver.com>


## v0.1.0 (2025-05-20)

### Bug Fixes

- Add build package to dev dependencies for CI
  ([`1b762c6`](https://github.com/cagojeiger/cli-onprem/commit/1b762c684fab8dad77a20140e61f73cb277140c7))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- 의존성 추가에 따른 uv.lock 파일 업데이트
  ([`ae97b6a`](https://github.com/cagojeiger/cli-onprem/commit/ae97b6a5e5bfff144933aab965815aba2b3043cc))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

### Chores

- Add uv.lock file and update .gitignore to include it
  ([`462f7f7`](https://github.com/cagojeiger/cli-onprem/commit/462f7f7e685fc1738e159a704c4fb1991838089c))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- 시맨틱 릴리스 브랜치 설정 구조 업데이트
  ([`a5f608d`](https://github.com/cagojeiger/cli-onprem/commit/a5f608d6d4e14e5e74facfbd82bc4f722660bb9c))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- 시맨틱 릴리스 브랜치 설정 업데이트
  ([`9e82793`](https://github.com/cagojeiger/cli-onprem/commit/9e8279396cf25f3f596225a6dd829dc84ca32e36))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- 시맨틱 릴리스 설정 업데이트
  ([`15d5f32`](https://github.com/cagojeiger/cli-onprem/commit/15d5f32956501da1b1b345134c9260d9b6c7bddf))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- 테스트를 위한 브랜치 설정 업데이트
  ([`b712a52`](https://github.com/cagojeiger/cli-onprem/commit/b712a52d8dbb873f7cf030960d2284d803b89e9c))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

### Code Style

- 스캔 명령어 파일 포맷팅 수정
  ([`221ae43`](https://github.com/cagojeiger/cli-onprem/commit/221ae438e022d651a0d880d0a11b89deba34ddad))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

### Documentation

- _ko.md 파일 제거 및 기존 문서 한국어로 변환
  ([`a0e46b9`](https://github.com/cagojeiger/cli-onprem/commit/a0e46b9584aedd6828ea31da52218702005fce99))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- Pypi 등록 과정 및 버전 관리 문서 추가, 영어 문서 제거
  ([`e8bd4b2`](https://github.com/cagojeiger/cli-onprem/commit/e8bd4b28cf41c0e4cea8c5040ad1175970592612))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

### Features

- Initialize CLI-ONPREM project structure
  ([`cc8b56e`](https://github.com/cagojeiger/cli-onprem/commit/cc8b56e7010b89edc9d8c123dfcbbeb71caccef9))

- Set up project structure with src layout - Implement Typer-based CLI commands (greet, scan) -
  Configure uv package management - Add pre-commit hooks (ruff, black, mypy) - Set up GitHub Actions
  CI pipeline - Add comprehensive documentation

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- 시맨틱 릴리스 및 한국어 문서화 추가
  ([`41e35b3`](https://github.com/cagojeiger/cli-onprem/commit/41e35b37363daad9ddc5f2618837dba24dec2d8a))

Co-Authored-By: 강희용 <cagojeiger@naver.com>
