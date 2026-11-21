import hashlib
import json
import time
import typing
import zlib


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


def load_remembered_urls(
    stored_value: typing.Union[None, bytes, typing.Dict[str, typing.Any]],
) -> typing.Dict[str, typing.Any]:
    """
    Turn the value stored under REMEMBERED_URLS_KEY back into a dict.

    With FANCY_COMPRESS_REMEMBERED_URLS the value is zlib-compressed JSON,
    otherwise it is the dict itself. It is detected by type rather than by
    the setting, so turning compression on or off keeps the URLs already
    remembered.

    JSON has no tuples, so each (cache_key, expiration_time) pair comes back
    as a list. It is turned back into a tuple, which is the shape
    filter_remembered_urls keeps.
    """
    if stored_value is None:
        return {}
    if isinstance(stored_value, bytes):
        decoded = json.loads(zlib.decompress(stored_value).decode())
        return {
            url: tuple(value) if isinstance(value, list) else value
            for url, value in decoded.items()
        }
    return stored_value


def dump_remembered_urls(
    remembered_urls: typing.Dict[str, typing.Any], compress: bool
) -> typing.Union[bytes, typing.Dict[str, typing.Any]]:
    """
    The value to store under REMEMBERED_URLS_KEY; see load_remembered_urls.
    """
    if compress:
        return zlib.compress(json.dumps(remembered_urls).encode())
    return remembered_urls
