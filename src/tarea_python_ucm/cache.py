"""
Disk cache to store and retrieve text data by name.

Provides the Cache class (generic storage in a per application folder),
CacheURL (a Cache specialised in data downloaded from URLs) and the
CacheError exception. Data is stored under CACHE_DIR (~/.my_cache by default).
"""

from pathlib import Path
import hashlib
import time
import requests

CACHE_DIR = Path.home() / ".my_cache"


class Cache:
    """
    Generic storage in a per application folder based on given name and obsolescence time.

    Args:
        app_name (str): Name of the application.
        obsolescence (int): Number of days for being obsolete.

    Attributes:
        app_name (str): Name of the application.
        obsolescence (int): Number of days for being obsolete.
        cache_dir (str): Full path name of application.

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

    def _path(self, name: str) -> Path:
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
        path = self._path(name)
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
        path = self._path(name)
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
        path = self._path(name)
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
        path = self._path(name)
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
        # Call Cache.how_old explicitly instead of self.how_old: in CacheURL, how_old is
        # overridden to hash its argument, and name here is already the hashed file name.
        age_ms = Cache.how_old(self, name)
        obs_ms = self.obsolescence * 24 * 60 * 60 * 1000
        return obs_ms < age_ms

    def delete(self, name: str) -> None:
        """
        Deletes the given name file. If the file does not exist, it does not fail.

        Args:
            name (str): Name of the stored file.

        Raises:
            CacheError: If name is empty or not a string.
        """
        # unlink() deletes the file; missing_ok=True avoids an error if it does not exist.
        self._path(name).unlink(missing_ok=True)

    def clear(self) -> None:
        """
        Deletes all files in path for the specific application. 
        """
        for child in Path(self.cache_dir).iterdir():
            if child.is_file():
                child.unlink()

    def __str__(self) -> str:
        """
        Informal, readable representation of the cache.

        Returns:
            str: String for user to visualize.
        """
        return f"{type(self).__name__}-{self.app_name},\nObsolescence of {self.obsolescence} days.\nPath in {self.cache_dir}."

    def __repr__(self) -> str:
        """
        Formal representation that allows recreating the object.

        Returns:
            str: Expression that recreates the object.
        """
        return f"{type(self).__name__}('{self.app_name}', {self.obsolescence})"


class CacheURL(Cache):
    """
    Inherits from Cache to work with URLs.
    """

    def _hash_me(self, url: str, **kwargs) -> str:
        """
        Hashes the url along with the optional parameters.

        Args:
            url (str): URL of the request.
            **kwargs: Optional request arguments (e.g. params, timeout).

        Returns:
            str: 32-character hexadecimal MD5 hash.

        Raises:
            CacheError: If url is empty or not a string.
        """
        if not isinstance(url, str) or not url.strip():
            raise CacheError("url cannot be empty or null!")
        key = url + str(sorted(kwargs.items()))
        url_hashed = hashlib.md5(key.encode('utf-8')).hexdigest()
        return url_hashed

    def exists(self, url: str, **kwargs) -> bool:
        """
        Checks if the file already exists along with given parameters based on hash naming.

        Args:
            url (str): URL of the stored file.
            **kwargs: Optional request arguments (e.g. params, timeout).

        Returns:
            bool: True if found, False if not.

        Raises:
            CacheError: If url is empty or not a string.
        """
        return super().exists(self._hash_me(url, **kwargs))

    def load(self, url: str, **kwargs) -> str:
        """
        Load the data stored in the cache under hash along with given parameters.

        Args:
            url (str): URL of the stored file.
            **kwargs: Optional request arguments (e.g. params, timeout).

        Returns:
            str: The stored data.

        Raises:
            CacheError: If url is empty or not a string.
            CacheError: If url does not exist in cache.
        """
        if not self.exists(url, **kwargs):
            raise CacheError(f"'{url}' does not exist in cache!")
        return super().load(self._hash_me(url, **kwargs))

    def how_old(self, name: str, **kwargs) -> float:
        """
        Checks how old is the existing file with the hash naming along with parameters.

        Args:
            name (str): URL of the stored file.
            **kwargs: Optional request arguments (e.g. params, timeout).

        Returns:
            float: Returns the milliseconds that has passed.

        Raises:
            CacheError: If there is no element with that name.
            CacheError: If the name is not correct, empty or null.
        """
        if not self.exists(name, **kwargs):
            raise CacheError(f"'{name}' does not exist in cache!")
        return super().how_old(self._hash_me(name, **kwargs))

    def is_obsolete(self, name: str, **kwargs) -> bool:
        """
        Checks if given hash along with parameters of file is obsolete.

        Args:
            name (str): URL of the stored file.
            **kwargs: Optional request arguments (e.g. params, timeout).

        Returns:
            bool: True if obsolete, False if not.

        Raises:
            CacheError: If there is no element with that name.
            CacheError: If the name is not correct, empty or null.
        """
        if not self.exists(name, **kwargs):
            raise CacheError(f"'{name}' does not exist in cache!")
        return super().is_obsolete(self._hash_me(name, **kwargs))

    def delete(self, name: str, **kwargs) -> None:
        """
        Deletes the given hash name file along with the parameters. If the file does not exist, it does not fail.

        Args:
            name (str): URL of the stored file.
            **kwargs: Optional request arguments (e.g. params, timeout).

        Raises:
            CacheError: If name is empty or not a string.
        """
        super().delete(self._hash_me(name, **kwargs))

    def get(self, url: str) -> str:
        """
        Return the content of the URL: from the cache if it is stored and not obsolete. 
        Otherwise download it, store it and return it.

        Args:
            url (str): URL to download.

        Returns:
            str: The content of the URL.

        Raises:
            CacheError: If the status code is not 200.
            CacheError: If the URL cannot be reached.
        """
        if self.exists(url) and not self.is_obsolete(url):
            return self.load(url)

        try:
            response = requests.get(url)
            if response.status_code != 200:
                raise CacheError(
                    f"'{url}' returned status {response.status_code}")
            self.set(self._hash_me(url), response.text)
            return response.text
        except requests.exceptions.RequestException as e:
            raise CacheError(f"Unable to reach '{url}': {e}")


class CacheError(Exception):
    """
    Error raised by the cache module.
    """
