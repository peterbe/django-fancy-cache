import logging
import re
import typing

from django.core.cache import cache

from fancy_cache.constants import LONG_TIME, REMEMBERED_URLS_KEY
from fancy_cache.middleware import USE_MEMCACHED_CAS
from fancy_cache.utils import md5, filter_remembered_urls

__all__ = ("find_urls",)

LOGGER = logging.getLogger(__name__)


def _match(url: str, regexes: typing.List[typing.Pattern[str]]):
    if not regexes:
        return url
    for regex in regexes:
        if regex.match(url):
            return True
    return False


def _urls_to_regexes(
    urls: typing.List[str],
) -> typing.List[typing.Pattern[str]]:
    regexes = []
    for each in urls:
        parts = each.split("*")
        if len(parts) == 1:
            regexes.append(re.compile("^%s$" % re.escape(parts[0])))
        else:
            _re = ".*".join(re.escape(x) for x in parts)
            regexes.append(re.compile("^%s$" % _re))
    return regexes


def find_urls(
    urls: typing.List[str] = None, purge: bool = False
) -> typing.Generator[
    typing.Tuple[str, str, typing.Optional[typing.Dict[str, int]]], None, None
]:
    remembered_urls = cache.get(REMEMBERED_URLS_KEY, {})
    keys_to_delete = []
    if urls:
        regexes = _urls_to_regexes(urls)
    for url in remembered_urls:
        if not urls or _match(url, regexes):
            cache_key_tuple = remembered_urls[url]

            # TODO: Remove the check for tuple in a future release as it will
            # no longer be needed once the new dictionary structure {url: (cache_key, expiration_time)}
            # has been implemented.
            if isinstance(cache_key_tuple, str):
                cache_key_tuple = (
                    cache_key_tuple,
                    0,
                )

            cache_key = cache_key_tuple[0]

            if not cache.get(cache_key):
                if purge:
                    keys_to_delete.append(url)
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
        try:
            remembered_urls, cas_token = cache._cache.gets(REMEMBERED_URLS_KEY)
        except AttributeError:
            return False
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
    keys_to_delete: typing.List[str],
    remembered_urls: typing.Dict[str, typing.Tuple[str, int]],
) -> typing.Dict[str, typing.Tuple[str, int]]:
    """
    Helper function to delete `keys_to_delete` from the `remembered_urls` dict.
    """
    for url in keys_to_delete:
        remembered_urls.pop(url)
        misses_cache_key = "%s__misses" % url
        hits_cache_key = "%s__hits" % url
        cache.delete(misses_cache_key)
        cache.delete(hits_cache_key)
    remembered_urls = filter_remembered_urls(remembered_urls)
    return remembered_urls
