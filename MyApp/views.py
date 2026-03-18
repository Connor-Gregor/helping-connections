from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.views.decorators.http import require_POST

from .forms import RegisterForm, LoginForm, ChangePasswordForm, ProfileSettingsForm, DeleteAccountForm, EmailChangeForm, \
    RoleChangeForm, RequestForm, OfferForm
from .models import Profile, Role, Request, Offer
from django.conf import settings


def home(request):
    return render(request, "home.html")


def map(request):
    return render(request, "map.html", {
        "google_maps_api_key": settings.GOOGLE_MAPS_API_KEY
    })


def find_help(request):
    return render(request, "find_help.html")


def resources(request):
    return render(request, "resources.html")


def about(request):
    return render(request, "about.html")


@login_required
def account_view(request):
    profile = getattr(request.user, "profile", None)
    return render(request, "account.html", {"profile": profile})


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
        first_name = form.cleaned_data["first_name"]
        last_name = form.cleaned_data["last_name"]
        phone_number = form.cleaned_data.get("phone_number", "")
        address_line1 = form.cleaned_data["address_line1"]
        address_line2 = form.cleaned_data.get("address_line2", "")
        city = form.cleaned_data["city"]
        state = form.cleaned_data["state"]
        zip_code = form.cleaned_data["zip_code"]

        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                )

                role, _ = Role.objects.get_or_create(name=role_name)

                profile, _ = Profile.objects.get_or_create(user=user)
                profile.role = role
                profile.display_username = display_username
                profile.phone_number = phone_number
                profile.address_line1 = address_line1
                profile.address_line2 = address_line2
                profile.city = city
                profile.state = state
                profile.zip_code = zip_code
                profile.save()

        except IntegrityError:
            form.add_error("email", "An account with this email or username already exists.")
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

    request.user.first_name = form.cleaned_data.get("first_name", "").strip()
    request.user.last_name = form.cleaned_data.get("last_name", "").strip()
    request.user.save()

    profile.display_username = form.cleaned_data["display_username"].strip()
    profile.phone_number = form.cleaned_data.get("phone_number", "").strip()
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
                "first_name": request.user.first_name or "",
                "last_name": request.user.last_name or "",
                "address_line1": getattr(profile, "address_line1", "") or "",
                "address_line2": getattr(profile, "address_line2", "") or "",
                "city": getattr(profile, "city", "") or "",
                "state": getattr(profile, "state", "") or "",
                "zip_code": getattr(profile, "zip_code", "") or "",
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

@login_required
def create_offer(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        messages.error(request, "You must have a profile to create an offer.")
        return redirect("home")

    if profile.role is None or profile.role.name.lower() != "volunteer":
        messages.error(request, "Only volunteers can create offers.")
        return redirect("home")

    if request.method == "POST":
        form = OfferForm(request.POST)
        if form.is_valid():
            offer = form.save(commit=False)
            offer.offered_by = profile
            offer.status = Offer.STATUS_OPEN
            offer.save()

            messages.success(request, "Your offer was submitted successfully.")
            return redirect("create_offer")
    else:
        form = OfferForm()

    return render(request, "create_offer.html", {"form": form})

@login_required
def available_offers(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        messages.error(request, "You must have a profile to view offers.")
        return redirect("home")

    if profile.role is None or profile.role.name.lower() != "unhoused":
        messages.error(request, "Only unhoused users can view offers.")
        return redirect("home")

    offers = Offer.objects.filter(status=Offer.STATUS_OPEN)

    return render(request, "available_offers.html", {
        "offers": offers
    })

@login_required
@require_POST
def claim_offer(request, offer_id):
    profile = request.user.profile

    if profile.role is None or profile.role.name.lower() != "unhoused":
        messages.error(request, "Only unhoused users can claim offers.")
        return redirect("home")

    offer = get_object_or_404(Offer, id=offer_id)

    if offer.status != Offer.STATUS_OPEN:
        messages.error(request, "This offer has already been claimed.")
        return redirect("available_offers")

    offer.status = Offer.STATUS_CLAIMED
    offer.claimed_by = profile
    offer.save()

    messages.success(request, "You have claimed this offer.")
    return redirect("available_offers")

@login_required
def my_offers(request):
    profile = request.user.profile

    if profile.role is None or profile.role.name.lower() != "volunteer":
        messages.error(request, "Only volunteers can view their offers.")
        return redirect("home")

    offers = Offer.objects.filter(offered_by=profile)

    return render(request, "my_offers.html", {
        "offers": offers
    })