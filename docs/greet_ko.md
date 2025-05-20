# 인사 명령어

`greet` 명령어는 인사 메시지를 출력하는 간단한 방법을 제공합니다.

## 사용법

```bash
cli-onprem greet hello [이름]
```

## 옵션

- `이름`: 선택 사항. 인사할 사람의 이름. 제공하지 않으면 기본값은 "world"입니다.

## 예제

```bash
# 기본 메시지로 인사
cli-onprem greet hello
# 출력: Hello, world!

# 특정 사람에게 인사
cli-onprem greet hello Alice
# 출력: Hello, Alice!
```

## 목적

이 명령어는 다음을 빠르게 검증하기 위한 MVP 스켈레톤 검증 도구로 사용됩니다:
- Typer 데코레이터 기능
- 자동 도움말 생성
- Rich를 통한 ANSI 색상 출력
- 완전한 pre-commit → mypy → pytest → CI 파이프라인
