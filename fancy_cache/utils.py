import datetime
import hashlib
import typing

from django.conf import settings

from fancy_cache.constants import LONG_TIME, REMEMBERED_URLS_KEY

CACHE_N_DAYS = getattr(settings, "FANCY_CACHE_N_DAYS", None)


def md5(x) -> str:
    return hashlib.md5(x.encode("utf-8")).hexdigest()


def get_fancy_cache_keys_and_duration() -> typing.Tuple[typing.List[str], int]:
    cache_keys = []
    if CACHE_N_DAYS:
        days = CACHE_N_DAYS
        duration = days * 60 * 60 * 24
        while days > 0:
            key = f"fancy-cache-{datetime.date.today().isoformat()}"
            cache_keys.append(key)
            days -= 1
    else:
        cache_keys.append(REMEMBERED_URLS_KEY)
        duration = LONG_TIME
    return cache_keys, duration
