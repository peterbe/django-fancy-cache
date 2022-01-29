import logging
import re
import typing

from django.core.cache import cache

from fancy_cache.middleware import (
    REMEMBERED_URLS_KEY,
    LONG_TIME,
    USE_MEMCACHED_CAS,
)
from fancy_cache.utils import md5

__all__ = ("find_urls",)

LOGGER = logging.getLogger(__name__)


def _match(url, regexes):
    if not regexes:
        return url
    for regex in regexes:
        if regex.match(url):
            return True
    return False


def _urls_to_regexes(urls):
    regexes = []
    for each in urls:
        parts = each.split("*")
        if len(parts) == 1:
            regexes.append(re.compile("^%s$" % re.escape(parts[0])))
        else:
            _re = ".*".join(re.escape(x) for x in parts)
            regexes.append(re.compile("^%s$" % _re))
    return regexes


def find_urls(urls=None, purge=False):
    remembered_urls = cache.get(REMEMBERED_URLS_KEY, {})
    keys_to_delete = []
    if urls:
        regexes = _urls_to_regexes(urls)
    for url in remembered_urls:
        if not urls or _match(url, regexes):
            cache_key = remembered_urls[url]
            if not cache.get(cache_key):
                continue
            if purge:
                cache.delete(cache_key)
                keys_to_delete.append(url)
            misses_cache_key = "%s__misses" % url
            misses_cache_key = md5(misses_cache_key)
            hits_cache_key = "%s__hits" % url
            hits_cache_key = md5(hits_cache_key)

            misses = cache.get(misses_cache_key)
            hits = cache.get(hits_cache_key)
            if misses is None and hits is None:
                stats = None
            else:
                stats = {"hits": hits or 0, "misses": misses or 0}
            yield (url, cache_key, stats)

    if keys_to_delete:
        # means something was changed

        if USE_MEMCACHED_CAS is True:
            deleted = delete_keys_cas(keys_to_delete)
            if deleted is True:
                return

        remembered_urls = cache.get(REMEMBERED_URLS_KEY, {})
        remembered_urls = delete_keys(keys_to_delete, remembered_urls)
        cache.set(REMEMBERED_URLS_KEY, remembered_urls, LONG_TIME)


def delete_keys_cas(keys_to_delete: typing.List[str]) -> bool:
    result = False
    tries = 0
    while result is False and tries < 100:
        remembered_urls, cas_token = cache._cache.gets(REMEMBERED_URLS_KEY)
        if remembered_urls is None:
            return False
        remembered_urls = delete_keys(keys_to_delete, remembered_urls)
        result = cache._cache.cas(
            REMEMBERED_URLS_KEY, remembered_urls, cas_token, LONG_TIME
        )
        tries += 1
    if result is False:
        LOGGER.error("Fancy cache delete_keys_cas failed after %s tries", tries)
    return result


def delete_keys(
    keys_to_delete: typing.List[str], remembered_urls: typing.Dict[str, str]
) -> typing.Dict[str, str]:
    """
    Helper function to delete `keys_to_delete` from the `remembered_urls` dict.
    """
    for url in keys_to_delete:
        remembered_urls.pop(url)
        misses_cache_key = "%s__misses" % url
        hits_cache_key = "%s__hits" % url
        cache.delete(misses_cache_key)
        cache.delete(hits_cache_key)
    return remembered_urls
