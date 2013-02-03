from django.conf.urls import patterns, include, url


urlpatterns = patterns(
    '',
    url(r'', include('example.app.urls')),
    url(r'fancy-cache', include('fancy_cache.urls')),
)
