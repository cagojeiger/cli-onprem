# CHANGELOG


## v0.2.0 (2025-05-23)

### Bug Fixes

- Gh secret
  ([`2944279`](https://github.com/cagojeiger/cli-onprem/commit/2944279c9d6244dbee2affddd1ed92201d573b63))

- Remove hardcoded repo_dir path in semantic-release config
  ([`e89776b`](https://github.com/cagojeiger/cli-onprem/commit/e89776b1b27d5bf64ce981b0f4d7378907e27ace))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

### Chores

- Add debug
  ([`834549c`](https://github.com/cagojeiger/cli-onprem/commit/834549cc8a9a8b161c0d84b5d8e897d87f16fb03))

### Documentation

- **readme**: Clarify source installation
  ([`4961431`](https://github.com/cagojeiger/cli-onprem/commit/4961431a58c26ee42781e844ff5c3259781694c1))

### Features

- Semantic-release 최초 자동 릴리즈 테스트
  ([`a2e48e3`](https://github.com/cagojeiger/cli-onprem/commit/a2e48e3d3a195cea2e290b2816093e9d77681e2b))

- **docker_tar**: Validate arch choices
  ([`fdc7f3b`](https://github.com/cagojeiger/cli-onprem/commit/fdc7f3b593facd96be0dcf2805fadb5743bbd5d8))


## v0.1.0 (2025-05-22)

### Bug Fixes

- Add arch parameter to pull_image function with linux/amd64 default
  ([`25f467b`](https://github.com/cagojeiger/cli-onprem/commit/25f467b2603f8ce5f4c183508488574fc37740ee))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- Add build package to dev dependencies for CI
  ([`907031f`](https://github.com/cagojeiger/cli-onprem/commit/907031f8c0737720c4898c7e5573ca6e97661927))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- Add return type annotations and fix line length issues in tests
  ([`e3cd26b`](https://github.com/cagojeiger/cli-onprem/commit/e3cd26b58ba3d97b2b720a73481c77942f8a5e18))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- Ci 실패 수정 및 이미지 자동 풀링 기능 추가
  ([`c1e0a0c`](https://github.com/cagojeiger/cli-onprem/commit/c1e0a0c92c48e202482abf8ae5bff46f2acff00b))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- Correct archive.tar.gz path reference in restore.sh script
  ([`4ef84d5`](https://github.com/cagojeiger/cli-onprem/commit/4ef84d59d6fbbb2fa84d4c30795dda68256f85d6))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- Fix linting issues in test_docker_tar.py
  ([`ec5fd58`](https://github.com/cagojeiger/cli-onprem/commit/ec5fd58fdf400cc2c3b0948fe2ab22473e6c0245))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- Fix linting issues in test_docker_tar.py
  ([`5f4a54a`](https://github.com/cagojeiger/cli-onprem/commit/5f4a54a60175585441495dd7cbb889d782313917))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- Remove unused List import in helm.py
  ([`e7f773c`](https://github.com/cagojeiger/cli-onprem/commit/e7f773c5c4e4a46693d8e9a72ed2f659b39d705c))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- Resolve CI issues in helm command
  ([`5fcf948`](https://github.com/cagojeiger/cli-onprem/commit/5fcf9482e1f9d79666e0559c4c0233602cbf0b9f))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- Resolve line length issue in restore.sh script
  ([`b8a7e60`](https://github.com/cagojeiger/cli-onprem/commit/b8a7e6008d8e6d1e9aed6672a75170c9f69c29aa))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- Resolve linting issues and improve split command compatibility
  ([`044dee5`](https://github.com/cagojeiger/cli-onprem/commit/044dee558aa59604f0c34fa73a7814ba1957bd26))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- Resolve linting issues in fatpack command
  ([`6a51f90`](https://github.com/cagojeiger/cli-onprem/commit/6a51f907602e85855fdfc3940c92f9d3cdfff866))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- Resolve mypy configuration for yaml imports
  ([`2c88c07`](https://github.com/cagojeiger/cli-onprem/commit/2c88c072c317c3b049d0575a125408f42e144c8a))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- Resolve mypy errors in helm command
  ([`8310df0`](https://github.com/cagojeiger/cli-onprem/commit/8310df057aab4663f46b1d82bd0760f02f405297))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- Resolve remaining linting issues in fatpack command
  ([`44c49a3`](https://github.com/cagojeiger/cli-onprem/commit/44c49a3848beccc60d3a09a8a3ffefabd237a82e))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- Resolve Typer.Option configuration issue
  ([`87ef277`](https://github.com/cagojeiger/cli-onprem/commit/87ef277d90e0e1ace59258b7d42a48470bca39e1))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- Restore.sh now extracts files to parent directory
  ([`77c038b`](https://github.com/cagojeiger/cli-onprem/commit/77c038b76c4472f6f289b8cc347a48828e87a860))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- 기존 디렉터리 자동 삭제 및 split 명령어 호환성 개선
  ([`c1f55fa`](https://github.com/cagojeiger/cli-onprem/commit/c1f55fa7636c1f5b55a80124d9c11b8aff83b3af))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- 등록되지 않은 옵션에 대한 에러 처리 추가
  ([`2ad1a9e`](https://github.com/cagojeiger/cli-onprem/commit/2ad1a9e45373df90d1ec6ad9e5f1b7c8957d8d1c))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- 의존성 추가에 따른 uv.lock 파일 업데이트
  ([`6aee1aa`](https://github.com/cagojeiger/cli-onprem/commit/6aee1aa9cb3efbfe713a2d8ceb3d34d9ee7e6339))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- 저장소 URL 설정 추가로 semantic-release 문제 해결
  ([`59d6865`](https://github.com/cagojeiger/cli-onprem/commit/59d686576b5101daf27cde5d2ee353c9c5bd8c05))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

### Chores

- Add uv.lock file and update .gitignore to include it
  ([`4f679bb`](https://github.com/cagojeiger/cli-onprem/commit/4f679bb41b6004462a64ef1af7d9867849f989d5))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- Initial commit
  ([`919b200`](https://github.com/cagojeiger/cli-onprem/commit/919b2009e494a8e746cd7ec46136e0ca27e3fb34))

- Pyproject.toml 설정 변경 사항 반영
  ([`7868eac`](https://github.com/cagojeiger/cli-onprem/commit/7868eac8266adddf29166867a3ca9d0494e22a41))

- Rm chlog
  ([`b427ac9`](https://github.com/cagojeiger/cli-onprem/commit/b427ac9cdb57e13c5ecade357e6c084757a37b5b))

- Update uv.lock file
  ([`e949ff2`](https://github.com/cagojeiger/cli-onprem/commit/e949ff263f525b4a30ab0d578ee0ff5142bcc9b0))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- Update uv.lock file with PyYAML dependency
  ([`76df412`](https://github.com/cagojeiger/cli-onprem/commit/76df412b004526a9077d95e594faeec8595fe08f))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- 시맨틱 릴리스 브랜치 설정 구조 업데이트
  ([`155e1d7`](https://github.com/cagojeiger/cli-onprem/commit/155e1d74632c35f86b95052326e9ffc2169bb7be))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- 시맨틱 릴리스 브랜치 설정 업데이트
  ([`d5beed0`](https://github.com/cagojeiger/cli-onprem/commit/d5beed0c13492e6b9b5c9ee23e21579c5d3dc23c))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- 시맨틱 릴리스 설정 업데이트
  ([`14e4dd5`](https://github.com/cagojeiger/cli-onprem/commit/14e4dd5463312e32acd901bc6030333bd3eb475d))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- 초기 버전 태그 추가
  ([`f97df5a`](https://github.com/cagojeiger/cli-onprem/commit/f97df5acedf4edf14074924a679936cb3c13bae5))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- 테스트를 위한 브랜치 설정 업데이트
  ([`6ee29da`](https://github.com/cagojeiger/cli-onprem/commit/6ee29dabe2ad8015dd6834148c5f818594363667))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- **semantic-release**: Changelog 설정을 최신 권장 방식으로 변경
  ([`688eea4`](https://github.com/cagojeiger/cli-onprem/commit/688eea4634cf1e9ccf0e6b4b4d6da71f0db516b8))

### Code Style

- Fix ruff-check style issues
  ([`0e3b9c5`](https://github.com/cagojeiger/cli-onprem/commit/0e3b9c5c63f44809d4b4dbb57ba4452b4516762f))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- 스캔 명령어 파일 포맷팅 수정
  ([`e7ac8e8`](https://github.com/cagojeiger/cli-onprem/commit/e7ac8e878f4722380d884f1658c3da7e6ec5cd69))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- 코드 포맷팅 수정
  ([`3658ab5`](https://github.com/cagojeiger/cli-onprem/commit/3658ab5b2ccb19fdf093b751a5bc733af53348f2))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

### Documentation

- _ko.md 파일 제거 및 기존 문서 한국어로 변환
  ([`5e5bae3`](https://github.com/cagojeiger/cli-onprem/commit/5e5bae3f7ec433ab1b0d4dd6a7c0b7536adf3581))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- Add detailed example with directory structure
  ([`adf4b49`](https://github.com/cagojeiger/cli-onprem/commit/adf4b49f07d2efe92efea418c0f61ba30324965a))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- Pypi 등록 과정 및 버전 관리 문서 추가, 영어 문서 제거
  ([`6702ce6`](https://github.com/cagojeiger/cli-onprem/commit/6702ce612ccfd46cfd7f6f64918e95cfcb9a8acf))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- **readme**: Pipx 설치 명령어 수정 및 한글 문서 제거
  ([`a09b022`](https://github.com/cagojeiger/cli-onprem/commit/a09b02222fb51af4a3651234b70fdf5edac527ad))

- README.md의 소스 설치 명령어를 pipx install -e . --force로 수정 - docs/README_KO.md 파일 삭제

### Features

- Add fatpack command for file compression and chunking
  ([`3e3c38d`](https://github.com/cagojeiger/cli-onprem/commit/3e3c38d79713408f2c325590fbc7eff8d40e04b2))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- Add helm image extraction command
  ([`932bbeb`](https://github.com/cagojeiger/cli-onprem/commit/932bbeb350edcc20451152032ab810c770c62be4))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- Add parameter value autocompletion
  ([`90917ab`](https://github.com/cagojeiger/cli-onprem/commit/90917abb83bcc5141533a5692c07220914d2d80c))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- Add retry logic for docker image pull timeouts
  ([`d8f4118`](https://github.com/cagojeiger/cli-onprem/commit/d8f4118b30b34a27b8bb685ef0b67b49a54944a1))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- Docker-tar save 명령어 구현
  ([`a4b77bf`](https://github.com/cagojeiger/cli-onprem/commit/a4b77bf7f49115f4df891270606b11aa8d0c775e))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- Initialize CLI-ONPREM project structure
  ([`b39329d`](https://github.com/cagojeiger/cli-onprem/commit/b39329ded0301056b78fd3b9bbc40b2e66d26c41))

- Set up project structure with src layout - Implement Typer-based CLI commands (greet, scan) -
  Configure uv package management - Add pre-commit hooks (ruff, black, mypy) - Set up GitHub Actions
  CI pipeline - Add comprehensive documentation

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- 시맨틱 릴리스 및 한국어 문서화 추가
  ([`8ee18e2`](https://github.com/cagojeiger/cli-onprem/commit/8ee18e28337b1056f8ae58d84dc0145e39edc8a5))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- 작별 인사 명령어 추가
  ([`989435d`](https://github.com/cagojeiger/cli-onprem/commit/989435d7b31bfa29cbdbe4f68fe42d8f3540f9cb))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

### Refactoring

- Remove greet and scan commands
  ([`3389eaa`](https://github.com/cagojeiger/cli-onprem/commit/3389eaa4585b59f75f3f77566bf71578f9dbc88b))

Co-Authored-By: 강희용 <cagojeiger@naver.com>

- Remove unused test flags
  ([`c30c866`](https://github.com/cagojeiger/cli-onprem/commit/c30c866b8392ae8b063f58e11217c7983b50b694))

### Testing

- 테스트 커버리지 80%로 향상
  ([`4542895`](https://github.com/cagojeiger/cli-onprem/commit/4542895a97e86e303769070126b22de64236c242))

Co-Authored-By: 강희용 <cagojeiger@naver.com>
