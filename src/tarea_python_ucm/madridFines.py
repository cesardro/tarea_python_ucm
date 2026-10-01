"""
Download, cleaning and analysis of Madrid traffic fines.

Provides the get_url function, the MadridFines class and the MadridError exception.
"""

import requests
import pandas as pd
from bs4 import BeautifulSoup
from .cache import CacheURL, CacheError

RAIZ = "https://datos.madrid.es/"
DOWNLOAD = "https://datos.madrid.es/dataset/210104-0-multas-circulacion-detalle/downloads"


def get_url(year: int, month: int) -> str:
    """
    Retrieves the URL from Datos Madrid based on given year and month.

    Args:
        year (int): Year you are looking for.
        month (int): Month you are looking for.

    Returns:
        str: Full URL for download.

    Raises:
        MadridError: If month not between 1 and 12.
        MadridError: If the date is before June 2017.
        MadridError: If no download link is found for that month.
    """
    if month < 1 or month > 12:
        raise MadridError("Month must be between 1 and 12.")
    if year < 2017 or (year == 2017 and month < 6):
        raise MadridError("Date must be from June 2017.")

    try:
        response = requests.get(DOWNLOAD)
        if response.status_code != 200:
            raise MadridError(
                f"Madrid Fines returned status {response.status_code}")
        html = response.text
    except requests.exceptions.RequestException as e:
        raise MadridError(f"Unable to reach Madrid Fines: {e}")

    soup = BeautifulSoup(html, "html.parser")
    links = soup.find_all("a")
    name_months = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                   "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    this_month = name_months[month - 1]
    looking_for = f"Detalle. {this_month} {year}"
    found = None
    for a in links:
        if looking_for in a.get_text():
            found = a.get("href")
    if found is None:
        raise MadridError(f"'{looking_for}' not found.")
    return RAIZ + found.lstrip("/")


class MadridFines:
    """
    Downloads, cleans and analyses Madrid traffic fines month by month,
    using a cache (CacheURL) to avoid downloading the same file twice.

    Args:
        app_name (str): Name of the application (cache folder).
        obsolescence (int): Number of days after which a cached file is obsolete.

    Attributes:
        cacheurl (CacheURL): Object that downloads the CSV files and keeps them in the cache.
        data (pd.DataFrame): Cleaned fines of all loaded months.
        loaded (list): (month, year) tuples of the months contained in data.

    Raises:
        MadridError: If app_name or obsolescence are not valid.
    """

    def __init__(self, app_name: str, obsolescence: int) -> None:
        try:
            self.__cacheurl = CacheURL(app_name, obsolescence)
        except CacheError as e:
            raise MadridError(f"Invalid cache configuration: {e}")
        self.__data = pd.DataFrame()
        self.__loaded = []

    @property
    def cacheurl(self) -> CacheURL:
        """
        @Property: Gets the object that downloads the CSV files and keeps them in the disk cache.

        Returns:
            CacheURL: Cache used to download the fines.
        """
        return self.__cacheurl

    @property
    def data(self) -> pd.DataFrame:
        """
        @Property: Contains a cleaned DataFrame with all added months from Madrid Fines URL.

        The DataFrame is empty until a month is added with 'add' method. A copy is returned, so
        changes made to it do not affect the original DataFrame.

        Returns:
            pd.DataFrame: Cleaned DataFrame with all months added.
        """
        return self.__data.copy()

    @property
    def loaded(self) -> list:
        """
        @Property: Gets the months loaded in data.

        The list is empty until a month and year is added. A copy is returned, so
        changes made to it do not affect the object.

        Returns:
            list: (month, year) tuples of the months loaded in data.
        """
        return self.__loaded.copy()


class MadridError(Exception):
    """
    Error raised by the madridFines module.
    """
