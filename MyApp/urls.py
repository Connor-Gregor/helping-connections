from django.urls import path
from .views import home, resources, Register, LoginView, logout_view, account_view
from . import views
from django.contrib.auth import views as auth_views
urlpatterns = [
    path("", home, name="home"),
    path("resources/", resources, name="resources"),
    path("register/", Register.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", logout_view, name="logout"),
    path("account/", views.account_view, name="account"),
]