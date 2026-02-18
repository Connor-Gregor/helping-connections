from django.db import IntegrityError
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from .forms import RegisterForm, LoginForm
from .models import Profile, Role



def home(request):
    return render(request, "home.html")

def resources(request):
    return render(request, "resources.html")

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

def logout_view(request):
    logout(request)
    return redirect("home")
