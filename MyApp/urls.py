from django.urls import path
from .views import home, resources, Register, LoginView, logout_view, settings_page, update_profile_settings, \
    change_password, find_help, volunteer, unhoused, account_view, delete_account, update_email, update_role, dashboard_redirect, map

urlpatterns = [
    path("", home, name="home"),
    path("resources/", resources, name="resources"),
    path("register/", Register.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", logout_view, name="logout"),

    path("account/", account_view, name="account"),

    path("settings/", settings_page, name="settings"),
    path("settings/profile/", update_profile_settings, name="settings_profile"),
    path("settings/password/", change_password, name="settings_password"),
    path("settings/delete/", delete_account, name="delete_account"),
    path("settings/email/", update_email, name="settings_email"),
    path("settings/role/", update_role, name="settings_role"),
    path("find-help/", find_help, name="find_help"),
    path('volunteer/', volunteer, name='volunteer'),
    path('unhoused_dash/', unhoused, name='unhoused'),
    path("dashboard/", dashboard_redirect, name="dashboard_redirect"),
    path("map/", map, name="map")

]