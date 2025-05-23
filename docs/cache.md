# 캐시 모듈

CLI-ONPREM의 자동완성 성능을 개선하기 위한 캐시 모듈입니다.

## 개요

CLI-ONPREM은 자동완성 기능을 제공하기 위해 S3 버킷 목록, Docker 이미지 목록 등을 조회합니다. 이 과정에서 네트워크 요청이나 외부 프로세스 실행이 필요하여 지연이 발생할 수 있습니다.

캐시 모듈은 이러한 데이터를 로컬 파일 시스템에 캐싱하고, TTL(Time-To-Live) 기반으로 관리하여 자동완성 성능을 개선합니다.

## 주요 기능

- 파일 기반 캐싱: `~/.cache/cli-onprem/` 디렉토리에 JSON 형식으로 데이터 저장
- TTL 기반 캐시 관리: 설정된 시간 동안만 캐시 유효
- 백그라운드 갱신: 만료된 캐시는 백그라운드 스레드에서 비동기적으로 갱신

## 사용 방법

```python
from cli_onprem.libs.cache import get_cached_data

def complete_bucket(incomplete: str) -> List[str]:
    """S3 버킷 자동완성: 접근 가능한 버킷 제안"""
    def fetch_buckets() -> List[str]:
        # 실제 데이터를 가져오는 함수
        # ...
        return buckets
    
    # 캐시에서 버킷 목록 가져오기 (TTL: 10분)
    buckets = get_cached_data("s3_buckets", fetch_buckets, ttl=600)
    return [b for b in buckets if b.startswith(incomplete)]
```

## 캐시 파일 구조

캐시 파일은 다음과 같은 JSON 구조로 저장됩니다:

모든 캐시 파일은 **UTF-8 인코딩**으로 저장됩니다.

```json
{
  "timestamp": 1621234567,  // 마지막 갱신 시간 (Unix 타임스탬프)
  "data": [...],            // 실제 데이터
  "ttl": 600                // 유효 시간(초)
}
```

## API 참조

### `get_cached_data(cache_name, fetch_func, ttl=600)`

캐시에서 데이터를 가져오거나, 필요시 백그라운드에서 갱신합니다.

- `cache_name`: 캐시 파일 이름
- `fetch_func`: 캐시가 없거나 만료된 경우 데이터를 가져오는 함수
- `ttl`: 캐시 유효 시간(초), 기본값 10분

### `update_cache_in_background(cache_name, fetch_func, ttl=600)`

백그라운드 스레드에서 캐시를 갱신합니다.

- `cache_name`: 캐시 파일 이름
- `fetch_func`: 데이터를 가져오는 함수
- `ttl`: 캐시 유효 시간(초), 기본값 10분

## 성능 개선 효과

- 첫 실행 시: 기존과 동일한 성능 (캐시 생성)
- 두 번째 실행부터: 캐시에서 즉시 데이터 로드로 지연 없음
- 캐시 만료 시: 백그라운드에서 갱신하므로 사용자 경험에 영향 없음
