from django.urls import patterns, include, re_path
from . import views

urlpatterns = patterns(
    "",
    re_path(r"^$", views.home, name="home"),
    re_path(r"^page1.html$", views.page1, name="page1"),
    re_path(r"^page2.html$", views.page2, name="page2"),
    re_path(r"^page3.html$", views.page3, name="page3"),
    re_path(r"^page4.html$", views.page4, name="page4"),
    re_path(r"^page5.html$", views.page5, name="page5"),
)
