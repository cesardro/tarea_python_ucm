from pathlib import Path
import pytest
import requests
import tarea_python_ucm.cache as cache
from tarea_python_ucm import Cache, CacheURL, CacheError

FIXTURE_DIR = Path(__file__).parent.resolve() / 'data'


@pytest.fixture
def cache_test(monkeypatch):
    """Empty Cache 'test_app' stored in tests/data/cache instead of the real home folder."""
    monkeypatch.setattr(cache, "CACHE_DIR", FIXTURE_DIR / "cache")
    c = Cache("test_app", 1)
    c.clear()
    return c


@pytest.mark.parametrize("app_name, obsolescence",
                         [("", 1), (123, 1), ("x", 0), ("x", -1), ("x", True), ("x", "7")])
def test_init_invalid(monkeypatch, app_name, obsolescence):
    """Wrong app_name or obsolescence raises CacheError."""
    monkeypatch.setattr(cache, "CACHE_DIR", FIXTURE_DIR / "cache")
    with pytest.raises(CacheError):
        Cache(app_name, obsolescence)


def test_properties(cache_test):
    """Properties return the values given in __init__."""
    assert cache_test.app_name == "test_app"
    assert cache_test.obsolescence == 1
    assert cache_test.cache_dir == str(FIXTURE_DIR / "cache" / "test_app")


def test_repr_and_str(cache_test):
    """repr recreates the object and str shows the app name."""
    assert repr(cache_test) == "Cache('test_app', 1)"
    assert "test_app" in str(cache_test)


def test_set_and_load(cache_test):
    """Saved data is loaded back unchanged."""
    cache_test.set("a", "hola")
    assert cache_test.load("a") == "hola"


def test_set_overwrites(cache_test):
    """Saving twice with the same name keeps the last data."""
    cache_test.set("a", "hola")
    cache_test.set("a", "adios")
    assert cache_test.load("a") == "adios"


@pytest.mark.parametrize("name, data",
                         [("", "hola"), ("   ", "hola"), (123, "hola"), ("a", ""), ("a", 123)])
def test_set_invalid(cache_test, name, data):
    """Empty or non-string name or data raises CacheError."""
    with pytest.raises(CacheError):
        cache_test.set(name, data)


def test_exists(cache_test):
    """exists is True only for saved names."""
    cache_test.set("a", "hola")
    assert cache_test.exists("a")
    assert not cache_test.exists("b")


def test_missing_name(cache_test):
    """load and how_old raise CacheError for a name not in cache."""
    with pytest.raises(CacheError):
        cache_test.load("nope")
    with pytest.raises(CacheError):
        cache_test.how_old("nope")


def test_new_file_not_obsolete(cache_test):
    """A file just saved has a non negative age and is not obsolete."""
    cache_test.set("a", "hola")
    assert cache_test.how_old("a") >= 0
    assert not cache_test.is_obsolete("a")


def test_is_obsolete(monkeypatch, cache_test):
    """With the clock moved 2 days ahead, a 1 day cache is obsolete."""
    cache_test.set("a", "hola")
    real_now = cache.time.time()

    class MockTime:
        @staticmethod
        def time():
            return real_now + 2 * 24 * 60 * 60

    monkeypatch.setattr(cache, "time", MockTime)
    assert cache_test.is_obsolete("a")


def test_delete(cache_test):
    """delete removes the file and does not fail if it does not exist."""
    cache_test.set("a", "hola")
    cache_test.delete("a")
    assert not cache_test.exists("a")
    cache_test.delete("nope")


def test_clear(cache_test):
    """clear removes every file of the application."""
    cache_test.set("a", "hola")
    cache_test.set("b", "adios")
    cache_test.clear()
    assert not cache_test.exists("a")
    assert not cache_test.exists("b")



# ================================ CacheURL ================================
URL = "https://datos.madrid.es/test.csv"


class MockResponse:
    """Fake requests response, as in test_traductor_html.py (status_code can be changed)."""

    def __init__(self, text, status_code=200):
        self.status_code = status_code
        self.text = text


@pytest.fixture
def cacheurl_test(monkeypatch):
    """Empty CacheURL 'test_url' stored in tests/data/cache."""
    monkeypatch.setattr(cache, "CACHE_DIR", FIXTURE_DIR / "cache")
    c = CacheURL("test_url", 1)
    c.clear()
    return c


