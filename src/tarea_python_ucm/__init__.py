"""
Analysis of Madrid traffic fines.

Modules:
    cache: disk cache (Cache, CacheURL, CacheError).
    madridFines: download, cleaning and analysis of fines (pending).
"""

from .cache import Cache, CacheURL, CacheError

__all__ = ["Cache", "CacheURL", "CacheError"]


def main() -> None:
    """
    Entry point of the tarea-python-ucm command.
    """
    print("tarea_python_ucm: Madrid traffic fines package.")