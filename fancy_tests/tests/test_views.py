import mock
import time
import unittest
import re
from nose.tools import eq_, ok_
from django.test.client import RequestFactory
from django.core.cache import cache, caches
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
        eq_(response.status_code, 200)
        ok_(re.findall("Random:\w+", response.content.decode("utf8")))
        random_string_1 = re.findall(
            "Random:(\w+)", response.content.decode("utf8")
        )[0]

        # do it again
        response = views.home(request)
        eq_(response.status_code, 200)
        random_string_2 = re.findall(
            "Random:(\w+)", response.content.decode("utf8")
        )[0]
        eq_(random_string_1, random_string_2)

    def test_render_home2(self):
        authenticated = RequestFactory(AUTH_USER="peter")
        request = self.factory.get("/2")

        response = views.home2(request)
        eq_(response.status_code, 200)
        ok_(re.findall("Random:\w+", response.content.decode("utf8")))
        random_string_1 = re.findall(
            "Random:(\w+)", response.content.decode("utf8")
        )[0]

        # do it again
        response = views.home2(request)
        eq_(response.status_code, 200)
        random_string_2 = re.findall(
            "Random:(\w+)", response.content.decode("utf8")
        )[0]
        eq_(random_string_1, random_string_2)

        # do it again, but with a hint to disable cache
        request = authenticated.get("/2")
        response = views.home2(request)
        eq_(response.status_code, 200)
        random_string_2 = re.findall(
            "Random:(\w+)", response.content.decode("utf8")
        )[0]
        ok_(random_string_1 != random_string_2)

    def test_render_home3(self):
        request = self.factory.get("/anything")

        response = views.home3(request)
        eq_(response.status_code, 200)
        ok_(re.findall("Random:\w+", response.content.decode("utf8")))
        random_string_1 = re.findall(
            "Random:(\w+)", response.content.decode("utf8")
        )[0]
        ok_("In your HTML" in response.content.decode("utf8"))
        extra_random_1 = re.findall(
            "In your HTML:(\w+)", response.content.decode("utf8")
        )[0]

        response = views.home3(request)
        eq_(response.status_code, 200)
        ok_(re.findall("Random:\w+", response.content.decode("utf8")))
        random_string_2 = re.findall(
            "Random:(\w+)", response.content.decode("utf8")
        )[0]
        extra_random_2 = re.findall(
            "In your HTML:(\w+)", response.content.decode("utf8")
        )[0]
        ok_("In your HTML" in response.content.decode("utf8"))
        eq_(random_string_1, random_string_2)
        # the post_process_response is only called once
        eq_(extra_random_1, extra_random_2)

    def test_render_home3_no_cache(self):
        factory = RequestFactory(AUTH_USER="peter")
        request = factory.get("/3")

        response = views.home3(request)
        eq_(response.status_code, 200)
        ok_(re.findall("Random:\w+", response.content.decode("utf8")))
        ok_("In your HTML" not in response.content.decode("utf8"))

    def test_render_home4(self):
        request = self.factory.get("/4")

        response = views.home4(request)
        eq_(response.status_code, 200)
        ok_(re.findall("Random:\w+", response.content.decode("utf8")))
        random_string_1 = re.findall(
            "Random:(\w+)", response.content.decode("utf8")
        )[0]
        ok_("In your HTML" in response.content.decode("utf8"))
        extra_random_1 = re.findall(
            "In your HTML:(\w+)", response.content.decode("utf8")
        )[0]

        response = views.home4(request)
        eq_(response.status_code, 200)
        ok_(re.findall("Random:\w+", response.content.decode("utf8")))
        random_string_2 = re.findall(
            "Random:(\w+)", response.content.decode("utf8")
        )[0]
        extra_random_2 = re.findall(
            "In your HTML:(\w+)", response.content.decode("utf8")
        )[0]
        ok_("In your HTML" in response.content.decode("utf8"))
        eq_(random_string_1, random_string_2)
        # the post_process_response is now called every time
        ok_(extra_random_1 != extra_random_2)

    def test_render_home5(self):
        request = self.factory.get("/4", {"foo": "bar"})
        response = views.home5(request)
        eq_(response.status_code, 200)
        ok_(re.findall("Random:\w+", response.content.decode("utf8")))
        random_string_1 = re.findall(
            "Random:(\w+)", response.content.decode("utf8")
        )[0]

        request = self.factory.get("/4", {"foo": "baz"})
        response = views.home5(request)
        eq_(response.status_code, 200)
        ok_(re.findall("Random:\w+", response.content.decode("utf8")))
        random_string_2 = re.findall(
            "Random:(\w+)", response.content.decode("utf8")
        )[0]
        ok_(random_string_1 != random_string_2)

        request = self.factory.get("/4", {"foo": "baz", "other": "junk"})
        response = views.home5(request)
        eq_(response.status_code, 200)
        ok_(re.findall("Random:\w+", response.content.decode("utf8")))
        random_string_3 = re.findall(
            "Random:(\w+)", response.content.decode("utf8")
        )[0]
        eq_(random_string_2, random_string_3)

    def test_render_home5bis(self):
        request = self.factory.get("/4", {"foo": "bar"})
        response = views.home5bis(request)
        eq_(response.status_code, 200)
        ok_(re.findall("Random:\w+", response.content.decode("utf8")))
        random_string_1 = re.findall(
            "Random:(\w+)", response.content.decode("utf8")
        )[0]

        request = self.factory.get("/4", {"foo": "baz"})
        response = views.home5bis(request)
        eq_(response.status_code, 200)
        ok_(re.findall("Random:\w+", response.content.decode("utf8")))
        random_string_2 = re.findall(
            "Random:(\w+)", response.content.decode("utf8")
        )[0]
        ok_(random_string_1 != random_string_2)

        request = self.factory.get("/4", {"foo": "baz", "bar": "foo"})
        response = views.home5bis(request)
        eq_(response.status_code, 200)
        ok_(re.findall("Random:\w+", response.content.decode("utf8")))
        random_string_3 = re.findall(
            "Random:(\w+)", response.content.decode("utf8")
        )[0]
        eq_(random_string_2, random_string_3)

    def test_remember_stats_all_urls(self):
        remembered_urls = cache.get(REMEMBERED_URLS_KEY)
        eq_(remembered_urls, None)
        request = self.factory.get("/anything")
        response = views.home6(request)
        eq_(response.status_code, 200)

        # now ask the memory thing
        (match,) = find_urls(urls=["/anything"])
        eq_(match[0], "/anything")
        eq_(match[2]["hits"], 0)
        eq_(match[2]["misses"], 1)

        remembered_urls = cache.get(REMEMBERED_URLS_KEY)
        eq_(len(remembered_urls.keys()), 1)
        eq_(list(remembered_urls.keys())[0], "/anything")
        cache_key = remembered_urls["/anything"][0]
        timeout = remembered_urls["/anything"][1]
        ok_(timeout > int(time.time()))

        # second time
        response = views.home6(request)
        eq_(response.status_code, 200)
        (match,) = find_urls(urls=["/anything"])
        eq_(match[0], "/anything")
        eq_(match[2]["hits"], 1)
        eq_(match[2]["misses"], 1)

        remembered_urls = cache.get(REMEMBERED_URLS_KEY)
        eq_(len(remembered_urls.keys()), 1)
        eq_(list(remembered_urls.keys())[0], "/anything")
        eq_(remembered_urls["/anything"][0], cache_key)
        eq_(remembered_urls["/anything"][1], timeout)
        ok_(timeout > int(time.time()))

    def test_remember_stats_all_urls_with_never_cache_decorator(self):
        request = self.factory.get("/anything")
        response = views.home9(request)
        eq_(response.status_code, 200)

        # now ask the memory thing
        (match,) = find_urls(urls=["/anything"])
        eq_(match[0], "/anything")
        eq_(match[2]["hits"], 0)
        eq_(match[2]["misses"], 1)

        # TODO: assert that the timeout was passed as expected.
        remembered_urls = cache.get(REMEMBERED_URLS_KEY)
        eq_(len(remembered_urls.keys()), 1)
        eq_(list(remembered_urls.keys())[0], "/anything")
        cache_key = remembered_urls["/anything"][0]
        timeout = remembered_urls["/anything"][1]
        ok_(timeout > int(time.time()))

        # second time
        response = views.home9(request)
        eq_(response.status_code, 200)
        (match,) = find_urls(urls=["/anything"])
        eq_(match[0], "/anything")
        eq_(match[2]["hits"], 1)
        eq_(match[2]["misses"], 1)

        remembered_urls = cache.get(REMEMBERED_URLS_KEY)
        eq_(len(remembered_urls.keys()), 1)
        eq_(list(remembered_urls.keys())[0], "/anything")
        eq_(remembered_urls["/anything"][0], cache_key)
        eq_(remembered_urls["/anything"][1], timeout)
        ok_(timeout > int(time.time()))

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
        eq_(response.status_code, 200)

        # now ask the memory thing
        (match,) = find_urls()
        ok_(match[0].startswith("/something/really"))
        eq_(match[2]["hits"], 0)
        eq_(match[2]["misses"], 1)

        # second time
        response = views.home6(request)
        eq_(response.status_code, 200)
        (match,) = find_urls([])
        ok_(match[0].startswith("/something/really"))
        eq_(match[2]["hits"], 1)
        eq_(match[2]["misses"], 1)

    def test_cache_backends(self):
        request = self.factory.get("/anything")

        response = views.home7(request)
        eq_(response.status_code, 200)
        ok_(re.findall("Random:\w+", response.content.decode("utf8")))
        random_string_1 = re.findall(
            "Random:(\w+)", response.content.decode("utf8")
        )[0]

        # clear second cache backend
        caches["second_backend"].clear()
        response = views.home7(request)
        eq_(response.status_code, 200)
        random_string_2 = re.findall(
            "Random:(\w+)", response.content.decode("utf8")
        )[0]
        ok_(random_string_1 != random_string_2)

    def test_cache_dummy_backend(self):
        """
        Test that the Dummy cache backend works as expected by not caching.
        """
        request = self.factory.get("/anything")

        response = views.home8(request)
        eq_(response.status_code, 200)
        ok_(re.findall("Random:\w+", response.content.decode("utf8")))
        random_string_1 = re.findall(
            "Random:(\w+)", response.content.decode("utf8")
        )[0]

        response = views.home8(request)
        eq_(response.status_code, 200)
        random_string_2 = re.findall(
            "Random:(\w+)", response.content.decode("utf8")
        )[0]
        ok_(random_string_1 != random_string_2)

        # Make sure clearing the dummy cache doesn't raise an error,
        # even though it should do nothing.
        caches["dummy_backend"].clear()

    @mock.patch("fancy_cache.middleware.USE_MEMCACHED_CAS", True)
    def test_cache_dummy_backend_with_memcached_check_and_set(self):
        """
        Test that the Dummy cache backend works as expected by not caching
        when FANCY_USE_MEMCACHED_CHECK_AND_SET is set to True.
        """
        request = self.factory.get("/anything")

        response = views.home8(request)
        eq_(response.status_code, 200)
        ok_(re.findall("Random:\w+", response.content.decode("utf8")))
        random_string_1 = re.findall(
            "Random:(\w+)", response.content.decode("utf8")
        )[0]

        response = views.home8(request)
        eq_(response.status_code, 200)
        random_string_2 = re.findall(
            "Random:(\w+)", response.content.decode("utf8")
        )[0]
        ok_(random_string_1 != random_string_2)

        # Make sure clearing the dummy cache doesn't raise an error,
        # even though it should do nothing.
        caches["dummy_backend"].clear()
