from django.urls import include, path


urlpatterns = [
    path("", include("example.app.urls")),
    path("fancy-cache", include("fancy_cache.urls")),
]
