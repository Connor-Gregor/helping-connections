from django.urls import path
from .views import home, resources, Register, LoginView, logout_view, settings_page, update_profile_settings, change_password, find_help

urlpatterns = [
    path("", home, name="home"),
    path("resources/", resources, name="resources"),
    path("register/", Register.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", logout_view, name="logout"),
    path("settings/", settings_page, name="settings"),
    path("settings/profile/", update_profile_settings, name="settings_profile"),
    path("settings/password/", change_password, name="settings_password"),
    path("find-help/", find_help, name="find_help"),
]