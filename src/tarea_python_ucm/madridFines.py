"""
Download, cleaning and analysis of Madrid traffic fines.

Provides the get_url function, the MadridFines class and the MadridError exception.
"""

import io
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
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
    looking_for = f"CSV Detalle. {this_month} {year}"
    found = None
    for a in links:
        if looking_for in a.get_text(" ", strip=True):
            found = a.get("href")
            break
    if found is None:
        raise MadridError(f"'{looking_for}' not found.")

    download = None
    for a in links:
        if a.get("href", "").startswith(found + "/download/"):
            download = a.get("href")
            break
    if download is None:
        raise MadridError(f"Download link for '{looking_for}' not found.")
    return RAIZ + download.lstrip("/")


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

    @staticmethod
    def load(year: int, month: int, cacheurl: CacheURL) -> pd.DataFrame:
        """
        @StaticMethod: Downloads (or reads from the cache) the CSV of the given
        month and returns it as a DataFrame, without cleaning.

        Args:
            year (int): Year you are looking for.
            month (int): Month you are looking for.
            cacheurl (CacheURL): Cache used to download the fines.

        Returns:
            pd.DataFrame: Returns the CSV downloaded in a Pandas DataFrame format.

        Raises:
            MadridError: If month not between 1 and 12.
            MadridError: If the date is before June 2017.
            MadridError: If no download link is found for that month.
            MadridError: If unable to download.
        """
        url = get_url(year, month)

        try:
            content = io.StringIO(cacheurl.get(url))
        except CacheError as e:
            raise MadridError(f"Unable to download '{url}': {e}")
        fines = pd.read_csv(content, sep=';', encoding='latin1')
        return fines

    def clean_cache(self) -> None:
        """
        Deletes all the files stored in the cache of this application.
        """
        self.cacheurl.clear()

    @staticmethod
    def clean(df: pd.DataFrame) -> None:
        """
        @StaticMethod: Cleans and treats the Pandas DataFrame given.

        Steps applied:
            - Strips spaces from the column names and renames COORDENADA_X/_Y.
            - Strips spaces from the value columns CALIFICACION, DESCUENTO,
              HECHO-BOL and DENUNCIANTE.
            - Casts VEL_LIMITE, VEL_CIRCULA, COORDENADA-X and COORDENADA-Y
              to numbers; empty or invalid values become NaN.
            - Builds the FECHA column from ANIO, MES and HORA,
              sets it as the index and sorts by it.

        The DataFrame passed as argument is modified directly (inplace=True), so nothing is returned.

        Args:
            df (pd.DataFrame): Raw fines of one month, as returned by load.

        Returns:
            None
        """
        same_names = {"COORDENADA_X": "COORDENADA-X",
                      "COORDENADA_Y": "COORDENADA-Y"}
        columns = ["COORDENADA-X", "COORDENADA-Y"]
        df.rename(columns=str.strip, inplace=True)
        df.rename(columns=same_names, inplace=True)
        df[columns] = df[columns].apply(pd.to_numeric, errors="coerce")
        df["CALIFICACION"] = df["CALIFICACION"].str.strip()
        df["DESCUENTO"] = df["DESCUENTO"].str.strip()
        df["HECHO-BOL"] = df["HECHO-BOL"].str.strip()
        df["DENUNCIANTE"] = df["DENUNCIANTE"].str.strip()
        columns = ["VEL_LIMITE", "VEL_CIRCULA"]
        df[columns] = df[columns].apply(pd.to_numeric, errors="coerce")
        hr = (df["HORA"] * 100).round().astype(int)
        dt = pd.DataFrame({
            "year": df["ANIO"],
            "month": df["MES"],
            "day": 1,
            "hour": hr // 100,
            "minute": hr % 100
        })
        df["FECHA"] = pd.to_datetime(dt)
        df.set_index("FECHA", inplace=True)
        df.sort_index(inplace=True)

    def add(self, year: int, month: int | None = None) -> None:
        """
        Adds the fines of the given month (or of the whole year) to DataFrame.

        If the month is already loaded, nothing is done.
        Otherwise the month is downloaded with load, cleaned with
        clean, joined to existing DataFrame (sorted by FECHA) and registered in loaded as a
        (month, year) tuple.

        If month is None, every month of the year (1 to 12) is added. Months
        that are not available (before June 2017 or not published yet) are
        skipped without raising an error.

        Args:
            year (int): Year of the fines.
            month (int | None, optional): Month of the fines (1-12). If None,
                the whole year is added.

        Raises:
            MadridError: If a specific month is not valid, not available or
                cannot be downloaded (only when month is given).
        """
        if month is None:
            for m in range(1, 13):
                try:
                    self.add(year, m)
                except MadridError:
                    pass
            return

        if (month, year) in self.__loaded:
            return None

        df = MadridFines.load(year, month, self.__cacheurl)
        MadridFines.clean(df)
        self.__data = pd.concat([self.__data, df])
        self.__data.sort_index(inplace=True)
        self.__loaded.append((month, year))

    def fines_hour(self, fig_name: str) -> None:
        """
        Draws a line chart with the number of fines per hour of the day
        and saves it as an image.

        The fines in data are counted for each hour (0-23) and each loaded
        month. The figure is saved with the given name and then closed.

        Args:
            fig_name (str): Name or path of the image file to create.

        Raises:
            MadridError: If no data has been loaded yet (use add first).
        """
        if self.__data.empty:
            raise MadridError("No data loaded: use add first.")
        hours = self.__data.index.hour
        label = self.__data["ANIO"].astype(
            str) + "-" + self.__data["MES"].astype(str)
        table = self.__data.pivot_table(
            index=hours,
            columns=label,
            fill_value=0,
            aggfunc='size'
        )
        table.plot(figsize=(10, 5), marker="o", title="Sanciones por hora")
        plt.xlabel("Hora")
        plt.ylabel("Número de sanciones")
        plt.xticks(range(24))
        plt.savefig(fig_name)
        plt.close()

    def fines_calification(self) -> pd.DataFrame:
        """
        Counts the fines of each type (CALIFICACION) for every loaded month.

        Returns:
            pd.DataFrame: Table with one row per (MES, ANIO) and one column
                per calificación (GRAVE, LEVE, MUY GRAVE). Each cell is
                the number of fines.

        Raises:
            MadridError: If no data has been loaded yet (use add first).
        """
        if self.__data.empty:
            raise MadridError("No data loaded: use add first.")
        table = self.__data.pivot_table(
            index=["MES", "ANIO"],
            columns="CALIFICACION",
            fill_value=0,
            aggfunc='size'
        )
        return table

    def total_payment(self) -> pd.DataFrame:
        """
        Summarises the total amount of the fines for every loaded month.

        Fine with DESCUENTO "SI" can be paid with a 50% discount if it is paid early,
        but it might be paid late and lose it:
            - MAX: every fine is paid in full.
            - MIN: fines with discount are paid at 50%.

        Returns:
            pd.DataFrame: Table with one row per (MES, ANIO) and the
                columns MAX and MIN with the total amounts.

        Raises:
            MadridError: If no data has been loaded yet (use add first).
        """
        if self.__data.empty:
            raise MadridError("No data loaded: use add first.")
        df = self.__data.copy()
        df["MAX"] = df["IMP_BOL"]
        df["MIN"] = np.where(df["DESCUENTO"] == "SI",
                             df["IMP_BOL"] * 0.5,
                             df["IMP_BOL"])
        table = df.pivot_table(
            index=["MES", "ANIO"],
            values=["MAX", "MIN"],
            aggfunc="sum"
        )
        return table


class MadridError(Exception):
    """
    Error raised by the madridFines module.
    """
