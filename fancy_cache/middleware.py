"""
Middleware based on Django's cache middleware.
See https://github.com/django/django/blob/main/django/middleware/cache.py
"""
import functools
import logging
import time
import typing

from django.conf import settings
from django.core.cache import DEFAULT_CACHE_ALIAS, caches
from django.middleware.cache import (
    FetchFromCacheMiddleware,
    UpdateCacheMiddleware,
)
from django.utils.encoding import iri_to_uri
from django.utils.cache import (
    get_cache_key,
    has_vary_header,
    learn_cache_key,
    patch_response_headers,
    get_max_age,
)
from urllib.parse import parse_qs, urlencode

from fancy_cache.constants import REMEMBERED_URLS_KEY, LONG_TIME
from fancy_cache.utils import md5, filter_remembered_urls

LOGGER = logging.getLogger(__name__)

USE_MEMCACHED_CAS = getattr(
    settings, "FANCY_USE_MEMCACHED_CHECK_AND_SET", False
)


class RequestPath(object):
    def __init__(self, request, only_get_keys, forget_get_keys):
        self.request = request
        self.only_get_keys = only_get_keys
        self.forget_get_keys = forget_get_keys
        assert not (self.only_get_keys and self.forget_get_keys)
        self._prev_get_full_path = request.get_full_path

    def __enter__(self):
        if self.only_get_keys is not None:
            # then monkey patch self.request.get_full_path
            self.request.get_full_path = functools.partial(
                self.get_full_path, self.request, self.only_get_keys, True
            )

        if self.forget_get_keys is not None:
            # then monkey patch self.request.get_full_path
            self.request.get_full_path = functools.partial(
                self.get_full_path, self.request, self.forget_get_keys, False
            )

    def __exit__(self, exc_type, exc_value, traceback):
        if self.only_get_keys is not None or self.forget_get_keys is not None:
            self.request.get_full_path = self._prev_get_full_path

    def get_full_path(self, this, keys, is_only_keys):
        """modified version of django.http.request.Request.get_full_path
        with the ability to return a different query string based on
        `keys` to be included or excluded
        """
        qs = this.META.get("QUERY_STRING", "")
        parsed = parse_qs(qs, keep_blank_values=True)
        if is_only_keys:
            keep = dict((k, parsed[k]) for k in parsed if k in keys)
        else:
            keep = dict((k, parsed[k]) for k in parsed if k not in keys)
        qs = urlencode(keep, True)
        return "%s%s" % (this.path, ("?" + iri_to_uri(qs)) if qs else "")


