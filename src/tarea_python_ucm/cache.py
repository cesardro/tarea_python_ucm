"""
Disk cache to store and retrieve text data by name.

Provides the Cache class (generic storage in a per application folder),
CacheURL (a Cache specialised in data downloaded from URLs) and the
CacheError exception. Data is stored under CACHE_DIR (~/.my_cache by default).
"""

from pathlib import Path
import time

CACHE_DIR = Path.home() / ".my_cache"


class Cache:
    """
    Generic storage in a per application folder based on given name and obsolescence time.

    Args:
        app_name (str): Name of the application.
        obsolescence (int): Number of days for being obsolete.

    Args:
        __app_name (str): Name of the application.
        __obsolescence (int): Number of days for being obsolete.
        __cache_dir (str): Full path name of application.

    Raises:
        CacheError: If the app_name is not correct, empty or null.
        CacheError: If the obsolescence is not correct, empty, null or lower/equal to zero.
    """

    def __init__(self, app_name: str, obsolescence: int) -> None:

        if not isinstance(app_name, str) or not app_name.strip():
            raise CacheError("app_name cannot be empty or null!")
        if not isinstance(obsolescence, int) or isinstance(obsolescence, bool) or obsolescence <= 0:
            raise CacheError("obsolescence must be greater than 0!")

        self.__app_name = app_name
        self.__obsolescence = obsolescence

        path = CACHE_DIR / app_name
        # parents=True creates missing parent folders; exist_ok=True avoids an error if it already exists.
        path.mkdir(parents=True, exist_ok=True)
        self.__cache_dir = str(path)

    @property
    def app_name(self) -> str:
        """
        @Property: Gets the application name of the attribute app_name.

        Returns:
            str: Returns the application name.
        """
        return self.__app_name

    @property
    def cache_dir(self) -> str:
        """
        @Property: Gets the cache directory of the attribute cache_dir.

        Returns:
            str: Returns the cache directory path.
        """
        return self.__cache_dir

    @property
    def obsolescence(self) -> int:
        """
        @Property: Gets the obsolescence value of the attribute obsolescence.

        Returns:
            int: Returns the obsolescence number.
        """
        return self.__obsolescence

    def _ruta(self, name: str) -> Path:
        """
        Retrieves the path for the given name, auxiliar method.

        Args:
            name (str): Name of the stored file.

        Returns:
            Path: Sends the full path of the given name.

        Raises:
            CacheError: If the name is not correct, empty or null.
        """
        if not isinstance(name, str) or not name.strip():
            raise CacheError("name cannot be empty or null!")
        return Path(self.cache_dir) / name

    def set(self, name: str, data: str) -> None:
        """
        Writes the data with the given name. If already exists, it is overwritten.

        Args:
            name (str): Name of the stored file.
            data (str): Data of the stored file.

        Raises:
            CacheError: If the data is empty or not a string.
            CacheError: If the name is not correct, empty or null.
        """
        if not isinstance(data, str) or not data.strip():
            raise CacheError("data cannot be empty or null!")
        path = self._ruta(name)
        path.write_text(data, encoding="utf-8")

    def exists(self, name: str) -> bool:
        """
        Checks if the file already exists.

        Args:
            name (str): Name of the stored file.

        Returns:
            bool: True if found, False if not.

        Raises:
            CacheError: If name is empty or not a string.
        """
        path = self._ruta(name)
        return path.is_file()

    def load(self, name: str) -> str:
        """
        Load the data stored in the cache under the given name.

        Args:
            name (str): Name of the stored file.

        Returns:
            str: The stored data.

        Raises:
            CacheError: If there is no element with that name.
            CacheError: If the name is not correct, empty or null.
        """
        path = self._ruta(name)
        if not path.is_file():
            raise CacheError(f"'{name}' does not exist in cache!")
        return path.read_text(encoding="utf-8")

    def how_old(self, name: str) -> float:
        """
        Checks how old is the existing file.

        Args:
            name (str): Name of the stored file.

        Returns:
            float: Returns the milliseconds that has passed.

        Raises:
            CacheError: If there is no element with that name.
            CacheError: If the name is not correct, empty or null.
        """
        path = self._ruta(name)
        if not path.is_file():
            raise CacheError(f"'{name}' does not exist in cache!")
        filetime = path.stat().st_mtime
        now = time.time()
        return ((now * 1000) - (filetime * 1000))

    def is_obsolete(self, name: str) -> bool:
        """
        Checks if given name of file is obsolete.

        Args:
            name (str): Name of the stored file.

        Returns:
            bool: True if obsolete, False if not.

        Raises:
            CacheError: If there is no element with that name.
            CacheError: If the name is not correct, empty or null.
        """
        age_ms = self.how_old(name)
        obs_ms = self.obsolescence * 24 * 60 * 60 * 1000
        if obs_ms < age_ms:
            return True
        else:
            return False

    def delete(self, name: str) -> None:
        """
        Deletes the given name file. If the file does not exists, it does not fail.

        Args:
            name (str): Name of the stored file.

        Raises:
            CacheError: If name is empty or not a string.
        """

        # unlink() deletes the file; missing_ok=True avoids an error if it does not exist.
        self._ruta(name).unlink(missing_ok=True)

    def clear(self) -> None:
        """
        Deletes all files in path for the specific application. 
        """
        for child in Path(self.cache_dir).iterdir():
            if child.is_file():
                child.unlink()


class CacheURL(Cache):
    """
    Inherits from Cache to work with URLs.
    """


class CacheError(Exception):
    """
    Controls the exceptions for class Cache.
    """
