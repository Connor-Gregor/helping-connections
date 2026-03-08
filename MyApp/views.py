from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.views.decorators.http import require_POST

from config import settings
from .forms import (
    RegisterForm, LoginForm, ChangePasswordForm, ProfileSettingsForm,
    DeleteAccountForm, EmailChangeForm, RoleChangeForm, RequestForm
)
from .models import Profile, Role, Request


def home(request):
    return render(request, "home.html")

def map(request):
    return render(request,"map.html", {
        "google_maps_api_key": settings.GOOGLE_MAPS_API_KEY
    })

def find_help(request):
    return render(request, "find_help.html")


def resources(request):
    return render(request, "resources.html")


@login_required
def account_view(request):
    return render(request, "account.html")


class Register(View):
    def get(self, request):
        form = RegisterForm()
        return render(request, "register.html", {"form": form})

    def post(self, request):
        form = RegisterForm(request.POST)

        if not form.is_valid():
            return render(request, "register.html", {"form": form})

        email = form.cleaned_data["email"]
        password = form.cleaned_data["password1"]
        role_name = form.cleaned_data["role"]

        display_username = form.cleaned_data["display_username"]
        phone_number = form.cleaned_data.get("phone_number", "")

        try:
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password
            )
        except IntegrityError:
            form.add_error("email", "An account with this email already exists.")
            return render(request, "register.html", {"form": form})

        role, _ = Role.objects.get_or_create(name=role_name)

        try:
            with transaction.atomic():
                profile, _ = Profile.objects.get_or_create(user=user)
                profile.role = role
                profile.display_username = display_username
                profile.phone_number = phone_number or ""
                profile.save()
        except IntegrityError:
            user.delete()
            form.add_error("display_username", "That username is already taken.")
            return render(request, "register.html", {"form": form})

        login(request, user)
        if profile.role.name == "volunteer":
            return redirect("volunteer")
        elif profile.role.name == "unhoused":
            return redirect("unhoused")
        else:
            return redirect("home")


class LoginView(View):
    def get(self, request):
        form = LoginForm()
        return render(request, "login.html", {"form": form})

    def post(self, request):
        form = LoginForm(request.POST)
        if not form.is_valid():
            return render(request, "login.html", {"form": form})

        email = form.cleaned_data["email"]
        password = form.cleaned_data["password"]

        user = authenticate(request, username=email, password=password)
        if user is None:
            form.add_error(None, "Invalid email or password.")
            return render(request, "login.html", {"form": form})

        login(request, user)
        request.session.set_expiry(300)

        role = getattr(user.profile, "role", None)
        if role and role.name == "volunteer":
            return redirect("volunteer")
        elif role and role.name == "unhoused":
            return redirect("unhoused")
        return redirect("home")


def logout_view(request):
    logout(request)
    return redirect("home")


@login_required
def settings_page(request):
    profile = Profile.objects.get(user=request.user)

    profile_form = ProfileSettingsForm(
        profile=profile,
        initial={
            "display_username": profile.display_username or "",
            "phone_number": profile.phone_number or "",
        }
    )
    password_form = ChangePasswordForm(user=request.user)

    return render(request, "settings.html", {
        "profile_form": profile_form,
        "password_form": password_form,
    })


@login_required
def update_profile_settings(request):
    if request.method != "POST":
        return redirect("settings")

    profile = Profile.objects.get(user=request.user)
    form = ProfileSettingsForm(request.POST, profile=profile)

    if not form.is_valid():
        password_form = ChangePasswordForm(user=request.user)
        return render(request, "settings.html", {
            "profile_form": form,
            "password_form": password_form,
        })

    profile.display_username = form.cleaned_data["display_username"]
    profile.phone_number = form.cleaned_data.get("phone_number", "")
    profile.save()

    messages.success(request, "Profile updated.")
    return redirect("settings")


