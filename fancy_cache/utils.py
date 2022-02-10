import hashlib


def md5(x) -> str:
    return hashlib.md5(x.encode("utf-8")).hexdigest()
