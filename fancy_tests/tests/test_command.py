import time

from django.test import TestCase
from nose.tools import ok_
from django.core.cache import cache
from django.core.management import call_command
from io import StringIO
from fancy_cache.constants import REMEMBERED_URLS_KEY


class TestBaseCommand(TestCase):
    def setUp(self):
        expiration_time = int(time.time()) + 5
        self.urls = {
            "/page1.html": (
                "key1",
                expiration_time,
            ),
            "/page2.html": (
                "key2",
                expiration_time,
            ),
            "/page3.html?foo=bar": (
                "key3",
                expiration_time,
            ),
            "/page3.html?foo=else": (
                "key4",
                expiration_time,
            ),
        }
        for key, value in self.urls.items():
            cache.set(value[0], key)
        cache.set(REMEMBERED_URLS_KEY, self.urls, 5)

    def tearDown(self):
        cache.clear()

    def test_fancyurls_command(self):
        out = StringIO()
        call_command("fancy-urls", verbosity=3, stdout=out)
        self.assertIn("4 URLs cached", out.getvalue())

    def test_purge_command(self):
        out = StringIO()
        # Note: first call will show 4 URLs, so call again to confirm deletion
        call_command("fancy-urls", "--purge")
        call_command("fancy-urls", verbosity=3, stdout=out)
        self.assertIn("0 URLs cached", out.getvalue())
