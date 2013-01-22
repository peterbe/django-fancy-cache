from django.conf import settings
from django.core.cache import cache
from django.utils.cache import get_cache_key, learn_cache_key, patch_response_headers, get_max_age


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
        if not hasattr(request, '_cache_update_cache') or not request._cache_update_cache:
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
        if timeout == None:
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
                response = self.post_process_response(response, request=request)
            cache_key = learn_cache_key(request, response, timeout, key_prefix)
            cache.set(cache_key, response, timeout)
        return response


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
        if self.cache_anonymous_only:
            assert hasattr(request, 'user'), "The Django cache middleware with CACHE_MIDDLEWARE_ANONYMOUS_ONLY=True requires authentication middleware to be installed. Edit your MIDDLEWARE_CLASSES setting to insert 'django.contrib.auth.middleware.AuthenticationMiddleware' before the CacheMiddleware."

        if not request.method in ('GET', 'HEAD'):
            request._cache_update_cache = False
            return None # Don't bother checking the cache.

        if request.GET and not callable(self.key_prefix):
            request._cache_update_cache = False
            return None # Default behaviour for requests with GET parameters: don't bother checking the cache.

        if self.cache_anonymous_only and request.user.is_authenticated():
            request._cache_update_cache = False
            return None # Don't cache requests from authenticated users.

        if callable(self.key_prefix):
            key_prefix = self.key_prefix(request)
            if key_prefix is None:
                request._cache_update_cache = False
                return None # Don't bother checking the cache if key_prefix function returns magic "None" value.
        else:
            key_prefix = self.key_prefix

        cache_key = get_cache_key(request, key_prefix)

        if cache_key is None:
            request._cache_update_cache = True
            return None # No cache information available, need to rebuild.

        response = cache.get(cache_key, None)
        if response is None:
            request._cache_update_cache = True
            return None # No cache information available, need to rebuild.

        request._cache_update_cache = False
        #response.write('\n<!-- cache HIT -->\n')
        if self.post_process_response_always and self.post_process_response:
            response = self.post_process_response(response, request=request)

        return response


class CacheMiddleware(UpdateCacheMiddleware, FetchFromCacheMiddleware):
    """
    Cache middleware that provides basic behavior for many simple sites.

    Also used as the hook point for the cache decorator, which is generated
    using the decorator-from-middleware utility.
    """
    def __init__(self,
                 cache_timeout=settings.CACHE_MIDDLEWARE_SECONDS,
                 key_prefix=settings.CACHE_MIDDLEWARE_KEY_PREFIX,
                 cache_anonymous_only=getattr(settings, 'CACHE_MIDDLEWARE_ANONYMOUS_ONLY', False),
                 patch_headers=False,
                 post_process_response=None,
                 post_process_response_always=False):
        self.patch_headers = patch_headers
        self.cache_timeout = cache_timeout
        self.key_prefix = key_prefix
        self.cache_anonymous_only = cache_anonymous_only
        self.post_process_response = post_process_response
        self.post_process_response_always = post_process_response_always
