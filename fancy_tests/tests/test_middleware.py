from django.core.cache import caches
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase
from django.views.decorators.cache import cache_page as django_cache_page

from fancy_cache.middleware import (
    FancyFetchFromCacheMiddleware,
    FancyUpdateCacheMiddleware,
)


def plain_view(request):
    return HttpResponse("ok")


class TestDjangoCacheMiddlewareCompatibility(SimpleTestCase):
    """
    Projects often use Django's own cache_page next to fancy_cache's, so
    importing fancy_cache must not change Django's cache middleware classes.
    """

    def test_django_cache_page_works_after_importing_fancy_cache(self):
        view = django_cache_page(60)(plain_view)
        response = view(RequestFactory().get("/plain-django-cache-page/"))
        self.assertEqual(response.status_code, 200)

    def test_standalone_middleware_uses_the_default_cache(self):
        update_middleware = FancyUpdateCacheMiddleware(plain_view)
        fetch_middleware = FancyFetchFromCacheMiddleware(plain_view)
        self.assertIs(update_middleware.cache, caches["default"])
        self.assertIs(fetch_middleware.cache, caches["default"])
