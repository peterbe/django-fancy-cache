import itertools
import json
import time
import unittest
import zlib
from unittest import mock

from django.core.cache import caches
from django.http import HttpResponse
from django.test import RequestFactory

from fancy_cache import cache_page
from fancy_cache.constants import REMEMBERED_URLS_KEY
from fancy_cache.memory import find_urls

PATHS = ["/page1/", "/page2/", "/page3/"]

render_count = itertools.count()


def numbered_view(request):
    return HttpResponse("render %d" % next(render_count))


class CompressedRememberedUrlsTests:
    """
    FANCY_COMPRESS_REMEMBERED_URLS behaviour, run against each cache backend
    by the subclasses below.
    """

    cache_alias: str
    use_memcached_check_and_set = False

    def setUp(self):
        self.cache = caches[self.cache_alias]
        self.cache.clear()
        self.addCleanup(self.cache.clear)
        self.patch_settings(compress=True)
        self.view = cache_page(
            60, cache=self.cache_alias, remember_all_urls=True
        )(numbered_view)

    def patch_settings(self, compress):
        patches = {
            "fancy_cache.memory.cache": self.cache,
            "fancy_cache.memory.COMPRESS_REMEMBERED_URLS": compress,
            "fancy_cache.middleware.COMPRESS_REMEMBERED_URLS": compress,
            "fancy_cache.memory.USE_MEMCACHED_CAS": (
                self.use_memcached_check_and_set
            ),
            "fancy_cache.middleware.USE_MEMCACHED_CAS": (
                self.use_memcached_check_and_set
            ),
        }
        for target, value in patches.items():
            patcher = mock.patch(target, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def get(self, path):
        return self.view(RequestFactory().get(path)).content

    def remembered_urls(self):
        return sorted(url for url, _cache_key, _stats in find_urls([]))

    def stored_remembered_urls(self):
        # With check-and-set, the remembered URLs live under the raw key.
        if self.use_memcached_check_and_set:
            return self.cache._cache.get(REMEMBERED_URLS_KEY)
        return self.cache.get(REMEMBERED_URLS_KEY)

    def store_remembered_urls(self, remembered_urls):
        if self.use_memcached_check_and_set:
            self.cache._cache.set(REMEMBERED_URLS_KEY, remembered_urls, 60)
        else:
            self.cache.set(REMEMBERED_URLS_KEY, remembered_urls, 60)

    def test_every_cached_url_is_remembered(self):
        for path in PATHS:
            self.get(path)
        self.assertEqual(self.remembered_urls(), PATHS)
        self.assertIsInstance(self.stored_remembered_urls(), bytes)

    def test_purging_one_url_keeps_the_others(self):
        for path in PATHS:
            self.get(path)
        purged = [url for url, _key, _stats in find_urls(["/page1/"], True)]
        self.assertEqual(purged, ["/page1/"])
        self.assertEqual(self.remembered_urls(), ["/page2/", "/page3/"])

    def test_purged_page_is_rendered_again(self):
        for path in PATHS:
            self.get(path)
        first_render = self.get("/page1/")
        list(find_urls(["/page1/"], purge=True))
        self.assertNotEqual(self.get("/page1/"), first_render)

    def test_urls_remembered_before_compression_was_turned_on_are_kept(self):
        self.cache.set("old-page-cache-key", "cached response")
        self.store_remembered_urls(
            {"/old/": ("old-page-cache-key", int(time.time()) + 60)}
        )
        self.get("/page1/")
        self.get("/page2/")
        self.assertEqual(
            self.remembered_urls(), ["/old/", "/page1/", "/page2/"]
        )

    def test_compression_can_be_turned_off_again(self):
        for path in PATHS:
            self.get(path)
        self.patch_settings(compress=False)
        self.get("/page4/")
        self.assertEqual(self.remembered_urls(), PATHS + ["/page4/"])
        self.assertIsInstance(self.stored_remembered_urls(), dict)

    def test_stored_format_is_zlib_compressed_json(self):
        self.get("/page1/")
        self.get("/page2/")
        stored = json.loads(zlib.decompress(self.stored_remembered_urls()))
        self.assertEqual(sorted(stored), ["/page1/", "/page2/"])


class TestCompressedRememberedUrlsLocMem(
    CompressedRememberedUrlsTests, unittest.TestCase
):
    cache_alias = "default"


class TestCompressedRememberedUrlsPyLibMC(
    CompressedRememberedUrlsTests, unittest.TestCase
):
    cache_alias = "memcached_backend"
    use_memcached_check_and_set = True


class TestCompressedRememberedUrlsPyMemcache(
    CompressedRememberedUrlsTests, unittest.TestCase
):
    cache_alias = "pymemcache_backend"
    use_memcached_check_and_set = True
