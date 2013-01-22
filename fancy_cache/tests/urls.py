from django.conf.urls.defaults import include, patterns, url
from . import views


urlpatterns = patterns('',
    url(r'^$', views.home, name='home'),
    url(r'^2$', views.home2, name='home2'),
    url(r'^3$', views.home3, name='home3'),
)
