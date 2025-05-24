"""공통 타입 정의."""

from typing import Any, Dict, List, Set

# Type aliases
ImageSet = Set[str]
ImageList = List[str]
YamlDict = Dict[str, Any]

# CLI Context settings
CONTEXT_SETTINGS = {
    "ignore_unknown_options": True,
    "allow_extra_args": True,
}
