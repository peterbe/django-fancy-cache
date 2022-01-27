from django.urls import re_path
from . import views


urlpatterns = [
    re_path(r"^$", views.home, name="home"),
    # re_path(r'^2$', views.home2, name='home2'),
    # re_path(r'^3$', views.home3, name='home3'),
]
