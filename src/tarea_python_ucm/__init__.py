"""
Analysis of Madrid traffic fines.

Modules:
    cache: disk cache (Cache, CacheURL, CacheError).
    madridFines: download, cleaning and analysis of fines (get_url, MadridFines, MadridError).
"""

from .cache import Cache, CacheURL, CacheError
from .madridFines import MadridFines, MadridError, get_url

__all__ = ["Cache", "CacheURL", "CacheError", "MadridFines", "MadridError", "get_url"]


def main() -> None:
    """
    Entry point of the tarea-python-ucm command.
    """
    print("tarea_python_ucm: Madrid traffic fines package.")