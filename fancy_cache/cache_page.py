from django.utils.decorators import decorator_from_middleware_with_args

from .middleware import CacheMiddleware


def cache_page(*args, **kwargs):
    return (
        decorator_from_middleware_with_args
        (CacheMiddleware)(*args, **kwargs)
    )
