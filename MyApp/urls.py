from django.urls import path
from .views import home, resources, Register, LoginView, logout_view

urlpatterns = [
    path("", home, name="home"),
    path("resources/", resources, name="resources"),
    path("register/", Register.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", logout_view, name="logout"),
]