import typing

from django.utils.decorators import decorator_from_middleware_with_args

from .middleware import FancyCacheMiddleware


def cache_page(
    timeout: typing.Optional[float],
    *,
    cache: str = None,
    key_prefix: str = None,
    **kwargs
) -> typing.Callable:
    return decorator_from_middleware_with_args(FancyCacheMiddleware)(
        page_timeout=timeout, cache_alias=cache, key_prefix=key_prefix, **kwargs
    )
