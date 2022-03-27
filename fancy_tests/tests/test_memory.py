import time
import unittest

from nose.tools import eq_, ok_
from django.core.cache import cache

from fancy_cache.constants import REMEMBERED_URLS_KEY
from fancy_cache.memory import find_urls


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

    def test_some_urls(self):
        found = list(find_urls(["/page2.html*"]))
        eq_(len(found), 1)
        ok_(("/page2.html", "key2", None) in found)

    def test_some_urls_double_star(self):
        found = list(find_urls(["/page*.html?*"]))
        eq_(len(found), 2)
        ok_(("/page3.html?foo=bar", "key3", None) in found)
        ok_(("/page3.html?foo=else", "key4", None) in found)
