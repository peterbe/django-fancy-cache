import time
import unittest

from django.core.cache import cache

from fancy_cache.constants import REMEMBERED_URLS_KEY
from fancy_cache.utils import filter_remembered_urls


class TestUtils(unittest.TestCase):
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

    def test_filter_remembered_urls(self):
        remembered_urls = filter_remembered_urls(self.urls)
        self.assertDictEqual(remembered_urls, self.urls)

        url = "/page1.html"
        self.urls[url] = ("key1", int(time.time()) - 1)
        remembered_urls = filter_remembered_urls(self.urls)
        self.assertEqual(len(remembered_urls.keys()), len(self.urls.keys()) - 1)
        self.assertNotIn(url, remembered_urls.keys())