class FancyUpdateCacheMiddleware(UpdateCacheMiddleware):
    """
    Response-phase cache middleware that updates the cache if the response is
    cacheable.

    Must be used as part of the two-part update/fetch cache middleware.
    UpdateCacheMiddleware must be the first piece of middleware in MIDDLEWARE
    so that it'll get called last during the response phase.
    """

    def __init__(self, get_response=None):
        super().__init__(get_response)

    def process_response(self, request, response):
        """Set the cache, if needed."""
        if not self._should_update_cache(request, response):
            # We don't need to update the cache, just return.
            return response

        if response.streaming or response.status_code not in (200, 304):
            return response

        # Don't cache responses that set a user-specific (and maybe security
        # sensitive) cookie in response to a cookie-less request.
        if (
            not request.COOKIES
            and response.cookies
            and has_vary_header(response, "Cookie")
        ):
            return response

        # Don't cache a response with 'Cache-Control: private'
        if "private" in response.get("Cache-Control", ()):
            return response

        # Page timeout takes precedence over the "max-age" and the default
        # cache timeout.
        timeout = self.page_timeout
        if timeout is None:
            # The timeout from the "max-age" section of the "Cache-Control"
            # header takes precedence over the default cache timeout.
            timeout = get_max_age(response)
            if timeout is None:
                timeout = self.cache_timeout
            elif timeout == 0:
                # max-age was set to 0, don't cache.
                return response
        patch_response_headers(response, timeout)
        if timeout and response.status_code == 200:
            if callable(self.key_prefix):
                key_prefix = self.key_prefix(request)
            else:
                key_prefix = self.key_prefix
            if self.post_process_response:
                response = self.post_process_response(response, request)

            with RequestPath(request, self.only_get_keys, self.forget_get_keys):
                cache_key = learn_cache_key(
                    request, response, timeout, key_prefix, cache=self.cache
                )

                if self.remember_all_urls:
                    self.remember_url(request, cache_key, timeout)

            if hasattr(response, "render") and callable(response.render):
                response.add_post_render_callback(
                    lambda r: self.cache.set(cache_key, r, timeout)
                )
            else:
                self.cache.set(cache_key, response, timeout)

        if self.post_process_response_always:
            response = self.post_process_response_always(response, request)

        return response

    def remember_url(self, request, cache_key: str, timeout: int) -> None:
        """
        Function to remember a newly cached URL.

        All cached URLs are remembered in a dictionary
        in the cache under REMEMBERED_URLS_KEY.

        This dictionary is structured as follows:
        - The key is the URL
        - The value is a tuple (cache key string, expiration time in seconds integer)

        If USE_MEMCACHED_CAS is True, we try to use CAS (check and set)
        to set the dictionary via self.cache._cache.cas to avoid missing
        cached URLs in high traffic environments.cache._cache.cas.

        See Issue #7 for more information:
        https://github.com/peterbe/django-fancy-cache/issues/7
        """
        url = request.get_full_path()
        expiration_time = int(time.time()) + timeout

        if USE_MEMCACHED_CAS is True:
            # Memcached check-and-set is available.
            # Try using check-and-set to avoid a race condition
            # in remembering urls; if this fails, fallback to cache.set.
            result = self._remember_url_cas(url, cache_key, expiration_time)
            if result:
                # Remembered URLs have been successfully saved
                # via Memcached CAS.
                return

        remembered_urls = self.cache.get(REMEMBERED_URLS_KEY, {})
        remembered_urls = filter_remembered_urls(remembered_urls)
        remembered_urls[url] = (cache_key, expiration_time)
        self.cache.set(REMEMBERED_URLS_KEY, remembered_urls, LONG_TIME)

    def _remember_url_cas(
        self, url: str, cache_key: str, expiration_time: int
    ) -> bool:
        """
        Helper function to use Memcached CAS to store remembered URLs.
        This addresses race conditions when using Memcached.
        See Issue #7: https://github.com/peterbe/django-fancy-cache/issues/7.
        """
        result = False
        tries = 0  # Make sure an unexpected error doesn't cause a loop
        while result is False and tries <= 100:
            try:
                remembered_urls, cas_token = self.cache._cache.gets(
                    REMEMBERED_URLS_KEY
                )
            except AttributeError:
                return False

            if remembered_urls is None:
                # No cache entry; set the cache using `cache.set`.
                return False

            remembered_urls = filter_remembered_urls(remembered_urls)

            remembered_urls[url] = (cache_key, expiration_time)

            result = self.cache._cache.cas(
                REMEMBERED_URLS_KEY, remembered_urls, cas_token, LONG_TIME
            )

            tries += 1

        if result is False:
            LOGGER.error(
                "Django-fancy-cache failed to save using CAS after %s tries.",
                tries,
            )
        return result


class FancyFetchFromCacheMiddleware(FetchFromCacheMiddleware):
    """
    Request-phase cache middleware that fetches a page from the cache.

    Must be used as part of the two-part update/fetch cache middleware.
    FetchFromCacheMiddleware must be the last piece of middleware in MIDDLEWARE
    so that it'll get called last during the request phase.
    """

    def __init__(self, get_response=None):
        super().__init__(get_response)

    def process_request(self, request):
        """
        Check whether the page is already cached and return the cached
        version if available.
        """
        response = self._process_request(request)
        if self.remember_stats_all_urls:
            # then we're nosy
            cache_key = request.get_full_path()
            if response is None:
                cache_key += "__misses"
            else:
                cache_key += "__hits"
            cache_key = md5(cache_key)
            if self.cache.get(cache_key) is None:
                self.cache.set(cache_key, 0, LONG_TIME)
            self.cache.incr(cache_key)
        return response

    def _process_request(self, request):
        if request.method not in ("GET", "HEAD"):
            request._cache_update_cache = False
            return None  # Don't bother checking the cache.

        if callable(self.key_prefix):
            key_prefix = self.key_prefix(request)
            if key_prefix is None:
                request._cache_update_cache = False
                # Don't bother checking the cache if key_prefix function
                # returns magic "None" value.
                return None
        else:
            key_prefix = self.key_prefix

        with RequestPath(request, self.only_get_keys, self.forget_get_keys):
            # try and get the cached GET response
            cache_key = get_cache_key(
                request, key_prefix, "GET", cache=self.cache
            )

        if cache_key is None:
            request._cache_update_cache = True
            return None  # No cache information available, need to rebuild.
        response = self.cache.get(cache_key)
        # if it wasn't found and we are looking for a HEAD, try looking just for that
        if response is None and request.method == "HEAD":
            cache_key = get_cache_key(
                request, key_prefix, "HEAD", cache=self.cache
            )
            response = self.cache.get(cache_key)

        if response is None:
            request._cache_update_cache = True
            return None  # No cache information available, need to rebuild.

        # hit, return cached response
        request._cache_update_cache = False
        if self.post_process_response_always:
            response = self.post_process_response_always(
                response, request=request
            )

        return response


