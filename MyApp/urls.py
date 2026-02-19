from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("find-help/", views.find_help, name="find_help"),
]