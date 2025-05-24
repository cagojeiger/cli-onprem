"""출력 포맷팅 유틸리티."""

import json
from typing import Any, List


def format_json(data: Any, indent: int = 2) -> str:
    """데이터를 JSON 형식으로 포맷팅합니다.

    Args:
        data: 포맷팅할 데이터
        indent: 들여쓰기 수준

    Returns:
        JSON 문자열
    """
    return json.dumps(data, indent=indent, ensure_ascii=False)


def format_list(items: List[str], separator: str = "\n") -> str:
    """리스트를 문자열로 포맷팅합니다.

    Args:
        items: 항목 리스트
        separator: 구분자

    Returns:
        포맷팅된 문자열
    """
    return separator.join(items)
