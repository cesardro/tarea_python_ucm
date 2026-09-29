from pathlib import Path

class Cache():

    __CACHE_DIR = Path.home() / ".my_cache"

    def __init__(self, app_name, obsolescence):
        self.__app_name = app_name
        self.__obsolescence = obsolescence

    @property
    def app_name(self):
        return self.__app_name

    @property
    def cache_dir(self):
        return Cache.__CACHE_DIR

    @property
    def obsolescence(self):
        return self.__obsolescence

class CacheURL(Cache):
    pass