@pytest.fixture
def calls(monkeypatch):
    """Replaces requests.get with a fake that answers 'hi, i am a test' and records every URL asked for."""
    asked = []

    def mock_get(url, **kwargs):
        asked.append(url)
        return MockResponse("hi, i am a test")

    monkeypatch.setattr(cache.requests, "get", mock_get)
    return asked


def test_hash_me(cacheurl_test):
    """The hash has 32 characters, is always the same for the same input and depends on the url and kwargs."""
    h = cacheurl_test._hash_me(URL)
    assert len(h) == 32
    assert h == cacheurl_test._hash_me(URL)
    assert h != cacheurl_test._hash_me(URL + "?x=1")
    assert h != cacheurl_test._hash_me(URL, timeout=5)
    assert cacheurl_test._hash_me(URL, a=1, b=2) == cacheurl_test._hash_me(URL, b=2, a=1)


@pytest.mark.parametrize("url", ["", "   ", None, 123])
def test_hash_me_invalid(cacheurl_test, url):
    """Empty or non-string url raises CacheError."""
    with pytest.raises(CacheError):
        cacheurl_test._hash_me(url)


def test_get_downloads_and_saves(cacheurl_test, calls):
    """First get downloads the url and saves it under its hash."""
    assert cacheurl_test.get(URL) == "hi, i am a test"
    assert calls == [URL]
    assert cacheurl_test.exists(URL)
    assert cacheurl_test.load(URL) == "hi, i am a test"
    assert (Path(cacheurl_test.cache_dir) / cacheurl_test._hash_me(URL)).is_file()


def test_get_uses_cache(cacheurl_test, calls):
    """Second get reads from disk: requests.get is called only once."""
    cacheurl_test.get(URL)
    assert cacheurl_test.get(URL) == "hi, i am a test"
    assert len(calls) == 1


def test_get_obsolete_downloads_again(monkeypatch, cacheurl_test, calls):
    """If the stored file is obsolete, get downloads it again."""
    cacheurl_test.get(URL)
    real_now = cache.time.time()

    class MockTime:
        @staticmethod
        def time():
            return real_now + 2 * 24 * 60 * 60

    monkeypatch.setattr(cache, "time", MockTime)
    assert cacheurl_test.is_obsolete(URL)
    cacheurl_test.get(URL)
    assert len(calls) == 2


def test_get_status_error(monkeypatch, cacheurl_test):
    """A status code other than 200 raises CacheError and nothing is saved."""
    def mock_get(url, **kwargs):
        return MockResponse("", 404)

    monkeypatch.setattr(cache.requests, "get", mock_get)
    with pytest.raises(CacheError):
        cacheurl_test.get(URL)
    assert not cacheurl_test.exists(URL)


def test_get_no_network(monkeypatch, cacheurl_test):
    """Without network (RequestException) get raises CacheError."""
    def mock_get(url, **kwargs):
        raise requests.exceptions.ConnectionError("no network")

    monkeypatch.setattr(cache.requests, "get", mock_get)
    with pytest.raises(CacheError):
        cacheurl_test.get(URL)


def test_cacheurl_missing_url(cacheurl_test):
    """exists is False and load, how_old and is_obsolete raise CacheError for a url not in cache."""
    assert not cacheurl_test.exists(URL)
    with pytest.raises(CacheError):
        cacheurl_test.load(URL)
    with pytest.raises(CacheError):
        cacheurl_test.how_old(URL)
    with pytest.raises(CacheError):
        cacheurl_test.is_obsolete(URL)


def test_cacheurl_kwargs(cacheurl_test, calls):
    """The same url with other kwargs is a different file."""
    cacheurl_test.get(URL)
    assert cacheurl_test.exists(URL)
    assert not cacheurl_test.exists(URL, timeout=5)


def test_cacheurl_how_old_not_obsolete(cacheurl_test, calls):
    """A url just downloaded has a non negative age and is not obsolete."""
    cacheurl_test.get(URL)
    assert cacheurl_test.how_old(URL) >= 0
    assert not cacheurl_test.is_obsolete(URL)


def test_cacheurl_delete(cacheurl_test, calls):
    """delete removes the url and does not fail if it is not in cache."""
    cacheurl_test.get(URL)
    cacheurl_test.delete(URL)
    assert not cacheurl_test.exists(URL)
    cacheurl_test.delete(URL)


def test_cacheurl_repr(cacheurl_test):
    """repr and str show the class name CacheURL."""
    assert repr(cacheurl_test) == "CacheURL('test_url', 1)"
    assert "CacheURL" in str(cacheurl_test)


if __name__ == "__main__":
    pytest.main([__file__])
