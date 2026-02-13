from django.urls import path
from .views import home, resources

urlpatterns = [
    path("", home, name="home.html"),
    path("resources/", resources, name = "resources.html")
]