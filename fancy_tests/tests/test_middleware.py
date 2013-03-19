import re

from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings
from django.conf import settings
from django.core.cache import cache
from nose.tools import eq_, ok_

from fancy_cache.memory import find_urls
from fancy_cache.middleware import RequestPath
from . import views


class TestRequestPath(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.url = '/blog/?page=2&other=junk'
        self.request = self.factory.get(self.url)


    def test_request_get_full_path(self):
        """Test the patched request.get_full_path"""

        with RequestPath(self.request, ['page',]):
            path = self.request.get_full_path()
        self.assertEqual(path, '/blog/?page=2')

@override_settings(FANCY_CACHE_SETCACHE_KEY = '1234')
class TestRequestPathSetCache(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.url = '/blog/?page=2&other=junk&setcache=1234'
        self.request = self.factory.get(self.url)

    def test_request_get_full_path_setcache(self):
        """Test the patched request.get_full_path with setcache correctly set
        and that setcache works with only_get_keys
        """

        with RequestPath(self.request, ['page',]):
            path = self.request.get_full_path()
        self.assertEqual(path, '/blog/?page=2&setcache=1234')
        self.assertTrue(self.request._cache_update_cache)

@override_settings(FANCY_CACHE_SETCACHE_KEY = '1234')
class TestRequestPathSetCacheIncorrectly(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.url = '/blog/?page=2&other=junk&setcache=letmein'
        self.request = self.factory.get(self.url)

    def test_request_get_full_path_setcache_incorrectly(self):
        """Test the patched request.get_full_path with setcache incorrectly set"""

        with RequestPath(self.request, ['page',]):
            path = self.request.get_full_path()
        self.assertEqual(path, '/blog/?page=2')
        self.assertFalse(hasattr(self.request, '._cache_update_cache') \
                         and self.request._cache_update_cache)


@override_settings(FANCY_CACHE_SETCACHE_KEY = '1234')
class TestViewsWithSetCache(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def tearDown(self):
        cache.clear()

    def test_render_home_with_setcache(self):

        request = self.factory.get('/pardon/')
        response = views.home(request)
        eq_(response.status_code, 200)
        ok_(re.findall('Random:\w+', response.content))
        random_string_1 = re.findall('Random:(\w+)', response.content)[0]

        # punch a hole in the cache with setcache
        request2 = self.factory.get('/pardon/?setcache=1234')
        response = views.home(request2)
        eq_(response.status_code, 200)
        random_string_2 = re.findall('Random:(\w+)', response.content)[0]
        self.assertNotEqual(random_string_2, random_string_1)

        # do it again - should be cached
        request = self.factory.get('/pardon/')
        response = views.home(request)
        eq_(response.status_code, 200)
        random_string_3 = re.findall('Random:(\w+)', response.content)[0]
        eq_(random_string_2, random_string_3)

        self.assertNotEqual(random_string_3, random_string_1)













