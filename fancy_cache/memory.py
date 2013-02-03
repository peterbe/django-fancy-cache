import re

from django.core.cache import cache

from fancy_cache.middleware import REMEMBERED_URLS_KEY, LONG_TIME

__all__ = ('find_urls',)


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
        parts = each.split('*')
        if len(parts) == 1:
            regexes.append(re.compile(re.escape(parts[0])))
        else:
            _re = '.*'.join(re.escape(x) for x in parts)
            regexes.append(re.compile(_re))
    return regexes


def find_urls(urls, purge=False):
    remembered_urls = cache.get(REMEMBERED_URLS_KEY, {})
    _del_keys = []
    regexes = _urls_to_regexes(urls)

    for url in remembered_urls:
        if _match(url, regexes):
            cache_key = remembered_urls[url]
            if not cache.get(cache_key):
                continue
            if purge:
                cache.delete(cache_key)
                _del_keys.append(url)
            misses_cache_key = '%s__misses' % url
            hits_cache_key = '%s__hits' % url
            misses = cache.get(misses_cache_key)
            hits = cache.get(hits_cache_key)
            if misses is None and hits is None:
                stats = None
            else:
                stats = {
                    'hits': hits or 0,
                    'misses': misses or 0
                }
            yield (url, cache_key, stats)

    if _del_keys:
        # means something was changed
        for url in _del_keys:
            remembered_urls.pop(url)
            misses_cache_key = '%s__misses' % url
            hits_cache_key = '%s__hits' % url
            cache.delete(misses_cache_key)
            cache.delete(hits_cache_key)

        cache.set(
            REMEMBERED_URLS_KEY,
            remembered_urls,
            LONG_TIME
        )
