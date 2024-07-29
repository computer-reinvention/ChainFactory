import os
import json

BASE_CACHE_PATH = ".chainfactory/cache"

if not os.path.exists(BASE_CACHE_PATH):
    os.makedirs(BASE_CACHE_PATH, exist_ok=True)


def save_cache_file(key: str, value: dict) -> None:
    """
    This function loads the cache file from the filesystem.
    """
    path = os.path.join(BASE_CACHE_PATH, key)

    with open(path, "w") as file:
        json.dump(value, file)


def load_cache_file(key: str) -> dict | None:
    """
    This function loads the cache file contents from the filesystem.
    """
    path = os.path.join(BASE_CACHE_PATH, key)

    if not os.path.exists(path):
        return None

    with open(path, "r") as file:
        return json.load(file)
