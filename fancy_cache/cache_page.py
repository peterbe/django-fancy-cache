import typing

from django.utils.decorators import decorator_from_middleware_with_args

from .middleware import FancyCacheMiddleware


def cache_page(
    timeout: typing.Optional[float], *args, **kwargs
) -> typing.Callable:
    cache_alias = kwargs.pop("cache", None)
    return decorator_from_middleware_with_args(FancyCacheMiddleware)(
        timeout, *args, cache_alias=cache_alias, **kwargs
    )
