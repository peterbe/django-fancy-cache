from django.core.cache import cache
from django.http import HttpRequest
from django.utils.cache import get_cache_key
from django.utils.decorators import decorator_from_middleware_with_args

from .middleware import CacheMiddleware


def cache_page(*args, **kwargs):
    return decorator_from_middleware_with_args(CacheMiddleware)(*args, **kwargs)


def expire_page(path, key_prefix=None):
    """
    Delete page from cache based on it's url
    """
    # XXX this needs a lot more work
    request = HttpRequest()
    request.path = path
    key = get_cache_key(request, key_prefix)
    if cache.has_key(key):
        cache.delete(key)
        return key

def expire_pages(path, key_prefixes):
    """
    Delete pages from cache based on their url and list of possible key_prefixes
    """
    # XXX this needs a lot more work
    for prefix in key_prefixes:
        expire_page(path, prefix)
