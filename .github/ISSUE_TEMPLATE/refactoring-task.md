---
name: 리팩토링 작업
about: 코드 품질 개선, 아키텍처 변경, 기술 부채 해결
title: "[REFACTOR] "
labels: refactoring, technical-debt
assignees: ''
---

## 📝 작업 설명

<!-- 무엇을 리팩토링하나요? 간단히 설명해주세요 -->

## 🎯 목표

<!-- 이 리팩토링으로 무엇을 달성하고 싶나요? -->
- [ ] 보안 취약점 수정
- [ ] 안정성 개선
- [ ] 코드 가독성 향상
- [ ] 테스트 용이성 개선
- [ ] 성능 최적화
- [ ] 기타:

## 📂 영향 범위

<!-- 어떤 파일/모듈이 변경되나요? -->

**변경될 파일:**
- `src/cli_onprem/...`

**영향받는 테스트:**
- `tests/...`

## 🔍 현재 문제점

<!-- Before 코드 또는 현재 상황 설명 -->

```python
# 현재 코드 예시
```

**문제:**
-

## ✅ 제안된 해결책

<!-- After 코드 또는 개선안 설명 -->

```python
# 개선된 코드 예시
```

**개선 사항:**
-

## 📋 작업 체크리스트

### 코드 변경
- [ ] 코드 수정 완료
- [ ] 타입 힌트 추가/수정
- [ ] Docstring 작성/업데이트
- [ ] 로깅 추가 (필요 시)

### 테스트
- [ ] 기존 테스트 통과 (`pytest -q`)
- [ ] 새로운 테스트 작성 (필요 시)
- [ ] Edge case 테스트 추가
- [ ] Integration 테스트 확인

### 품질 검사
- [ ] Type checking (`mypy src --strict`)
- [ ] Linting (`SKIP=uv-lock uv run pre-commit run --all-files`)
- [ ] Code review 요청

### 문서화
- [ ] CHANGELOG.md 업데이트
- [ ] 아키텍처 문서 업데이트 (필요 시)
- [ ] 주석 추가/업데이트

## 🔗 관련 문서

<!-- 이 작업과 관련된 문서 링크 -->

- [REFACTORING.md](../../REFACTORING.md)
- [SUBPROCESS_WRAPPER.md](../../docs/architecture/SUBPROCESS_WRAPPER.md)
- [ERROR_HANDLING.md](../../docs/architecture/ERROR_HANDLING.md)
- 관련 이슈: #
- 관련 PR: #

## ⚠️ Breaking Changes

<!-- 기존 동작이 변경되나요? 사용자에게 영향이 있나요? -->

- [ ] Yes - 아래 설명 참고
- [ ] No

**변경 사항:**
<!-- Breaking change가 있다면 상세히 설명 -->

## 🧪 테스트 계획

<!-- 어떻게 테스트할 건가요? -->

### 단위 테스트
```bash
pytest tests/test_xxx.py -v
```

### 통합 테스트
```bash
pytest tests/test_xxx_integration.py -v
```

### 수동 테스트
<!-- 수동으로 확인해야 할 사항 -->
1.
2.

## 📊 성능 영향

<!-- 성능에 영향이 있나요? -->

- [ ] 성능 개선 예상
- [ ] 성능 영향 없음
- [ ] 성능 저하 가능 (아래 설명 참고)

**상세:**
<!-- 성능 변화가 있다면 설명 -->

## 💭 추가 컨텍스트

<!-- 리뷰어가 알아야 할 추가 정보 -->

---

<!--
이 템플릿은 다음 리팩토링 단계에 맞춰 작성되었습니다:
- 1단계: 보안 + 안정성 (shell injection, timeout, error handling)
- 2단계: 아키텍처 (subprocess abstraction, retry logic, health checks)
- 3단계: 코드 품질 (long functions, AWS consistency, test coverage)

해당하는 단계를 제목에 명시해주세요: [REFACTOR][P1] Shell injection 수정
-->
