import hashlib
from fancy_cache.constants import LONG_TIME, REMEMBERED_URLS_KEY


def md5(x) -> str:
    return hashlib.md5(x.encode("utf-8")).hexdigest()
