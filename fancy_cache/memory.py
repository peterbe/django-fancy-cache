import logging
import re
import typing

from django.core.cache import cache

from fancy_cache.middleware import USE_MEMCACHED_CAS

from fancy_cache.utils import md5, get_fancy_cache_keys_and_duration

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


def get_remembered_urls() -> typing.Dict[str, str]:
    fancy_cache_keys, _ = get_fancy_cache_keys_and_duration()
    remembered_urls = {}
    for fancy_cache_key in fancy_cache_keys:
        remembered_urls.update(cache.get(fancy_cache_key, {}))

    return remembered_urls


def find_urls(urls: typing.List[str] = None, purge: bool = False):
    remembered_urls = get_remembered_urls()
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
        fancy_cache_keys, duration = get_fancy_cache_keys_and_duration()
        if USE_MEMCACHED_CAS is True:
            cas_deletion_results = delete_keys_cas(keys_to_delete)

            # If keys_to_delete were not successfully removed from any
            # fancy_cache_key, identify that key and process it normally
            # (without using Memcached CAS)
            for fancy_cache_key, result in cas_deletion_results.items():
                if result is True:
                    # fancy_cache_key was handled appropriately, remove it.
                    fancy_cache_keys.remove(fancy_cache_key)

        for fancy_cache_key in fancy_cache_keys:
            remembered_urls = cache.get(fancy_cache_key, {})
            remembered_urls = delete_keys(keys_to_delete, remembered_urls)
            cache.set(fancy_cache_key, remembered_urls, duration)


def delete_keys_cas(keys_to_delete: typing.List[str]) -> typing.Dict[str, bool]:
    """
    Helper function to delete fancy cache saved keys
    using Memcached Check and Set (CAS)
    """
    fancy_cache_keys, duration = get_fancy_cache_keys_and_duration()
    total_result = {
        fancy_cache_key: False for fancy_cache_key in fancy_cache_keys
    }
    for fancy_cache_key in fancy_cache_keys:
        result = False
        tries = 0
        while result is False and tries < 100:
            remembered_urls, cas_token = cache._cache.gets(fancy_cache_key)
            if remembered_urls is None:
                break
            remembered_urls = delete_keys(keys_to_delete, remembered_urls)
            result = cache._cache.cas(
                fancy_cache_key, remembered_urls, cas_token, duration
            )
            tries += 1
        if result is False:
            LOGGER.error(
                "Fancy cache delete_keys_cas failed after %s tries", tries
            )
        else:
            total_result[fancy_cache_key] = True
    return total_result


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
