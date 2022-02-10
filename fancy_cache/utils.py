import hashlib
import time
import typing


def md5(x) -> str:
    return hashlib.md5(x.encode("utf-8")).hexdigest()


def filter_remembered_urls(
    remembered_urls: typing.Dict[str, typing.Tuple[str, int]],
) -> typing.Dict[str, typing.Tuple[str, int]]:
    """
    Filter out any expired URLs from Fancy Cache's remembered urls.
    """
    now = int(time.time())
    # TODO: Remove the check for tuple in a future release as it will
    # no longer be needed once the new dictionary structure {url: (cache_key, expiration_time)}
    # has been implemented.
    remembered_urls = {
        key: value
        for key, value in remembered_urls.items()
        if isinstance(value, tuple) and value[1] > now
    }
    return remembered_urls
