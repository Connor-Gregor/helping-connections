from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from .forms import RegisterForm, LoginForm, ChangePasswordForm, ProfileSettingsForm
from .models import Profile, Role


def home(request):
    return render(request, "home.html")

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
            profile = Profile.objects.create(
                user=user,
                role=role,
                display_username=display_username,
                phone_number=phone_number or ""
            )
        except IntegrityError:
            # this is most likely display_username duplicate
            user.delete()  # cleanup, since profile creation failed
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