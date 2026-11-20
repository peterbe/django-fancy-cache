import json
import time
import unittest
import zlib

from fancy_tests.tests.assertions import eq_, ok_
from django.core.cache import cache, caches
from unittest import mock

from fancy_cache.constants import REMEMBERED_URLS_KEY
from fancy_cache.memory import find_urls
from fancy_cache.utils import md5


class TestMemory(unittest.TestCase):
    def setUp(self):
        expiration_time = int(time.time()) + 5
        self.urls = {
            "/page1.html": ("key1", expiration_time),
            "/page2.html": ("key2", expiration_time),
            "/page3.html?foo=bar": ("key3", expiration_time),
            "/page3.html?foo=else": ("key4", expiration_time),
        }
        for key, value in self.urls.items():
            cache.set(value[0], key)
        cache.set(REMEMBERED_URLS_KEY, self.urls, 5)

    def tearDown(self):
        cache.clear()

    def test_find_all_urls(self):
        found = list(find_urls([]))
        eq_(len(found), 4)
        for key, value in self.urls.items():
            pair = (key, value[0], None)
            ok_(pair in found)

    def test_find_and_purge_all_urls(self):
        found = list(find_urls([], purge=True))
        eq_(len(found), 4)
        for key, value in self.urls.items():
            pair = (key, value[0], None)
            ok_(pair in found)
        found = list(find_urls([]))
        eq_(len(found), 0)

    @mock.patch("fancy_cache.memory.COMPRESS_REMEMBERED_URLS", True)
    def test_find_and_purge_all_urls_with_zlib_compression(self):
        remembered_urls = cache.get(REMEMBERED_URLS_KEY)
        remembered_urls = zlib.compress(json.dumps(remembered_urls).encode())
        cache.set(REMEMBERED_URLS_KEY, remembered_urls, 5)
        found = list(find_urls([], purge=True))
        eq_(len(found), 4)
        for key, value in self.urls.items():
            pair = (key, value[0], None)
            ok_(pair in found)
        found = list(find_urls([]))
        eq_(len(found), 0)

    @mock.patch("fancy_cache.memory.COMPRESS_REMEMBERED_URLS", True)
    def test_find_and_purge_all_urls_with_zlib_compression_first_time(self):
        """
        When enabling zlib compression, the existing REMEMBERED_URLS
        will not be compressed yet. This test ensures that the transition to
        compressed REMEMBERED_URLS is seamless.
        """
        remembered_urls = cache.get(REMEMBERED_URLS_KEY)
        cache.set(REMEMBERED_URLS_KEY, remembered_urls, 5)
        found = list(find_urls([], purge=True))
        eq_(len(found), 4)
        for key, value in self.urls.items():
            pair = (key, value[0], None)
            ok_(pair in found)
        found = list(find_urls([]))
        eq_(len(found), 0)

    def test_find_one_url(self):
        found = list(find_urls(["/page1.html"]))
        eq_(len(found), 1)
        ok_(("/page1.html", "key1", None) in found)

    def test_purge_one_url(self):
        ok_(cache.get("key1"))
        ok_("/page1.html" in cache.get(REMEMBERED_URLS_KEY))
        found = list(find_urls(["/page1.html"], purge=True))
        eq_(len(found), 1)
        ok_(("/page1.html", "key1", None) in found)

        ok_(not cache.get("key1"))
        ok_("/page1.html" not in cache.get(REMEMBERED_URLS_KEY))
        # find all the rest in there
        found = list(find_urls([]))
        eq_(len(found), 3)
        ok_(("/page1.html", "key1", None) not in found)

    def test_purge_one_expired_url(self):
        """
        If a URL has expired from the cache it should still
        be deleted from remembered URLs when `find_urls` is called
        with `purge=True`.
        """
        cache.delete("key1")
        ok_(not cache.get("key1"))
        ok_("/page1.html" in cache.get(REMEMBERED_URLS_KEY))
        found = list(find_urls(["/page1.html"], purge=True))
        eq_(len(found), 0)
        ok_(not cache.get("key1"))
        ok_("/page1.html" not in cache.get(REMEMBERED_URLS_KEY))

        # find all the rest in there
        found = list(find_urls([]))
        eq_(len(found), 3)
        ok_(("/page1.html", "key1", None) not in found)

    def test_purge_url_that_another_process_already_purged(self):
        """
        Two processes can purge the same URL at once. Whichever writes the
        remembered URLs back second must not fail because the URL is gone.
        """
        first_purge = find_urls(["/page1.html"], purge=True)
        next(first_purge)
        list(find_urls(["/page1.html"], purge=True))
        list(first_purge)
        self.assertNotIn("/page1.html", cache.get(REMEMBERED_URLS_KEY))

    def test_purge_deletes_hit_and_miss_counts(self):
        hits_cache_key = md5("/page1.html__hits")
        misses_cache_key = md5("/page1.html__misses")
        cache.set(hits_cache_key, 3)
        cache.set(misses_cache_key, 1)
        found = list(find_urls(["/page1.html"], purge=True))
        self.assertEqual(
            found, [("/page1.html", "key1", {"hits": 3, "misses": 1})]
        )
        self.assertIsNone(cache.get(hits_cache_key))
        self.assertIsNone(cache.get(misses_cache_key))

    def test_some_urls(self):
        found = list(find_urls(["/page2.html*"]))
        eq_(len(found), 1)
        ok_(("/page2.html", "key2", None) in found)

    def test_some_urls_double_star(self):
        found = list(find_urls(["/page*.html?*"]))
        eq_(len(found), 2)
        ok_(("/page3.html?foo=bar", "key3", None) in found)
        ok_(("/page3.html?foo=else", "key4", None) in found)


