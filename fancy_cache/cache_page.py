from django.utils.decorators import decorator_from_middleware_with_args

from .middleware import CacheMiddleware


def cache_page(*args, **kwargs):
    cache_alias = kwargs.pop('cache', None)
    return (
        decorator_from_middleware_with_args
        (CacheMiddleware)(cache_alias=cache_alias, *args, **kwargs)
    )
