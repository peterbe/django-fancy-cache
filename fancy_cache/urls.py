from django.conf.urls import patterns, url
from . import views


urlpatterns = patterns(
    'fancy-cache',
    url(r'^$', views.home, name='home'),
)
