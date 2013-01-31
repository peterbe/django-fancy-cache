from django.conf.urls import patterns, include, url
from . import views

urlpatterns = patterns(
    '',
    url(r'^$', views.home, name='home'),
    url(r'^page1.html$', views.page1, name='page1'),
    url(r'^page2.html$', views.page2, name='page2'),
    url(r'^page3.html$', views.page3, name='page3'),
    url(r'^page4.html$', views.page4, name='page4'),
    url(r'^page5.html$', views.page5, name='page5'),
)
