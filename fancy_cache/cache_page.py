"""
Decorator for views that tries getting the page from the cache and
populates the cache if the page isn't in the cache yet.

Works similar to standard Django cache_page decorator, but accept
2 parameters: timeout and callable key_prefix. It makes it easier to
fine-tune view caching (cache based on anything in request: GET parameters,
cookies, etc.)

The sample syntax::

    #have 2 static versions of the my_view response for authenticated and anonymous users

    def my_key_prefix(request):
        if request.GET:
            return None #magic value to disable caching

        if request.user.is_authenticated():
            return 'logged_in'
        else:
            return 'not_logged_in'

    @cache_control(must_revalidate=True)
    @cache_page_with_prefix(600, my_key_prefix)
    def my_view(request):
    ....... #something is different for authenticated and anonymous users
    #cache my_paginated_view based on "page" parameter in query string


    def page_key_prefix(request):
        return request.GET.get('page','')

    @cache_page_with_prefix(60, page_key_prefix)
    def my_paginated_view(request)
    .... #page number is passed via 'page' GET parameter and used for pagination

"""


from django.core.cache import cache
from django.http import HttpRequest
from django.utils.cache import get_cache_key
from django.utils.decorators import decorator_from_middleware
from .middleware import CacheMiddleware


''' decorator for advanced view caching '''
from django.utils.decorators import decorator_from_middleware_with_args

def cache_page(*args, **kwargs):
    return decorator_from_middleware_with_args(CacheMiddleware)(*args, **kwargs)



def expire_page(path, key_prefix=None):
    """
    Delete page from cache based on it's url
    """
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
    for prefix in key_prefixes:
        expire_page(path, prefix)
