import functools

from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from django.core.cache import caches, DEFAULT_CACHE_ALIAS
from django.utils.encoding import iri_to_uri
from django.utils.cache import (
    get_cache_key,
    learn_cache_key,
    patch_response_headers,
    get_max_age
)
from urllib.parse import parse_qs, urlencode

from fancy_cache.utils import md5


REMEMBERED_URLS_KEY = 'fancy-urls'
LONG_TIME = 60 * 60 * 24 * 30


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
                self.get_full_path,
                self.request,
                self.only_get_keys,
                True
            )

        if self.forget_get_keys is not None:
            # then monkey patch self.request.get_full_path
            self.request.get_full_path = functools.partial(
                self.get_full_path,
                self.request,
                self.forget_get_keys,
                False
            )

    def __exit__(self, exc_type, exc_value, traceback):
        if self.only_get_keys is not None or self.forget_get_keys is not None:
            self.request.get_full_path = self._prev_get_full_path

    def get_full_path(self, this, keys, is_only_keys):
        """modified version of django.http.request.Request.get_full_path
        with the ability to return a different query string based on
        `keys` to be included or excluded
        """
        qs = this.META.get('QUERY_STRING', '')
        parsed = parse_qs(qs, keep_blank_values=True)
        if is_only_keys:
            keep = dict((k, parsed[k]) for k in parsed if k in keys)
        else:
            keep = dict((k, parsed[k]) for k in parsed if k not in keys)
        qs = urlencode(keep, True)
        return '%s%s' % (this.path, ('?' + iri_to_uri(qs)) if qs else '')


class UpdateCacheMiddleware(object):
    """
    Response-phase cache middleware that updates the cache if the response is
    cacheable.

    Must be used as part of the two-part update/fetch cache middleware.
    UpdateCacheMiddleware must be the first piece of middleware in
    MIDDLEWARE_CLASSES so that it'll get called last during the response phase.
    """

    def process_response(self, request, response):
        """Sets the cache, if needed."""
        if (
            not hasattr(request, '_cache_update_cache') or
            not request._cache_update_cache
        ):
            # We don't need to update the cache, just return.
            return response
        if request.method != 'GET':
            # This is a stronger requirement than above. It is needed
            # because of interactions between this middleware and the
            # HTTPMiddleware, which throws the body of a HEAD-request
            # away before this middleware gets a chance to cache it.
            return response
        if not response.status_code == 200:
            return response
        # Try to get the timeout from the "max-age" section of the "Cache-
        # Control" header before reverting to using the default cache_timeout
        # length.
        timeout = get_max_age(response)
        if timeout is None:
            timeout = self.cache_timeout
        elif timeout == 0:
            # max-age was set to 0, don't bother caching.
            return response

        if self.patch_headers:
            patch_response_headers(response, timeout)

        if timeout:
            if callable(self.key_prefix):
                key_prefix = self.key_prefix(request)
            else:
                key_prefix = self.key_prefix
            if self.post_process_response:
                response = self.post_process_response(
                    response,
                    request
                )

            with RequestPath(request, self.only_get_keys, self.forget_get_keys):
                cache_key = learn_cache_key(
                    request,
                    response,
                    timeout,
                    key_prefix
                )

                if self.remember_all_urls:
                    self.remember_url(request, cache_key, timeout)

            self.cache.set(cache_key, response, timeout)

        if self.post_process_response_always:
            response = self.post_process_response_always(
                response,
                request
            )

        return response

    def remember_url(self, request, cache_key, timeout):
        url = request.get_full_path()
        remembered_urls = self.cache.get(REMEMBERED_URLS_KEY, {})
        remembered_urls[url] = cache_key
        self.cache.set(
            REMEMBERED_URLS_KEY,
            remembered_urls,
            LONG_TIME
        )


class FetchFromCacheMiddleware(object):
    """
    Request-phase cache middleware that fetches a page from the cache.

    Must be used as part of the two-part update/fetch cache middleware.
    FetchFromCacheMiddleware must be the last piece of middleware in
    MIDDLEWARE_CLASSES so that it'll get called last during the request phase.
    """
    def process_request(self, request):
        """
        Checks whether the page is already cached and returns the cached
        version if available.
        """
        response = self._process_request(request)
        if self.remember_stats_all_urls:
            # then we're nosy
            cache_key = request.get_full_path()
            if response is None:
                cache_key += '__misses'
            else:
                cache_key += '__hits'
            cache_key = md5(cache_key)
            if self.cache.get(cache_key) is None:
                self.cache.set(cache_key, 0, LONG_TIME)
            self.cache.incr(cache_key)
        return response

    def _process_request(self, request):
        if self.cache_anonymous_only:
            if not hasattr(request, 'user'):
                raise ImproperlyConfigured(
                    "The Django cache middleware with "
                    "CACHE_MIDDLEWARE_ANONYMOUS_ONLY=True requires "
                    "authentication middleware to be installed. Edit your "
                    "MIDDLEWARE_CLASSES setting to insert "
                    "'django.contrib.auth.middleware.AuthenticationMiddleware'"
                    "before the CacheMiddleware."
                )

        if request.method not in ('GET', 'HEAD'):
            request._cache_update_cache = False
            # Don't bother checking the cache.
            return None

        #if (
        #    request.GET and
        #    not callable(self.key_prefix) and
        #    not self.only_get_keys
        #):
        #    request._cache_update_cache = False
        #    # Default behaviour for requests with GET parameters: don't bother
        #    # checking the cache.
        #    return None

        if self.cache_anonymous_only and request.user.is_authenticated():
            request._cache_update_cache = False
            # Don't cache requests from authenticated users.
            return None

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
            cache_key = get_cache_key(request, key_prefix)

        if cache_key is None:
            request._cache_update_cache = True
            # No cache information available, need to rebuild.
            return None

        response = self.cache.get(cache_key, None)
        if response is None:
            request._cache_update_cache = True
            # No cache information available, need to rebuild.
            return None

        request._cache_update_cache = False
        if self.post_process_response_always:
            response = self.post_process_response_always(
                response,
                request=request
            )

        return response


class CacheMiddleware(UpdateCacheMiddleware, FetchFromCacheMiddleware):
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

    :param cache_anonymous_only:
        Guess!

    :param patch_headers:
        Basically, if you set a cache_timeout of 60 it additionally sets a
        Expires header with that timeout.

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
        cache_timeout=settings.CACHE_MIDDLEWARE_SECONDS,
        key_prefix=settings.CACHE_MIDDLEWARE_KEY_PREFIX,
        cache_anonymous_only=getattr(
            settings,
            'CACHE_MIDDLEWARE_ANONYMOUS_ONLY',
            False
        ),
        patch_headers=False,
        post_process_response=None,
        post_process_response_always=None,
        only_get_keys=None,
        forget_get_keys=None,
        remember_all_urls=getattr(
            settings,
            'FANCY_REMEMBER_ALL_URLS',
            False
        ),
        remember_stats_all_urls=getattr(
            settings,
            'FANCY_REMEMBER_STATS_ALL_URLS',
            False
        ),
        **kwargs
    ):
        self.patch_headers = patch_headers
        self.cache_timeout = cache_timeout
        self.key_prefix = key_prefix
        self.cache_anonymous_only = cache_anonymous_only
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

        try:
            cache_alias = kwargs['cache_alias']
            if cache_alias is None:
                cache_alias = DEFAULT_CACHE_ALIAS
        except KeyError:
            cache_alias = settings.CACHE_MIDDLEWARE_ALIAS

        self.cache_alias = cache_alias
        self.cache = caches[self.cache_alias]