class TestMemoryWithMemcached(unittest.TestCase):
    def setUp(self):
        expiration_time = int(time.time()) + 5
        self.urls = {
            "/page1.html": ("key1", expiration_time),
            "/page2.html": ("key2", expiration_time),
            "/page3.html?foo=bar": ("key3", expiration_time),
            "/page3.html?foo=else": ("key4", expiration_time),
        }
        self.cache = caches["memcached_backend"]
        for key, value in self.urls.items():
            self.cache.set(value[0], key)
        self.cache._cache.set(REMEMBERED_URLS_KEY, self.urls, 5)

    def tearDown(self):
        cache.clear()
        self.cache.clear()

    @mock.patch("fancy_cache.memory.USE_MEMCACHED_CAS", True)
    @mock.patch("fancy_cache.memory.cache", caches["memcached_backend"])
    def test_purge_url_that_another_process_already_purged(self):
        first_purge = find_urls(["/page1.html"], purge=True)
        next(first_purge)
        list(find_urls(["/page1.html"], purge=True))
        list(first_purge)
        self.assertNotIn(
            "/page1.html", self.cache._cache.get(REMEMBERED_URLS_KEY)
        )

    @mock.patch("fancy_cache.memory.USE_MEMCACHED_CAS", True)
    @mock.patch("fancy_cache.memory.cache", caches["memcached_backend"])
    def test_purge_url_longer_than_memcached_key_limit(self):
        """
        Memcached rejects keys over 250 characters, so any cache key built
        from a URL must be hashed.
        """
        long_url = "/page1.html?" + "&".join(
            "filter%d=value" % number for number in range(20)
        )
        self.assertGreater(len(long_url), 250)
        self.cache.set("key5", long_url)
        remembered_urls = self.cache._cache.get(REMEMBERED_URLS_KEY)
        remembered_urls[long_url] = ("key5", int(time.time()) + 5)
        self.cache._cache.set(REMEMBERED_URLS_KEY, remembered_urls, 5)

        found = list(find_urls([long_url], purge=True))
        self.assertEqual(found, [(long_url, "key5", None)])
        self.assertNotIn(long_url, self.cache._cache.get(REMEMBERED_URLS_KEY))

    @mock.patch("fancy_cache.memory.USE_MEMCACHED_CAS", True)
    @mock.patch("fancy_cache.memory.cache", caches["memcached_backend"])
    def test_purge_one_url_with_memcached_check_and_set(self):
        ok_(self.cache.get("key1"))
        ok_("/page1.html" in self.cache._cache.get(REMEMBERED_URLS_KEY))
        found = list(find_urls(["/page1.html"], purge=True))
        eq_(len(found), 1)
        ok_(("/page1.html", "key1", None) in found)

        ok_(not cache.get("key1"))
        ok_("/page1.html" not in self.cache._cache.get(REMEMBERED_URLS_KEY))
        # find all the rest in there
        found = list(find_urls([]))
        eq_(len(found), 3)
        ok_(("/page1.html", "key1", None) not in found)
