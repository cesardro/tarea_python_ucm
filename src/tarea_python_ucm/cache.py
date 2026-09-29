from pathlib import Path
import time

CACHE_DIR = Path.home() / ".my_cache"


class Cache:

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
        return self.__app_name

    @property
    def cache_dir(self) -> str:
        return self.__cache_dir

    @property
    def obsolescence(self) -> int:
        return self.__obsolescence

    def _ruta(self, name: str) -> Path:
        return Path(self.cache_dir) / name

    def set(self, name: str, data: str) -> None:
        if not isinstance(name, str) or not name.strip():
            raise CacheError("name cannot be empty or null!")
        if not isinstance(data, str) or not data.strip():
            raise CacheError("data cannot be empty or null!")
        path = self._ruta(name)
        path.write_text(data, encoding="utf-8")

    def exists(self, name: str) -> bool:
        path = self._ruta(name)
        return path.is_file()

    def load(self, name: str) -> str:
        path = self._ruta(name)
        if not path.is_file():
            raise CacheError(f"'{name}' does not exist in cache!")
        return path.read_text(encoding="utf-8")

    def how_old(self, name: str) -> float:
        path = self._ruta(name)
        if not path.is_file():
            raise CacheError(f"'{name}' does not exist in cache!")
        filetime = path.stat().st_mtime
        now = time.time()
        return ((now * 1000) - (filetime * 1000))

    def delete(self, name: str) -> None:
        # unlink() deletes the file; missing_ok=True avoids an error if it does not exist.
        self._ruta(name).unlink(missing_ok=True)


class CacheURL(Cache):
    pass


class CacheError(Exception):
    pass
