# CHANGELOG



## v0.6.0 (2025-05-23)

### Feature

* feat(fatpack): remove cache usage in completions ([`8939397`](https://github.com/cagojeiger/cli-onprem/commit/89393979f7d40f3bb96bc26617e49619c5a2ab4b))


## v0.5.3 (2025-05-23)

### Chore

* chore: apply uv ([`b92e7ea`](https://github.com/cagojeiger/cli-onprem/commit/b92e7ea7b08ce658091a22a6dbef954d73d4d739))

* chore: apply lint ([`773819e`](https://github.com/cagojeiger/cli-onprem/commit/773819e06c318acd760450f8f1903f33b1d8d99a))

### Fix

* fix(docker-tar): remove caching from completion ([`4dbc6dd`](https://github.com/cagojeiger/cli-onprem/commit/4dbc6dd5bd17a5099a50bf669b8f4d6e002b7d6e))

### Test

* test: add cache module unit tests ([`59f82f8`](https://github.com/cagojeiger/cli-onprem/commit/59f82f813c1aee2563a9d628af640d52c4d8cd4e))


## v0.5.2 (2025-05-23)

### Fix

* fix: ensure UTF-8 encoding for cache ([`f14ba09`](https://github.com/cagojeiger/cli-onprem/commit/f14ba09e7338ce6db70cfcede646f5a1dd3987fa))

### Refactor

* refactor: 버전 업데이트 및 CI 빌드 문제 해결

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`74928bb`](https://github.com/cagojeiger/cli-onprem/commit/74928bb29da2fae80e3ff2f168bf7ac68425e99b))

* refactor: CLI 시작 속도 최적화를 위한 지연 로딩 구현

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`fce7477`](https://github.com/cagojeiger/cli-onprem/commit/fce747768614504037ee032d27e7e68482b6be2b))


## v0.5.1 (2025-05-23)

### Performance

* perf: add cache module for autocompletion performance

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`b457ec1`](https://github.com/cagojeiger/cli-onprem/commit/b457ec1183123ffb129a3c7a3c6dda6c968d091b))

### Unknown

* Update uv.lock to match main branch version

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`c8170f5`](https://github.com/cagojeiger/cli-onprem/commit/c8170f54e35cf9f4604d7e843215a18e36286f55))

* 자동완성 기능 개선: 라인 길이 수정

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`ff278f5`](https://github.com/cagojeiger/cli-onprem/commit/ff278f5b3d191375946ca5d0da95d32ccc7d00a3))


## v0.5.0 (2025-05-23)

### Documentation

* docs: update s3-share.md with auto-completion and default region information

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`a536073`](https://github.com/cagojeiger/cli-onprem/commit/a536073aec61ba0c197b9839d265036f5bec3976))

### Feature

* feat: split s3-share init command into init-credential and init-bucket

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`2eea19f`](https://github.com/cagojeiger/cli-onprem/commit/2eea19f6a549dfa1de47396af1c0526313dd2a0a))

* feat: add auto-completion for S3 bucket and prefix in s3-share init command

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`1827dfa`](https://github.com/cagojeiger/cli-onprem/commit/1827dfa26a719f157e8a7ec0dbcadc9fb199a58e))

### Refactor

* refactor: remove deprecated init command and make prefix autocomplete show folders only

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`ec5537c`](https://github.com/cagojeiger/cli-onprem/commit/ec5537c34a4e0085a4c176c8840fa13ca71710b1))


## v0.4.0 (2025-05-23)

### Build

* build(release): 버전 미생성 시 후속 릴리스 작업 방지 ([`471a01c`](https://github.com/cagojeiger/cli-onprem/commit/471a01c399e3e84cdc0abe0f0ddcc019b4ee5178))

* build: 0.3.0 버전을 위한 의존성 업데이트 ([`fba2556`](https://github.com/cagojeiger/cli-onprem/commit/fba2556b3594cc6c4149ff7b63490c2266958637))

### Chore

* chore: remove Python 3.8 support, require Python 3.9+

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`72011fa`](https://github.com/cagojeiger/cli-onprem/commit/72011fab2120bc005ff17070d27d621fb49de9b2))

* chore: update minimum python version ([`2f8372f`](https://github.com/cagojeiger/cli-onprem/commit/2f8372f4be429dbb950a9e9dcd8b38702d2575ce))

* chore(ci): remove redundant file checks ([`e7017a1`](https://github.com/cagojeiger/cli-onprem/commit/e7017a1f553f04363c4b2bf657b7c01bb03bfa8c))

### Documentation

* docs(readme): link additional docs ([`68d2519`](https://github.com/cagojeiger/cli-onprem/commit/68d2519a388910d9f5b006136566eb623c4df3bb))

* docs: 버전 관리 설정 갱신 ([`ef676a2`](https://github.com/cagojeiger/cli-onprem/commit/ef676a2b7c479bfcd9c49410d47cff46c788747a))

* docs: sync PyPI workflow with release.yml ([`35abc8b`](https://github.com/cagojeiger/cli-onprem/commit/35abc8bde2c1ae189812eb8c2556e0af1d846439))

### Feature

* feat: add s3-share sync command

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`b65e11b`](https://github.com/cagojeiger/cli-onprem/commit/b65e11b2e5891e0601b31fe9180f2b8f1e119ce8))

* feat: s3-share init 명령어 추가

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`0fa9f4d`](https://github.com/cagojeiger/cli-onprem/commit/0fa9f4d95b4561a7121db362d1bdce09964feffc))

### Fix

* fix: update test functions to use global runner variable

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`91952c4`](https://github.com/cagojeiger/cli-onprem/commit/91952c4ad8e6b30b93cceb09075eb83365206914))

* fix: correct semantic-release commit_parser and pytest fixtures

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`b53ef75`](https://github.com/cagojeiger/cli-onprem/commit/b53ef75853ae6f197c4175d82b9798b446698327))

* fix: restructure pytest fixture to avoid mypy untyped decorator error

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`d8c673a`](https://github.com/cagojeiger/cli-onprem/commit/d8c673a1574fd44b9f2d9b5d5c9261170ba7b54e))

* fix: add type stubs for tqdm and pytest-mypy-plugins

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`086e10e`](https://github.com/cagojeiger/cli-onprem/commit/086e10ecf109d5edf8b82b33effb2a9a0364e2c9))

* fix: add pydantic<2.0.0 constraint for Python 3.8 compatibility

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`345c285`](https://github.com/cagojeiger/cli-onprem/commit/345c285bbe1fb2b4c2fe3a1cfcbfdc51ceac88ae))

* fix: use alternative approach to define pytest fixture

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`f4217ca`](https://github.com/cagojeiger/cli-onprem/commit/f4217ca5a64a281e3ce3e471137585a769529e92))

* fix: use standard type ignore syntax for pytest fixture

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`f4cb685`](https://github.com/cagojeiger/cli-onprem/commit/f4cb6854828ff1c1c07579c88de4743d8d3529ff))

* fix: mypy error in test_s3_share.py with proper type ignore

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`7c291af`](https://github.com/cagojeiger/cli-onprem/commit/7c291af1f482ec2118b5d6229fb954bcef55e79c))

* fix: mypy error in test_s3_share.py

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`ada4f63`](https://github.com/cagojeiger/cli-onprem/commit/ada4f63bb480a912e99c524df0b5ee88236122b7))


## v0.3.0 (2025-05-22)

### Feature

* feat: add CLI dependency checks for helm and docker commands

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`05fd898`](https://github.com/cagojeiger/cli-onprem/commit/05fd8981e2428808db23527efaccf3074d2d8f03))


## v0.2.3 (2025-05-22)

### Fix

* fix(ci): version_toml ([`14193d2`](https://github.com/cagojeiger/cli-onprem/commit/14193d28960f10cda56c03795b7ed7f6d5556c52))


## v0.2.2 (2025-05-22)

### Fix

* fix(ci): release.yml에서 TestPyPI 업로드 step의 run 구문 스타일 통일 ([`878b006`](https://github.com/cagojeiger/cli-onprem/commit/878b006852ad4f5c65ebfa77700136c34b4f0e02))


## v0.2.1 (2025-05-22)

### Fix

* fix(ci): PyPI/TestPyPI 업로드 시 TWINE_PASSWORD 시크릿 분리 및 조건부 업로드 개선 - TestPyPI와 PyPI 업로드 단계에서 각각 다른 TWINE_PASSWORD 시크릿을 명확히 분리하여 지정 - PyPI 업로드는 릴리즈 태그에 -rc, -beta가 포함되지 않은 경우에만 실행되도록 조건 추가 - 업로드 단계별 환경 변수 관리 명확화로 보안 및 유지보수성 향상 BREAKING CHANGE: 없음 (기존 배포 플로우와 호환됨) ([`04bd2c5`](https://github.com/cagojeiger/cli-onprem/commit/04bd2c5fb64e79b02ed8e38d27b57d0a8ac80696))


## v0.2.0 (2025-05-22)

### Chore

* chore: add debug ([`834549c`](https://github.com/cagojeiger/cli-onprem/commit/834549cc8a9a8b161c0d84b5d8e897d87f16fb03))

### Ci

* ci: add semantic-release version step before publish

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`bb6fb1d`](https://github.com/cagojeiger/cli-onprem/commit/bb6fb1d445b1e1e1275ac24efc88d9ae3b4f0008))

### Documentation

* docs(readme): clarify source installation ([`4961431`](https://github.com/cagojeiger/cli-onprem/commit/4961431a58c26ee42781e844ff5c3259781694c1))

### Feature

* feat: add version_toml configuration to update version in pyproject.toml

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`03e827e`](https://github.com/cagojeiger/cli-onprem/commit/03e827e7cad2e0b8ed410c2f673a1eeb2a7f8d97))

* feat(docker_tar): validate arch choices ([`fdc7f3b`](https://github.com/cagojeiger/cli-onprem/commit/fdc7f3b593facd96be0dcf2805fadb5743bbd5d8))

* feat: semantic-release 최초 자동 릴리즈 테스트 ([`a2e48e3`](https://github.com/cagojeiger/cli-onprem/commit/a2e48e3d3a195cea2e290b2816093e9d77681e2b))

### Fix

* fix: remove hardcoded repo_dir path in semantic-release config

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`e89776b`](https://github.com/cagojeiger/cli-onprem/commit/e89776b1b27d5bf64ce981b0f4d7378907e27ace))

* fix: gh secret ([`2944279`](https://github.com/cagojeiger/cli-onprem/commit/2944279c9d6244dbee2affddd1ed92201d573b63))

### Unknown

* Revert "chore: add debug"

This reverts commit 834549cc8a9a8b161c0d84b5d8e897d87f16fb03. ([`8818469`](https://github.com/cagojeiger/cli-onprem/commit/8818469e43dfe1a331e80052cf592dd544cbf509))


## v0.1.0 (2025-05-22)

### Chore

* chore(semantic-release): changelog 설정을 최신 권장 방식으로 변경 ([`688eea4`](https://github.com/cagojeiger/cli-onprem/commit/688eea4634cf1e9ccf0e6b4b4d6da71f0db516b8))

* chore: pyproject.toml 설정 변경 사항 반영 ([`7868eac`](https://github.com/cagojeiger/cli-onprem/commit/7868eac8266adddf29166867a3ca9d0494e22a41))

* chore: rm chlog ([`b427ac9`](https://github.com/cagojeiger/cli-onprem/commit/b427ac9cdb57e13c5ecade357e6c084757a37b5b))

* chore: update uv.lock file with PyYAML dependency

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`76df412`](https://github.com/cagojeiger/cli-onprem/commit/76df412b004526a9077d95e594faeec8595fe08f))

* chore: update uv.lock file

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`e949ff2`](https://github.com/cagojeiger/cli-onprem/commit/e949ff263f525b4a30ab0d578ee0ff5142bcc9b0))

* chore: 초기 버전 태그 추가

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`f97df5a`](https://github.com/cagojeiger/cli-onprem/commit/f97df5acedf4edf14074924a679936cb3c13bae5))

* chore: 시맨틱 릴리스 브랜치 설정 구조 업데이트

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`155e1d7`](https://github.com/cagojeiger/cli-onprem/commit/155e1d74632c35f86b95052326e9ffc2169bb7be))

* chore: 시맨틱 릴리스 브랜치 설정 업데이트

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`d5beed0`](https://github.com/cagojeiger/cli-onprem/commit/d5beed0c13492e6b9b5c9ee23e21579c5d3dc23c))

* chore: 시맨틱 릴리스 설정 업데이트

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`14e4dd5`](https://github.com/cagojeiger/cli-onprem/commit/14e4dd5463312e32acd901bc6030333bd3eb475d))

* chore: 테스트를 위한 브랜치 설정 업데이트

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`6ee29da`](https://github.com/cagojeiger/cli-onprem/commit/6ee29dabe2ad8015dd6834148c5f818594363667))

* chore: Add uv.lock file and update .gitignore to include it

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`4f679bb`](https://github.com/cagojeiger/cli-onprem/commit/4f679bb41b6004462a64ef1af7d9867849f989d5))

* chore: Initial commit ([`919b200`](https://github.com/cagojeiger/cli-onprem/commit/919b2009e494a8e746cd7ec46136e0ca27e3fb34))

### Documentation

* docs: add detailed example with directory structure

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`adf4b49`](https://github.com/cagojeiger/cli-onprem/commit/adf4b49f07d2efe92efea418c0f61ba30324965a))

* docs(readme): pipx 설치 명령어 수정 및 한글 문서 제거

- README.md의 소스 설치 명령어를 pipx install -e . --force로 수정
- docs/README_KO.md 파일 삭제 ([`a09b022`](https://github.com/cagojeiger/cli-onprem/commit/a09b02222fb51af4a3651234b70fdf5edac527ad))

* docs: _ko.md 파일 제거 및 기존 문서 한국어로 변환

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`5e5bae3`](https://github.com/cagojeiger/cli-onprem/commit/5e5bae3f7ec433ab1b0d4dd6a7c0b7536adf3581))

* docs: PyPI 등록 과정 및 버전 관리 문서 추가, 영어 문서 제거

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`6702ce6`](https://github.com/cagojeiger/cli-onprem/commit/6702ce612ccfd46cfd7f6f64918e95cfcb9a8acf))

### Feature

* feat: add parameter value autocompletion

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`90917ab`](https://github.com/cagojeiger/cli-onprem/commit/90917abb83bcc5141533a5692c07220914d2d80c))

* feat: add retry logic for docker image pull timeouts

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`d8f4118`](https://github.com/cagojeiger/cli-onprem/commit/d8f4118b30b34a27b8bb685ef0b67b49a54944a1))

* feat: add helm image extraction command

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`932bbeb`](https://github.com/cagojeiger/cli-onprem/commit/932bbeb350edcc20451152032ab810c770c62be4))

* feat: add fatpack command for file compression and chunking

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`3e3c38d`](https://github.com/cagojeiger/cli-onprem/commit/3e3c38d79713408f2c325590fbc7eff8d40e04b2))

* feat: 작별 인사 명령어 추가

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`989435d`](https://github.com/cagojeiger/cli-onprem/commit/989435d7b31bfa29cbdbe4f68fe42d8f3540f9cb))

* feat: docker-tar save 명령어 구현

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`a4b77bf`](https://github.com/cagojeiger/cli-onprem/commit/a4b77bf7f49115f4df891270606b11aa8d0c775e))

* feat: 시맨틱 릴리스 및 한국어 문서화 추가

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`8ee18e2`](https://github.com/cagojeiger/cli-onprem/commit/8ee18e28337b1056f8ae58d84dc0145e39edc8a5))

* feat: Initialize CLI-ONPREM project structure

- Set up project structure with src layout
- Implement Typer-based CLI commands (greet, scan)
- Configure uv package management
- Add pre-commit hooks (ruff, black, mypy)
- Set up GitHub Actions CI pipeline
- Add comprehensive documentation

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`b39329d`](https://github.com/cagojeiger/cli-onprem/commit/b39329ded0301056b78fd3b9bbc40b2e66d26c41))

### Fix

* fix: remove unused List import in helm.py

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`e7f773c`](https://github.com/cagojeiger/cli-onprem/commit/e7f773c5c4e4a46693d8e9a72ed2f659b39d705c))

* fix: 등록되지 않은 옵션에 대한 에러 처리 추가

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`2ad1a9e`](https://github.com/cagojeiger/cli-onprem/commit/2ad1a9e45373df90d1ec6ad9e5f1b7c8957d8d1c))

* fix: add return type annotations and fix line length issues in tests

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`e3cd26b`](https://github.com/cagojeiger/cli-onprem/commit/e3cd26b58ba3d97b2b720a73481c77942f8a5e18))

* fix: fix linting issues in test_docker_tar.py

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`ec5fd58`](https://github.com/cagojeiger/cli-onprem/commit/ec5fd58fdf400cc2c3b0948fe2ab22473e6c0245))

* fix: add arch parameter to pull_image function with linux/amd64 default

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`25f467b`](https://github.com/cagojeiger/cli-onprem/commit/25f467b2603f8ce5f4c183508488574fc37740ee))

* fix: fix linting issues in test_docker_tar.py

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`5f4a54a`](https://github.com/cagojeiger/cli-onprem/commit/5f4a54a60175585441495dd7cbb889d782313917))

* fix: resolve Typer.Option configuration issue

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`87ef277`](https://github.com/cagojeiger/cli-onprem/commit/87ef277d90e0e1ace59258b7d42a48470bca39e1))

* fix: resolve mypy configuration for yaml imports

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`2c88c07`](https://github.com/cagojeiger/cli-onprem/commit/2c88c072c317c3b049d0575a125408f42e144c8a))

* fix: resolve mypy errors in helm command

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`8310df0`](https://github.com/cagojeiger/cli-onprem/commit/8310df057aab4663f46b1d82bd0760f02f405297))

* fix: resolve CI issues in helm command

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`5fcf948`](https://github.com/cagojeiger/cli-onprem/commit/5fcf9482e1f9d79666e0559c4c0233602cbf0b9f))

* fix: correct archive.tar.gz path reference in restore.sh script

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`4ef84d5`](https://github.com/cagojeiger/cli-onprem/commit/4ef84d59d6fbbb2fa84d4c30795dda68256f85d6))

* fix: resolve line length issue in restore.sh script

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`b8a7e60`](https://github.com/cagojeiger/cli-onprem/commit/b8a7e6008d8e6d1e9aed6672a75170c9f69c29aa))

* fix: restore.sh now extracts files to parent directory

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`77c038b`](https://github.com/cagojeiger/cli-onprem/commit/77c038b76c4472f6f289b8cc347a48828e87a860))

* fix: resolve linting issues and improve split command compatibility

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`044dee5`](https://github.com/cagojeiger/cli-onprem/commit/044dee558aa59604f0c34fa73a7814ba1957bd26))

* fix: 기존 디렉터리 자동 삭제 및 split 명령어 호환성 개선

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`c1f55fa`](https://github.com/cagojeiger/cli-onprem/commit/c1f55fa7636c1f5b55a80124d9c11b8aff83b3af))

* fix: resolve remaining linting issues in fatpack command

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`44c49a3`](https://github.com/cagojeiger/cli-onprem/commit/44c49a3848beccc60d3a09a8a3ffefabd237a82e))

* fix: resolve linting issues in fatpack command

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`6a51f90`](https://github.com/cagojeiger/cli-onprem/commit/6a51f907602e85855fdfc3940c92f9d3cdfff866))

* fix: 저장소 URL 설정 추가로 semantic-release 문제 해결

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`59d6865`](https://github.com/cagojeiger/cli-onprem/commit/59d686576b5101daf27cde5d2ee353c9c5bd8c05))

* fix: CI 실패 수정 및 이미지 자동 풀링 기능 추가

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`c1e0a0c`](https://github.com/cagojeiger/cli-onprem/commit/c1e0a0c92c48e202482abf8ae5bff46f2acff00b))

* fix: 의존성 추가에 따른 uv.lock 파일 업데이트

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`6aee1aa`](https://github.com/cagojeiger/cli-onprem/commit/6aee1aa9cb3efbfe713a2d8ceb3d34d9ee7e6339))

* fix: Add build package to dev dependencies for CI

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`907031f`](https://github.com/cagojeiger/cli-onprem/commit/907031f8c0737720c4898c7e5573ca6e97661927))

### Refactor

* refactor: remove unused test flags ([`c30c866`](https://github.com/cagojeiger/cli-onprem/commit/c30c866b8392ae8b063f58e11217c7983b50b694))

* refactor: remove greet and scan commands

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`3389eaa`](https://github.com/cagojeiger/cli-onprem/commit/3389eaa4585b59f75f3f77566bf71578f9dbc88b))

### Style

* style: fix ruff-check style issues

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`0e3b9c5`](https://github.com/cagojeiger/cli-onprem/commit/0e3b9c5c63f44809d4b4dbb57ba4452b4516762f))

* style: 코드 포맷팅 수정

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`3658ab5`](https://github.com/cagojeiger/cli-onprem/commit/3658ab5b2ccb19fdf093b751a5bc733af53348f2))

* style: 스캔 명령어 파일 포맷팅 수정

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`e7ac8e8`](https://github.com/cagojeiger/cli-onprem/commit/e7ac8e878f4722380d884f1658c3da7e6ec5cd69))

### Test

* test: 테스트 커버리지 80%로 향상

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`4542895`](https://github.com/cagojeiger/cli-onprem/commit/4542895a97e86e303769070126b22de64236c242))

### Unknown

* Apply ruff formatting

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`8fe2c1b`](https://github.com/cagojeiger/cli-onprem/commit/8fe2c1b7a4be68413c521a26a614524cd0697e23))

* Fix CLI command parsing issues with subcommands

Co-Authored-By: 강희용 <cagojeiger@naver.com> ([`efe485e`](https://github.com/cagojeiger/cli-onprem/commit/efe485ec465678a9168b0c3d5abffd1bda271998))

* 0.2.0 ([`035d10b`](https://github.com/cagojeiger/cli-onprem/commit/035d10ba85ee01dccbadedde6aefe0a0640a1f2b))
