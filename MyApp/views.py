from django.db import IntegrityError
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from .forms import RegisterForm, LoginForm
from .models import Profile, Role
from django.contrib.auth.decorators import login_required


def home(request):
    return render(request, "home.html")

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

        try:
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password
            )
        except IntegrityError:
            form.add_error("email", "An account with this email already exists.")
            return render(request, "register.html", {"form": form})

        profile = Profile.objects.create(user=user)

        role, _ = Role.objects.get_or_create(name=role_name)
        profile.role = role
        profile.save()

        login(request, user)
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

        # Optional: force 5-min expiry from login time (absolute, not sliding)
        request.session.set_expiry(300)

        # Redirect based on role (simple version)
        role = getattr(user.profile, "role", None)
        if role and role.name == "volunteer":
            return redirect("resources")  # replace later with volunteer dashboard
        return redirect("home")

@login_required
def account_view(request):
    return render(request, "account.html")

@login_required
def logout_view(request):

    logout(request)

    return redirect("home")

