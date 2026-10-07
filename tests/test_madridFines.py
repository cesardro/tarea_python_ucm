from pathlib import Path
import pytest
import requests
import pandas as pd
import tarea_python_ucm
import tarea_python_ucm.cache as cache
import tarea_python_ucm.madridFines as mf
from tarea_python_ucm import CacheURL, MadridFines, MadridError, get_url

FIXTURE_DIR = Path(__file__).parent.resolve() / 'data'

URL_2024_12 = ("https://datos.madrid.es/dataset/210104-0-multas-circulacion-detalle/resource/"
               "210104-15-multas-circulacion-detalle-csv/download/210104-15-multas-circulacion-detalle-csv.csv")
URL_2019_05 = ("https://datos.madrid.es/dataset/210104-0-multas-circulacion-detalle/resource/"
               "210104-91-multas-circulacion-detalle-csv/download/210104-91-multas-circulacion-detalle-csv.csv")


@pytest.fixture
def csv_2024_12():
    """Text of the December 2024 CSV sample."""
    with open(FIXTURE_DIR / "multas_2024_12.csv", encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def csv_2019_05():
    """Text of the May 2019 CSV sample."""
    with open(FIXTURE_DIR / "multas_2019_05.csv", encoding="utf-8") as f:
        return f.read()


class MockResponse:
    """Fake requests response, as in test_traductor_html.py (status_code can be changed)."""

    def __init__(self, text, status_code=200):
        self.status_code = status_code
        self.text = text


@pytest.fixture
def calls(monkeypatch, csv_2024_12, csv_2019_05):
    """Fake Internet: get_url returns the CSV url of the two sample months and requests.get the CSV text.

    Returns the list of urls asked for, to count the downloads.
    """
    urls = {(2024, 12): URL_2024_12, (2019, 5): URL_2019_05}
    pages = {URL_2024_12: csv_2024_12, URL_2019_05: csv_2019_05}
    asked = []

    def mock_get_url(year, month):
        if (year, month) not in urls:
            raise MadridError(f"{month}/{year} not found.")
        return urls[(year, month)]

    def mock_get(url, **kwargs):
        asked.append(url)
        if url in pages:
            return MockResponse(pages[url])
        return MockResponse("", 404)

    monkeypatch.setattr(mf, "get_url", mock_get_url)
    monkeypatch.setattr(mf.requests, "get", mock_get)
    return asked


@pytest.fixture
def madrid_test(monkeypatch, calls):
    """Empty MadridFines whose cache is in tests/data/cache and whose Internet is fake."""
    monkeypatch.setattr(cache, "CACHE_DIR", FIXTURE_DIR / "cache")
    m = MadridFines("test_madrid", 1)
    m.clean_cache()
    return m


@pytest.fixture
def madrid_loaded(madrid_test):
    """MadridFines with December 2024 and May 2019 added."""
    madrid_test.add(2024, 12)
    madrid_test.add(2019, 5)
    return madrid_test


@pytest.mark.parametrize("year, month", [(2024, 0), (2024, 13), (2016, 12), (2017, 5)])
def test_get_url_invalid_date(calls, year, month):
    """Month outside 1-12 or date before June 2017 raises MadridError without asking the web."""
    with pytest.raises(MadridError):
        get_url(year, month)
    assert calls == []


def test_get_url_no_network(monkeypatch):
    """Without network (RequestException) MadridError is raised."""
    def mock_get(url, **kwargs):
        raise requests.exceptions.ConnectionError("no network")

    monkeypatch.setattr(mf.requests, "get", mock_get)
    with pytest.raises(MadridError):
        get_url(2024, 12)


@pytest.mark.parametrize("app_name, obsolescence", [("", 1), (123, 1), ("x", 0), ("x", "7")])
def test_init_invalid(monkeypatch, app_name, obsolescence):
    """A wrong cache configuration raises MadridError (not CacheError)."""
    monkeypatch.setattr(cache, "CACHE_DIR", FIXTURE_DIR / "cache")
    with pytest.raises(MadridError):
        MadridFines(app_name, obsolescence)


def test_init_empty(madrid_test):
    """A new object has no data, no loaded months and a CacheURL."""
    assert madrid_test.data.empty
    assert madrid_test.loaded == []
    assert isinstance(madrid_test.cacheurl, CacheURL)
    assert repr(madrid_test.cacheurl) == "CacheURL('test_madrid', 1)"


def test_clean_coordinates_2019(madrid_test):
    """May 2019 uses COORDENADA_X / COORDENADA_Y: they are renamed to COORDENADA-X / COORDENADA-Y."""
    df = MadridFines.load(2019, 5, madrid_test.cacheurl)
    MadridFines.clean(df)
    assert "COORDENADA-X" in df.columns
    assert "COORDENADA_X" not in df.columns


def test_add_month(madrid_test):
    """add joins the cleaned month to data and registers (month, year) in loaded."""
    madrid_test.add(2024, 12)
    assert madrid_test.loaded == [(12, 2024)]
    assert len(madrid_test.data) == 10
    assert madrid_test.data.index.name == "FECHA"


def test_add_duplicate(madrid_test):
    """Adding the same month twice does nothing the second time."""
    madrid_test.add(2024, 12)
    madrid_test.add(2024, 12)
    assert madrid_test.loaded == [(12, 2024)]
    assert len(madrid_test.data) == 10


@pytest.mark.parametrize("year, month", [(2024, 13), (2017, 5), (2030, 1)])
def test_add_month_not_available(madrid_test, year, month):
    """A specific month that is not valid or not published raises MadridError."""
    with pytest.raises(MadridError):
        madrid_test.add(year, month)
    assert madrid_test.loaded == []


def test_add_whole_year(madrid_test):
    """add(year) adds every available month and skips the others without error."""
    madrid_test.add(2024)
    madrid_test.add(2019)
    assert madrid_test.loaded == [(12, 2024), (5, 2019)]
    assert len(madrid_test.data) == 16


def test_add_uses_cache(madrid_test, calls):
    """A second object with the same app_name reads the CSV from disk instead of downloading it."""
    madrid_test.add(2024, 12)
    other = MadridFines("test_madrid", 1)
    other.add(2024, 12)
    assert calls.count(URL_2024_12) == 1
    assert len(other.data) == 10


def test_clean_cache(madrid_test):
    """clean_cache deletes the files on disk but keeps data and loaded."""
    madrid_test.add(2024, 12)
    assert madrid_test.cacheurl.exists(URL_2024_12)
    madrid_test.clean_cache()
    assert not madrid_test.cacheurl.exists(URL_2024_12)
    assert madrid_test.loaded == [(12, 2024)]


def test_fines_hour(madrid_loaded):
    """fines_hour saves the figure with the given name (inside tests/data)."""
    fig = FIXTURE_DIR / "fines_hour.png"
    fig.unlink(missing_ok=True)
    madrid_loaded.fines_hour(str(fig))
    assert fig.is_file()


def test_fines_calification(madrid_loaded):
    """Number of fines of each type for every loaded month."""
    table = madrid_loaded.fines_calification()
    assert list(table.columns) == ["GRAVE", "LEVE", "MUY GRAVE"]
    assert table.loc[(12, 2024), "LEVE"] == 4
    assert table.loc[(12, 2024), "GRAVE"] == 4
    assert table.loc[(12, 2024), "MUY GRAVE"] == 2
    assert table.loc[(5, 2019), "LEVE"] == 3
    assert table.loc[(5, 2019), "GRAVE"] == 2
    assert table.loc[(5, 2019), "MUY GRAVE"] == 1


def test_total_payment(madrid_loaded):
    """MAX: everything paid in full. MIN: fines with DESCUENTO SI paid at 50 %."""
    table = madrid_loaded.total_payment()
    assert table.loc[(12, 2024), "MAX"] == 2300
    assert table.loc[(12, 2024), "MIN"] == 1400
    assert table.loc[(5, 2019), "MAX"] == 1010
    assert table.loc[(5, 2019), "MIN"] == 505


def test_package_exports():
    """The package exports its six public names."""
    assert tarea_python_ucm.__all__ == [
        "Cache", "CacheURL", "CacheError", "MadridFines", "MadridError", "get_url"]
    assert tarea_python_ucm.MadridFines is MadridFines


if __name__ == "__main__":
    pytest.main([__file__])
