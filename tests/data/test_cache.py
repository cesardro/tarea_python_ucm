from pathlib import Path
import shutil
import pytest
from tarea_python_ucm import cache, Cache, CacheError

DATA_DIR = Path(__file__).parent / "data"

@pytest.fixture
def cache_dir(monkeypatch):
    folder = DATA_DIR / "cache"
    monkeypatch.setattr(cache, "CACHE_DIR", folder)
    yield folder
    shutil.rmtree(folder, ignore_errors=True)