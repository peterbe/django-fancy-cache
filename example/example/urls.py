from django.urls import patterns, include, path


urlpatterns = patterns(
    "",
    path("", include("example.app.urls")),
    path("fancy-cache", include("fancy_cache.urls")),
)
