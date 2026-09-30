"""
Download, cleaning and analysis of Madrid traffic fines.

Provides the get_url function, the MadridFines class and the MadridError exception.
"""

import requests
from bs4 import BeautifulSoup

ROOT = "https://datos.madrid.es/"
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
    return ROOT + found.lstrip("/")


class MadridFines:
    """..."""


class MadridError(Exception):
    """
    Error raised by the madridFines module.
    """
