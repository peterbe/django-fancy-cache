import typing

from django.utils.decorators import decorator_from_middleware_with_args

from .middleware import CacheMiddleware


def cache_page(timeout: float, *args, **kwargs) -> typing.Callable:
    cache_alias = kwargs.pop("cache", None)
    return decorator_from_middleware_with_args(CacheMiddleware)(
        timeout, *args, cache_alias=cache_alias, **kwargs
    )
