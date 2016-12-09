from django.conf.urls import url



urlpatterns = [
    url(r'^$', 'fancy_cache.views.home', name='home'),
]