@login_required
def change_password(request):
    if request.method != "POST":
        return redirect("settings")

    profile = Profile.objects.get(user=request.user)
    form = ChangePasswordForm(request.POST, user=request.user)

    if not form.is_valid():
        profile_form = ProfileSettingsForm(
            profile=profile,
            initial={
                "display_username": profile.display_username or "",
                "phone_number": profile.phone_number or "",
            }
        )
        return render(request, "settings.html", {
            "profile_form": profile_form,
            "password_form": form,
        })

    new_pw = form.cleaned_data["new_password1"]
    request.user.set_password(new_pw)
    request.user.save()
    update_session_auth_hash(request, request.user)

    messages.success(request, "Password changed.")
    return redirect("settings")


@login_required
def volunteer(request):
    role = getattr(request.user.profile, "role", None)
    if role and role.name == "volunteer":
        return render(request, "volunteer.html")
    return redirect("home")


@login_required
def unhoused(request):
    role = getattr(request.user.profile, "role", None)
    if role and role.name == "unhoused":
        return render(request, "unhoused_dash.html")
    return redirect("home")


def get_dashboard_url(user):
    role = user.profile.role.name.lower() if user.profile.role else None

    if role == "volunteer":
        return "volunteer"
    elif role == "unhoused":
        return "unhoused"

    return "home"


@login_required
def dashboard_redirect(request):
    return redirect(get_dashboard_url(request.user))


@login_required
def delete_account(request):
    if request.method != "POST":
        return redirect("settings")

    form = DeleteAccountForm(request.POST, user=request.user)

    if not form.is_valid():
        messages.error(request, "Could not delete account.")
        return redirect("settings")

    user = request.user
    logout(request)
    user.delete()

    messages.success(request, "Your account has been deleted.")
    return redirect("home")


@login_required
def update_email(request):
    if request.method != "POST":
        return redirect("settings")

    form = EmailChangeForm(request.POST, user=request.user)

    if not form.is_valid():
        messages.error(request, "Could not update email.")
        return redirect("settings")

    new_email = form.cleaned_data["email"]
    request.user.email = new_email
    request.user.username = new_email
    request.user.save()

    messages.success(request, "Email updated.")
    return redirect("settings")


@login_required
def update_role(request):
    if request.method != "POST":
        return redirect("settings")

    allowed = ["volunteer", "unhoused"]
    form = RoleChangeForm(request.POST, allowed_roles=allowed)

    if not form.is_valid():
        messages.error(request, "Invalid role.")
        return redirect("settings")

    profile = Profile.objects.get(user=request.user)

    new_role_name = form.cleaned_data["role"]
    role_obj, _ = Role.objects.get_or_create(name=new_role_name)
    profile.role = role_obj
    profile.save()

    messages.success(request, "Role updated.")
    return redirect("settings")


@login_required
def create_request(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        messages.error(request, "You must have a profile to create a request.")
        return redirect("home")

    if profile.role is None or profile.role.name.lower() != "unhoused":
        messages.error(request, "Only unhoused users can create requests.")
        return redirect("home")

    if request.method == "POST":
        form = RequestForm(request.POST)
        if form.is_valid():
            new_request = form.save(commit=False)
            new_request.requester = profile
            new_request.status = Request.STATUS_OPEN
            new_request.save()

            messages.success(request, "Your request was submitted successfully.")
            return redirect("create_request")
    else:
        form = RequestForm()

    return render(request, "create_request.html", {"form": form})


@login_required
def volunteer_requests(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        messages.error(request, "You must have a profile to view requests.")
        return redirect("home")

    if profile.role is None or profile.role.name.lower() != "volunteer":
        messages.error(request, "Only volunteers can view requests.")
        return redirect("home")

    requests = Request.objects.filter(status=Request.STATUS_OPEN)

    return render(request, "volunteer_requests.html", {
        "requests": requests
    })


@login_required
@require_POST
def claim_request(request, request_id):
    profile = request.user.profile

    if profile.role is None or profile.role.name.lower() != "volunteer":
        messages.error(request, "Only volunteers can claim requests.")
        return redirect("home")

    req = get_object_or_404(Request, id=request_id)

    if req.status != Request.STATUS_OPEN:
        messages.error(request, "This request has already been claimed.")
        return redirect("volunteer_requests")

    req.status = Request.STATUS_CLAIMED
    req.claimed_by = profile
    req.save()

    messages.success(request, "You have claimed this request.")
    return redirect("volunteer_requests")