from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("page1.html", views.page1, name="page1"),
    path("page2.html", views.page2, name="page2"),
    path("page3.html", views.page3, name="page3"),
    path("page4.html", views.page4, name="page4"),
    path("page5.html", views.page5, name="page5"),
]