class FancyCacheMiddleware(
    FancyUpdateCacheMiddleware, FancyFetchFromCacheMiddleware
):
    """
    Cache middleware that provides basic behavior for many simple sites.

    Also used as the hook point for the cache decorator, which is generated
    using the decorator-from-middleware utility.

    :param cache_timeout:
        How many seconds to cache the page. This is ignored if the view sets a
        Cache-Control header with a max-age.

    :param key_prefix:
        Either a string or a callable function. If it's a callable function,
        it's called with the request as the first and only argument.

    :param post_process_response:
        Callable function that gets called with the response (and request) just
        before the response gets set in cache.

    :param post_process_response_always:
        Callable function that gets called with the response (and request)
        every time the response goes through the middleware cached or not.

    :param only_get_keys:
        List of query string keys to reduce the cache key to. Without this a
        GET /some/path?foo=bar and /some/path?foo=bar&other=junk gets two
        different cache keys when it could be that the `other=junk` parameter
        doesn't change anything.

    :param forget_get_keys:
        List of query string keys to ignore when reducing the cache key.

    :param remember_all_urls:
        With this option you can have all cached URLs stored in cache which
        can make it easy to do things like cache invalidation by URL.

    :param remember_stats_all_urls:
        Only applicable if `remember_all_urls` is set. This stores a count
        of the number of times a `cache_page` hits and misses.

    """

    def __init__(
        self,
        get_response: typing.Callable = None,
        cache_timeout=None,
        page_timeout: int = None,
        post_process_response=None,
        post_process_response_always=None,
        only_get_keys=None,
        forget_get_keys=None,
        remember_all_urls=getattr(settings, "FANCY_REMEMBER_ALL_URLS", False),
        remember_stats_all_urls=getattr(
            settings, "FANCY_REMEMBER_STATS_ALL_URLS", False
        ),
        **kwargs
    ):
        super().__init__(get_response)
        # We need to differentiate between "provided, but using default value",
        # and "not provided". If the value is provided using a default, then
        # we fall back to system defaults. If it is not provided at all,
        # we need to use middleware defaults.

        try:
            key_prefix = kwargs["key_prefix"]
            if key_prefix is None:
                key_prefix = ""
            self.key_prefix = key_prefix
        except KeyError:
            pass
        try:
            cache_alias = kwargs["cache_alias"]
            if cache_alias is None:
                cache_alias = DEFAULT_CACHE_ALIAS
            self.cache_alias = cache_alias
            # TODO: Likely this will cause a conflict with this commit
            # in Django 4.1+:
            # https://github.com/django/django/commit/3ff7b15bb79f2ee5b7af245c55ae14546243bb77
            # The commit uses a @property decorator to set self.cache
            # instead of setting it directly as we do in the line below.
            # We can likely solve this by simply removing this line,
            # but will need to make sure that the library still works for
            # older versions of Django that use this `self.cache =` method.
            self.cache = caches[self.cache_alias]
        except KeyError:
            pass

        if cache_timeout is not None:
            self.cache_timeout = cache_timeout
        self.page_timeout = page_timeout

        self.post_process_response = post_process_response
        self.post_process_response_always = post_process_response_always
        if isinstance(only_get_keys, str):
            only_get_keys = [only_get_keys]
        self.only_get_keys = only_get_keys
        if isinstance(forget_get_keys, str):
            forget_get_keys = [forget_get_keys]
        self.forget_get_keys = forget_get_keys
        self.remember_all_urls = remember_all_urls
        self.remember_stats_all_urls = remember_stats_all_urls
