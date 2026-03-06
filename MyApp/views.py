from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from .forms import RegisterForm, LoginForm, ChangePasswordForm, ProfileSettingsForm, DeleteAccountForm, EmailChangeForm, RoleChangeForm
from .models import Profile, Role
from django.conf import settings


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
                username=email,   # keep this as email so your login flow stays the same
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
            return redirect("home")  # fallback

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

        # Optional: force 5-min expiry from login time (absolute, not sliding)
        request.session.set_expiry(300)

        # Redirect based on role (simple version)
        role = getattr(user.profile, "role", None)
        if role and role.name == "volunteer":
            return redirect("volunteer")  # replace later with volunteer dashboard
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
            "first_name": request.user.first_name or "",
            "last_name": request.user.last_name or "",
            "address_line1": getattr(profile, "address_line1", "") or "",
            "address_line2": getattr(profile, "address_line2", "") or "",
            "city": getattr(profile, "city", "") or "",
            "state": getattr(profile, "state", "") or "",
            "zip_code": getattr(profile, "zip_code", "") or "",

        }
    )
    email_form = EmailChangeForm(
        user=request.user,
        initial={"email": request.user.email or ""}
    )

    role_form = RoleChangeForm(
        allowed_roles=["unhoused", "volunteer"],
        initial={"role": profile.role.name if profile.role else "unhoused"}
    )

    password_form = ChangePasswordForm(user=request.user)
    delete_form = DeleteAccountForm(user=request.user)

    return render(request, "settings.html", {
        "profile_form": profile_form,
        "email_form": email_form,
        "role_form": role_form,
        "password_form": password_form,
        "delete_form": delete_form,
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
    # Save field on User
    request.user.first_name = form.cleaned_data.get("first_name", "").strip()
    request.user.last_name = form.cleaned_data.get("last_name", "").strip()
    request.user.save()
    # Save fields on Profile
    profile.display_username = form.cleaned_data["display_username"].strip()
    profile.phone_number = form.cleaned_data.get("phone_number", "").strip()
    # Save address on User
    if "address_line1" in form.cleaned_data:
        profile.address_line1 = form.cleaned_data.get("address_line1", "").strip()
        profile.address_line2 = form.cleaned_data.get("address_line2", "").strip()
        profile.city = form.cleaned_data.get("city", "").strip()
        profile.state = form.cleaned_data.get("state", "").strip()
        profile.zip_code = form.cleaned_data.get("zip_code", "").strip()

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

    # Keep them logged in after password change
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
    logout(request) # clear session first
    user.delete()   # remove user from database

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
