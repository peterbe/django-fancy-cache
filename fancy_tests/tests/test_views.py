import time
import unittest
import re

from django.test.client import RequestFactory
from django.core.cache import cache, caches
from unittest import mock

from fancy_cache.constants import REMEMBERED_URLS_KEY
from fancy_cache.memory import find_urls

from . import views


class TestViews(unittest.TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def tearDown(self):
        cache.clear()

    def test_render_home1(self):
        request = self.factory.get("/anything")

        response = views.home(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            re.findall("Random:\w+", response.content.decode("utf8"))
        )
        random_string_1 = re.findall(
            "Random:(\w+)", response.content.decode("utf8")
        )[0]

        # do it again
        response = views.home(request)
        self.assertEqual(response.status_code, 200)
        random_string_2 = re.findall(
            "Random:(\w+)", response.content.decode("utf8")
        )[0]
        self.assertEqual(random_string_1, random_string_2)

    @mock.patch("fancy_cache.middleware.COMPRESS_REMEMBERED_URLS", True)
    def test_render_home1_with_zlib_compression(self):
        request = self.factory.get("/anything")

        response = views.home(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            re.findall("Random:\w+", response.content.decode("utf8"))
        )
        random_string_1 = re.findall(
            "Random:(\w+)", response.content.decode("utf8")
        )[0]

        # do it again
        response = views.home(request)
        self.assertEqual(response.status_code, 200)
        random_string_2 = re.findall(
            "Random:(\w+)", response.content.decode("utf8")
        )[0]
        self.assertEqual(random_string_1, random_string_2)

    def test_render_home2(self):
        authenticated = RequestFactory(AUTH_USER="peter")
        request = self.factory.get("/2")

        response = views.home2(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            re.findall("Random:\w+", response.content.decode("utf8"))
        )
        random_string_1 = re.findall(
            "Random:(\w+)", response.content.decode("utf8")
        )[0]

        # do it again
        response = views.home2(request)
        self.assertEqual(response.status_code, 200)
        random_string_2 = re.findall(
            "Random:(\w+)", response.content.decode("utf8")
        )[0]
        self.assertEqual(random_string_1, random_string_2)

        # do it again, but with a hint to disable cache
        request = authenticated.get("/2")
        response = views.home2(request)
        self.assertEqual(response.status_code, 200)
        random_string_2 = re.findall(
            "Random:(\w+)", response.content.decode("utf8")
        )[0]
        self.assertTrue(random_string_1 != random_string_2)

    def test_render_home3(self):
        request = self.factory.get("/anything")

        response = views.home3(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            re.findall("Random:\w+", response.content.decode("utf8"))
        )
        random_string_1 = re.findall(
            "Random:(\w+)", response.content.decode("utf8")
        )[0]
        self.assertTrue("In your HTML" in response.content.decode("utf8"))
        extra_random_1 = re.findall(
            "In your HTML:(\w+)", response.content.decode("utf8")
        )[0]

        response = views.home3(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            re.findall("Random:\w+", response.content.decode("utf8"))
        )
        random_string_2 = re.findall(
            "Random:(\w+)", response.content.decode("utf8")
        )[0]
        extra_random_2 = re.findall(
            "In your HTML:(\w+)", response.content.decode("utf8")
        )[0]
        self.assertTrue("In your HTML" in response.content.decode("utf8"))
        self.assertEqual(random_string_1, random_string_2)
        # the post_process_response is only called once
        self.assertEqual(extra_random_1, extra_random_2)

    def test_render_home3_no_cache(self):
        factory = RequestFactory(AUTH_USER="peter")
        request = factory.get("/3")

        response = views.home3(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            re.findall("Random:\w+", response.content.decode("utf8"))
        )
        self.assertTrue("In your HTML" not in response.content.decode("utf8"))

    def test_render_home4(self):
        request = self.factory.get("/4")

        response = views.home4(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            re.findall("Random:\w+", response.content.decode("utf8"))
        )
        random_string_1 = re.findall(
            "Random:(\w+)", response.content.decode("utf8")
        )[0]
        self.assertTrue("In your HTML" in response.content.decode("utf8"))
        extra_random_1 = re.findall(
            "In your HTML:(\w+)", response.content.decode("utf8")
        )[0]

        response = views.home4(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            re.findall("Random:\w+", response.content.decode("utf8"))
        )
        random_string_2 = re.findall(
            "Random:(\w+)", response.content.decode("utf8")
        )[0]
        extra_random_2 = re.findall(
            "In your HTML:(\w+)", response.content.decode("utf8")
        )[0]
        self.assertTrue("In your HTML" in response.content.decode("utf8"))
        self.assertEqual(random_string_1, random_string_2)
        # the post_process_response is now called every time
        self.assertTrue(extra_random_1 != extra_random_2)

    def test_render_home5(self):
        request = self.factory.get("/4", {"foo": "bar"})
        response = views.home5(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            re.findall("Random:\w+", response.content.decode("utf8"))
        )
        random_string_1 = re.findall(
            "Random:(\w+)", response.content.decode("utf8")
        )[0]

        request = self.factory.get("/4", {"foo": "baz"})
        response = views.home5(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            re.findall("Random:\w+", response.content.decode("utf8"))
        )
        random_string_2 = re.findall(
            "Random:(\w+)", response.content.decode("utf8")
        )[0]
        self.assertTrue(random_string_1 != random_string_2)

        request = self.factory.get("/4", {"foo": "baz", "other": "junk"})
        response = views.home5(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            re.findall("Random:\w+", response.content.decode("utf8"))
        )
        random_string_3 = re.findall(
            "Random:(\w+)", response.content.decode("utf8")
        )[0]
        self.assertEqual(random_string_2, random_string_3)

    def test_render_home5bis(self):
        request = self.factory.get("/4", {"foo": "bar"})
        response = views.home5bis(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            re.findall("Random:\w+", response.content.decode("utf8"))
        )
        random_string_1 = re.findall(
            "Random:(\w+)", response.content.decode("utf8")
        )[0]

        request = self.factory.get("/4", {"foo": "baz"})
        response = views.home5bis(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            re.findall("Random:\w+", response.content.decode("utf8"))
        )
        random_string_2 = re.findall(
            "Random:(\w+)", response.content.decode("utf8")
        )[0]
        self.assertTrue(random_string_1 != random_string_2)

        request = self.factory.get("/4", {"foo": "baz", "bar": "foo"})
        response = views.home5bis(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            re.findall("Random:\w+", response.content.decode("utf8"))
        )
        random_string_3 = re.findall(
            "Random:(\w+)", response.content.decode("utf8")
        )[0]
        self.assertEqual(random_string_2, random_string_3)

    def test_remember_stats_all_urls(self):
        remembered_urls = cache.get(REMEMBERED_URLS_KEY)
        self.assertEqual(remembered_urls, None)
        request = self.factory.get("/anything")
        response = views.home6(request)
        self.assertEqual(response.status_code, 200)

        # now ask the memory thing
        (match,) = find_urls(urls=["/anything"])
        self.assertEqual(match[0], "/anything")
        self.assertEqual(match[2]["hits"], 0)
        self.assertEqual(match[2]["misses"], 1)

        remembered_urls = cache.get(REMEMBERED_URLS_KEY)
        self.assertEqual(len(remembered_urls.keys()), 1)
        self.assertEqual(list(remembered_urls.keys())[0], "/anything")
        cache_key = remembered_urls["/anything"][0]
        timeout = remembered_urls["/anything"][1]
        self.assertTrue(timeout > int(time.time()))

        # second time
        response = views.home6(request)
        self.assertEqual(response.status_code, 200)
        (match,) = find_urls(urls=["/anything"])
        self.assertEqual(match[0], "/anything")
        self.assertEqual(match[2]["hits"], 1)
        self.assertEqual(match[2]["misses"], 1)

        remembered_urls = cache.get(REMEMBERED_URLS_KEY)
        self.assertEqual(len(remembered_urls.keys()), 1)
        self.assertEqual(list(remembered_urls.keys())[0], "/anything")
        self.assertEqual(remembered_urls["/anything"][0], cache_key)
        self.assertEqual(remembered_urls["/anything"][1], timeout)
        self.assertTrue(timeout > int(time.time()))

    def test_remember_stats_all_urls_with_never_cache_decorator(self):
        request = self.factory.get("/anything")
        response = views.home9(request)
        self.assertEqual(response.status_code, 200)

        # now ask the memory thing
        (match,) = find_urls(urls=["/anything"])
        self.assertEqual(match[0], "/anything")
        self.assertEqual(match[2]["hits"], 0)
        self.assertEqual(match[2]["misses"], 1)

        # TODO: assert that the timeout was passed as expected.
        remembered_urls = cache.get(REMEMBERED_URLS_KEY)
        self.assertEqual(len(remembered_urls.keys()), 1)
        self.assertEqual(list(remembered_urls.keys())[0], "/anything")
        cache_key = remembered_urls["/anything"][0]
        timeout = remembered_urls["/anything"][1]
        self.assertTrue(timeout > int(time.time()))

        # second time
        response = views.home9(request)
        self.assertEqual(response.status_code, 200)
        (match,) = find_urls(urls=["/anything"])
        self.assertEqual(match[0], "/anything")
        self.assertEqual(match[2]["hits"], 1)
        self.assertEqual(match[2]["misses"], 1)

        remembered_urls = cache.get(REMEMBERED_URLS_KEY)
        self.assertEqual(len(remembered_urls.keys()), 1)
        self.assertEqual(list(remembered_urls.keys())[0], "/anything")
        self.assertEqual(remembered_urls["/anything"][0], cache_key)
        self.assertEqual(remembered_urls["/anything"][1], timeout)
        self.assertTrue(timeout > int(time.time()))

    def test_remember_stats_all_urls_looong_url(self):
        request = self.factory.get(
            "/something/really/long/to/start/with/right/here/since/this/will/"
            "test/that/things/work/with/long/urls/too",
            {
                "line1": "Bad luck, wind been blowing at my back",
                "line2": "I was born to bring trouble to wherever I'm at",
                "line3": "Got the number thirteen, tattooed on my neck",
                "line4": "When the ink starts to itch, ",
                "line5": "then the black will turn to red",
            },
        )
        response = views.home6(request)
        self.assertEqual(response.status_code, 200)

        # now ask the memory thing
        (match,) = find_urls()
        self.assertTrue(match[0].startswith("/something/really"))
        self.assertEqual(match[2]["hits"], 0)
        self.assertEqual(match[2]["misses"], 1)

        # second time
        response = views.home6(request)
        self.assertEqual(response.status_code, 200)
        (match,) = find_urls([])
        self.assertTrue(match[0].startswith("/something/really"))
        self.assertEqual(match[2]["hits"], 1)
        self.assertEqual(match[2]["misses"], 1)

    def test_cache_backends(self):
        request = self.factory.get("/anything")

        response = views.home7(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            re.findall("Random:\w+", response.content.decode("utf8"))
        )
        random_string_1 = re.findall(
            "Random:(\w+)", response.content.decode("utf8")
        )[0]

        # clear second cache backend
        caches["second_backend"].clear()
        response = views.home7(request)
        self.assertEqual(response.status_code, 200)
        random_string_2 = re.findall(
            "Random:(\w+)", response.content.decode("utf8")
        )[0]
        self.assertTrue(random_string_1 != random_string_2)

    def test_cache_dummy_backend(self):
        """
        Test that the Dummy cache backend works as expected by not caching.
        """
        request = self.factory.get("/anything")

        response = views.home8(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            re.findall("Random:\w+", response.content.decode("utf8"))
        )
        random_string_1 = re.findall(
            "Random:(\w+)", response.content.decode("utf8")
        )[0]

        response = views.home8(request)
        self.assertEqual(response.status_code, 200)
        random_string_2 = re.findall(
            "Random:(\w+)", response.content.decode("utf8")
        )[0]
        self.assertTrue(random_string_1 != random_string_2)

        # Make sure clearing the dummy cache doesn't raise an error,
        # even though it should do nothing.
        caches["dummy_backend"].clear()
