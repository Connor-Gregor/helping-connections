from django.urls import path
from django.contrib.auth import views as auth_views
from .forms import CustomPasswordResetForm
from . import views

from .views import (
    home, resources, Register, LoginView, logout_view,
    settings_page, update_profile_settings, change_password,
    find_help, volunteer, unhoused, account_view,
    delete_account, update_email, update_role,
    dashboard_redirect, map, create_request,
    volunteer_requests, claim_request,
    about, create_offer, available_offers, claim_offer, my_offers,
    update_offer, delete_offer,
    VerifyEmailView, resend_verification_code, admin_dashboard, save_favorite, remove_favorite, favorite_locations, get_favorites
)

urlpatterns = [
    path("", home, name="home"),
    path("about/", about, name="about"),
    path("resources/", resources, name="resources"),

    # AUTH
    path("register/", Register.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", logout_view, name="logout"),

    # EMAIL VERIFICATION
    path("verify-email/", VerifyEmailView.as_view(), name="verify_email"),
    path("resend-verification-code/", resend_verification_code, name="resend_verification_code"),

    # PASSWORD RESET
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            form_class=CustomPasswordResetForm,
            template_name="password_reset_form.html",
            email_template_name="password_reset_email.html",
            subject_template_name="password_reset_subject.txt",
            success_url="/password-reset/done/",
        ),
        name="password_reset",
    ),

    # PASSWORD RESET
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        views.CustomPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),

    # ACCOUNT
    path("account/", account_view, name="account"),

    # SETTINGS
    path("settings/", settings_page, name="settings"),
    path("settings/profile/", update_profile_settings, name="settings_profile"),
    path("settings/password/", change_password, name="settings_password"),
    path("settings/delete/", delete_account, name="delete_account"),
    path("settings/email/", update_email, name="settings_email"),
    path("settings/email/verify/", views.VerifyEmailChangeView.as_view(), name="verify_email_change"),
    path("settings/email/resend/", views.resend_email_change_code, name="resend_email_change_code"),
    path("settings/role/", update_role, name="settings_role"),
    path("dashboard-admin/accounts/<int:profile_id>/update/", views.admin_update_account, name="admin_update_account"),
    path("dashboard-admin/accounts/<int:profile_id>/delete/", views.admin_delete_account, name="admin_delete_account"),

    # DASHBOARD / NAVIGATION
    path("find-help/", find_help, name="find_help"),
    path("volunteer/", volunteer, name="volunteer"),
    path("unhoused_dash/", unhoused, name="unhoused"),
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("dashboard/", dashboard_redirect, name="dashboard_redirect"),
    path("map/", map, name="map"),
    

    # REQUESTS
    path("requests/create/", create_request, name="create_request"),
    path("requests/", volunteer_requests, name="volunteer_requests"),
    path("requests/claim/<int:request_id>/", claim_request, name="claim_request"),
    path("requests/<int:request_id>/update/", views.update_request, name="update_request"),
    path("requests/<int:request_id>/delete/", views.delete_request, name="delete_request"),
    path("requests/<int:request_id>/verify/", views.verify_request, name="verify_request"),
    path("requests/<int:request_id>/withdraw/", views.withdraw_claimed_request, name="withdraw_claimed_request"),

    # OFFERS
    path("offers/create/", create_offer, name="create_offer"),
    path("offers/", available_offers, name="available_offers"),
    path("offers/<int:offer_id>/claim/", claim_offer, name="claim_offer"),
    path("offers/<int:offer_id>/update/", update_offer, name="update_offer"),
    path("offers/<int:offer_id>/delete/", delete_offer, name="delete_offer"),
    path("offers/<int:offer_id>/verify/", views.verify_offer, name="verify_offer"),
    path("offers/mine/", my_offers, name="my_offers"),
    path("history/", views.history_view, name="history"), 
       
    # REPORT
    path("offers/report/", views.create_offer_report, name="create_offer_report"),
    path("reports/requests/create/", views.create_request_report, name="create_request_report"),
    
    path("favorites/save/", save_favorite, name="save_favorite"),
    path("favorites/remove/", remove_favorite, name="remove_favorite"),
    path("favorites/", favorite_locations, name="favorite_locations"),
    path("favorites/list/", get_favorites, name="get_favorites"),
]
