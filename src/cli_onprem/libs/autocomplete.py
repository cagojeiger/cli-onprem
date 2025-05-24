"""Autocompletion utilities."""

from typing import Callable, List


def filter_completions(
    fetch_func: Callable[[], List[str]], 
    incomplete: str
) -> List[str]:
    """Common pattern for autocompletion filtering.
    
    Args:
        fetch_func: Function that fetches all possible completions
        incomplete: Partial string to match against
        
    Returns:
        List of matching completions
    """
    try:
        matches = fetch_func()
        return [m for m in matches if m.startswith(incomplete)]
    except Exception:
        # Return empty list on any error to prevent breaking autocompletion
        return []