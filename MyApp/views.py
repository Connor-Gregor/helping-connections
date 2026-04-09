from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import views as auth_views
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse
from django.core.paginator import Paginator
from messaging.services import send_system_dm

from .forms import (
    RegisterForm,
    LoginForm,
    ChangePasswordForm,
    ProfileSettingsForm,
    DeleteAccountForm,
    EmailChangeForm,
    RoleChangeForm,
    RequestForm,
    OfferForm,
    AdminAccountEditForm,
)
from .models import (
    Profile,
    Role,
    Request,
    Offer,
    OfferImage,
    EmailVerificationCode,
    OfferReport,
    RequestReport,
)
from django.conf import settings
from .utils import generate_verification_code, send_verification_email


# =========================================
# Helping Connections - Views
# =========================================
# This file handles all main application logic, including:
# - Authentication (register, login, verification)
# - Profile & settings management
# - Role-based dashboards (volunteer / unhoused)
# - Requests & Offers workflows (create, update, claim, delete)
# - Reporting system (offers + requests)
#
# NOTE:
# - Role-based access is enforced in many views
# - Messaging/redirect feedback is handled using Django messages
# - Most forms are validated in forms.py before saving


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

# Handles user registration + email verification setup.
# Flow:
# 1. Validate form
# 2. Create inactive user (is_active=False)
# 3. Create Profile + assign role
# 4. Generate verification code
# 5. Send email
# 6. Store user ID in session for verification step
#
# Uses transaction.atomic() to ensure everything is created safely.


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
                    is_active=False,
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

                code = generate_verification_code()

                EmailVerificationCode.objects.create(
                    user=user,
                    code=code,
                    expires_at=timezone.now() + timedelta(minutes=10)
                )

                send_verification_email(user, code)

        except IntegrityError:
            form.add_error("email", "An account with this email or username already exists.")
            return render(request, "register.html", {"form": form})

        except Exception:
            form.add_error(None, "Account was created, but the verification email could not be sent. Please try again.")
            return render(request, "register.html", {"form": form})

        request.session["pending_verification_user_id"] = user.id
        messages.success(request, "Account created. Please check your email for the verification code.")
        return redirect("verify_email")

# Handles email verification after registration.
# Uses session-stored user ID to identify which account to verify.
#
# Logic:
# - Fetch latest unverified code
# - Check expiration
# - Match user input
# - Activate user + log them in
#
# Redirects user based on role after successful verification.


class VerifyEmailView(View):
    def get(self, request):
        user_id = request.session.get("pending_verification_user_id")

        if not user_id:
            messages.error(request, "No account is waiting for verification.")
            return redirect("register")

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect("register")

        return render(request, "verify_email.html", {"email": user.email})

    def post(self, request):
        user_id = request.session.get("pending_verification_user_id")

        if not user_id:
            messages.error(request, "No account is waiting for verification.")
            return redirect("register")

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect("register")

        entered_code = request.POST.get("code", "").strip()

        verification = (
            EmailVerificationCode.objects
                .filter(user=user, verified=False)
                .order_by("-created_at")
                .first()
        )

        if not verification:
            messages.error(request, "No verification code found. Please request a new one.")
            return redirect("verify_email")

        if verification.is_expired():
            messages.error(request, "This verification code has expired.")
            return redirect("verify_email")

        if verification.code != entered_code:
            messages.error(request, "Invalid verification code.")
            return redirect("verify_email")

        verification.verified = True
        verification.save()

        user.is_active = True
        user.save()

        request.session.pop("pending_verification_user_id", None)
        login(request, user)

        messages.success(request, "Email verified successfully. Welcome to Helping Connections!")

        role = getattr(user.profile, "role", None)
        if role and role.name == "admin":
            return redirect("admin_dashboard")
        elif role and role.name == "volunteer":
            return redirect("volunteer")
        elif role and role.name == "unhoused":
            return redirect("unhoused")
        return redirect("home")


class VerifyEmailChangeView(View):
    def get(self, request):
        pending_email = request.session.get("pending_new_email")

        if not pending_email:
            messages.error(request, "No email change request found.")
            return redirect("settings")

        return render(request, "verify_email_change.html", {
            "email": pending_email
        })

    def post(self, request):
        pending_email = request.session.get("pending_new_email")

        if not pending_email:
            messages.error(request, "No email change request found.")
            return redirect("settings")

        entered_code = request.POST.get("code", "").strip()

        verification = (
            EmailVerificationCode.objects
                .filter(user=request.user, verified=False)
                .order_by("-created_at")
                .first()
        )

        if not verification:
            messages.error(request, "No verification code found.")
            return redirect("verify_email_change")

        if verification.is_expired():
            messages.error(request, "Verification code expired.")
            return redirect("verify_email_change")

        if verification.code != entered_code:
            messages.error(request, "Invalid verification code.")
            return redirect("verify_email_change")

        verification.verified = True
        verification.save()

        # UPDATE happens here
        request.user.email = pending_email
        request.user.username = pending_email
        request.user.save()

        request.session.pop("pending_new_email", None)
        request.session.pop("last_email_change_verification_sent", None)

        messages.success(request, "Email updated successfully.")
        return redirect(f"{reverse('settings')}?tab=security-tab")

# Allows user to request a new verification code.
#
# Includes:
# - 30-second cooldown (prevents spam)
# - Marks previous codes as used
# - Generates and sends new code
# - Stores timestamp in session

def resend_verification_code(request):
    # Get the user ID from session (set during registration)
    user_id = request.session.get("pending_verification_user_id")

    if not user_id:
        messages.error(request, "No account is waiting for verification.")
        return redirect("register")

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect("register")

    # COOLDOWN CHECK (30 seconds)

    last_sent = request.session.get("last_verification_sent")

    if last_sent:
        last_sent_time = timezone.datetime.fromisoformat(last_sent)

        # If 30 seconds hasn't passed yet → block resend
        if timezone.now() < last_sent_time + timedelta(seconds=30):
            remaining = int(
                (last_sent_time + timedelta(seconds=30) - timezone.now()).total_seconds()
            )
            messages.error(request, f"Please wait {remaining}s before requesting another code.")
            return redirect("verify_email")

    # Mark all previous unverified codes as "used"
    EmailVerificationCode.objects.filter(user=user, verified=False).update(verified=True)

    # Generate new code

    code = generate_verification_code()

    EmailVerificationCode.objects.create(
        user=user,
        code=code,
        expires_at=timezone.now() + timedelta(minutes=10)  # expires in 10 min
    )

    # send email

    send_verification_email(user, code)

    # Save cooldown timestamp

    request.session["last_verification_sent"] = timezone.now().isoformat()

    # Success message
    messages.success(request, "A new verification code was sent to your email.")
    return redirect("verify_email")


class CustomPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = "password_reset_confirm.html"
    success_url = "/reset/done/"

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, error)
        return self.render_to_response(self.get_context_data(form=form))

# Handles user login.
#
# Special behavior:
# - If account exists but is not verified → redirect to verification
# - Session expires after 5 minutes (security)
# - Redirects user based on role after login

class LoginView(View):
    def get(self, request):
        form = LoginForm()
        return render(request, "login.html", {"form": form})

    def post(self, request):
        form = LoginForm(request.POST)

        if not form.is_valid():
            messages.error(request, "Please enter a valid email and password.")
            return render(request, "login.html", {"form": form})

        email = form.cleaned_data["email"].strip().lower()
        password = form.cleaned_data["password"]

        try:
            existing_user = User.objects.get(username__iexact=email)

            if not existing_user.is_active:
                request.session["pending_verification_user_id"] = existing_user.id
                messages.warning(
                    request,
                    "Your account has not been verified yet. Please enter the verification code sent to your email."
                )
                return redirect("verify_email")

        except User.DoesNotExist:
            pass

        user = authenticate(request, username=email, password=password)
        if user is None:
            messages.error(request, "Invalid email or password.")
            return render(request, "login.html", {"form": form})

        login(request, user)
        request.session.set_expiry(300)

        role = getattr(user.profile, "role", None)
        if role and role.name == "admin":
            return redirect("admin_dashboard")
        elif role and role.name == "volunteer":
            return redirect("volunteer")
        elif role and role.name == "unhoused":
            return redirect("unhoused")
        return redirect("home")


def logout_view(request):
    logout(request)
    return redirect("home")


# This helper formats stored 10-digit phone numbers for display in the settings form.
# The form can store digits only in the database, but users still see a clean U.S. format.
def format_phone_number(phone):
    if not phone:
        return ""

    digits = "".join(filter(str.isdigit, phone))

    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"

    return phone

# Helper function to build consistent context for settings page.
# Ensures all forms (profile, email, password, role, delete) are always available.
#
# This prevents duplication across settings views and keeps UI consistent.

def build_settings_context(request, *, profile_form=None, email_form=None,
                           password_form=None, role_form=None,
                           delete_form=None, active_tab="profile-tab"):
    profile = Profile.objects.get(user=request.user)

    if profile_form is None:
        profile_form = ProfileSettingsForm(
            profile=profile,
            initial={
                "display_username": profile.display_username,
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
                "phone_number": format_phone_number(profile.phone_number),
                "address_line1": profile.address_line1,
                "address_line2": profile.address_line2,
                "city": profile.city,
                "state": profile.state,
                "zip_code": profile.zip_code,
            }
        )

    if email_form is None:
        email_form = EmailChangeForm(
            user=request.user,
            initial={"email": request.user.email}
        )

    if password_form is None:
        password_form = ChangePasswordForm(user=request.user)

    if role_form is None:
        role_form = RoleChangeForm(
            allowed_roles=["unhoused", "volunteer"],
            initial={"role": profile.role.name if profile.role else ""}
        )

    if delete_form is None:
        delete_form = DeleteAccountForm(user=request.user)

    return {
        "profile_form": profile_form,
        "email_form": email_form,
        "password_form": password_form,
        "role_form": role_form,
        "delete_form": delete_form,
        "active_tab": active_tab,
    }


@login_required
def settings_page(request):
    active_tab = request.GET.get("tab", "profile-tab")
    context = build_settings_context(request, active_tab=active_tab)
    return render(request, "settings.html", context)


@login_required
def update_profile_settings(request):
    if request.method != "POST":
        return redirect("settings")

    profile = Profile.objects.get(user=request.user)
    form = ProfileSettingsForm(request.POST, request.FILES, profile=profile)

    if not form.is_valid():
        for field, errors in form.errors.items():
            for error in errors:
                if field == "__all__":
                    messages.error(request, error)
                else:
                    label = form.fields[field].label or field.replace("_", " ").title()
                    messages.error(request, f"{label}: {error}")

        return redirect(f"{reverse('settings')}?tab=profile-tab")

    request.user.first_name = form.cleaned_data.get("first_name", "").strip()
    request.user.last_name = form.cleaned_data.get("last_name", "").strip()
    request.user.save()

    profile.display_username = form.cleaned_data["display_username"].strip()
    profile.phone_number = form.cleaned_data.get("phone_number", "")
    profile.address_line1 = form.cleaned_data.get("address_line1", "").strip()
    profile.address_line2 = form.cleaned_data.get("address_line2", "").strip()
    profile.city = form.cleaned_data.get("city", "").strip()
    profile.state = form.cleaned_data.get("state", "").strip()
    profile.zip_code = form.cleaned_data.get("zip_code", "").strip()

    if form.cleaned_data.get("profile_photo"):
        profile.profile_photo = form.cleaned_data["profile_photo"]

    profile.save()

    messages.success(request, "Profile updated.")
    return redirect("settings")


@login_required
def change_password(request):
    if request.method != "POST":
        return redirect("settings")

    form = ChangePasswordForm(request.POST, user=request.user)

    if not form.is_valid():
        for field, errors in form.errors.items():
            for error in errors:
                if field == "__all__":
                    messages.error(request, error)
                else:
                    label = form.fields[field].label or field.replace("_", " ").title()
                    messages.error(request, f"{label}: {error}")

        return redirect(f"{reverse('settings')}?tab=security-tab")

    request.user.set_password(form.cleaned_data["new_password1"])
    request.user.save()

    messages.success(request, "Password changed successfully.")
    return redirect("login")

# Volunteer dashboard view.
#
# Displays active volunteer-side work in two sections:
# - accepted_requests: requests claimed by this volunteer
# - accepted_offers: offers created by this volunteer that were claimed
#
# accepted_requests excludes self-owned requests so the volunteer dashboard
# only shows real requester/volunteer pairings and avoids self-message cases.
# This gives volunteers one place to track both sides of their current activity
# without changing the existing request/offer workflows.

@login_required
def volunteer(request):
    role = getattr(request.user.profile, "role", None)
    if role and role.name == "volunteer":
        profile = request.user.profile
        active_tab = request.GET.get("tab", "accepted-requests-tab")
        offers_view = request.GET.get("offers_view", "accepted")

        available_requests_list = Request.objects.filter(
            status=Request.STATUS_OPEN
        ).exclude(
            requester=profile
        ).order_by("-created_at")

        available_requests_total = available_requests_list.count()
        available_requests_paginator = Paginator(available_requests_list, 9)
        available_requests_page_number = request.GET.get("available_page")
        available_requests = available_requests_paginator.get_page(available_requests_page_number)

        accepted_requests_list = Request.objects.filter(
            claimed_by=profile,
            status=Request.STATUS_CLAIMED
        ).exclude(
            requester=profile
        ).order_by("-claimed_at", "-created_at")

        accepted_requests_total = accepted_requests_list.count()
        accepted_requests_paginator = Paginator(accepted_requests_list, 9)
        accepted_requests_page_number = request.GET.get("accepted_page")
        accepted_requests = accepted_requests_paginator.get_page(accepted_requests_page_number)

        accepted_offers_list = Offer.objects.filter(
            offered_by=profile,
            status=Offer.STATUS_CLAIMED
        ).prefetch_related("images").order_by("-claimed_at", "-created_at")

        accepted_offers_paginator = Paginator(accepted_offers_list, 9)
        accepted_offers_page_number = request.GET.get("accepted_offers_page")
        accepted_offers = accepted_offers_paginator.get_page(accepted_offers_page_number)
        accepted_offers_total = accepted_offers_list.count()

        open_offers_list = Offer.objects.filter(
            offered_by=profile,
            status=Offer.STATUS_OPEN
        ).prefetch_related("images").order_by("-created_at")

        open_offers_total = open_offers_list.count()
        open_offers_paginator = Paginator(open_offers_list, 9)
        open_offers_page_number = request.GET.get("open_offers_page")
        open_offers = open_offers_paginator.get_page(open_offers_page_number)

        completed_requests_list = Request.objects.filter(
            claimed_by=profile,
            status=Request.STATUS_FULFILLED
        ).exclude(
            requester=profile
        ).order_by("-claimed_at", "-created_at")

        completed_requests_total = completed_requests_list.count()

        completed_requests_paginator = Paginator(completed_requests_list, 9)
        completed_requests_page_number = request.GET.get("completed_page")
        completed_requests = completed_requests_paginator.get_page(completed_requests_page_number)

        fulfilled_requests_count = completed_requests_total

        return render(request, "volunteer_dash.html", {
            "active_tab": active_tab,
            "accepted_requests": accepted_requests,
            "accepted_requests_total": accepted_requests_total,
            "accepted_offers": accepted_offers,
            "accepted_offers_total": accepted_offers_total,
            "open_offers_total": open_offers_total,
            "open_offers": open_offers,
            "offers_view": offers_view,
            "completed_requests": completed_requests,
            "completed_requests_total": completed_requests_total,
            "available_requests": available_requests,
            "available_requests_total": available_requests_total,
            "fulfilled_requests_count": fulfilled_requests_count,
        })

    return redirect("home")

# Unhoused dashboard view.
#
# Displays:
# - Open requests
# - Processing (claimed) requests
# - Completed requests
#
# Requests are separated by status for better UX.


@login_required
def unhoused(request):
    role = getattr(request.user.profile, "role", None)
    if role and role.name == "unhoused":
        profile = request.user.profile

        open_requests = Request.objects.filter(
            requester=profile,
            status=Request.STATUS_OPEN
        ).order_by("-created_at")

        processing_requests = Request.objects.filter(
            requester=profile,
            status=Request.STATUS_CLAIMED
        ).order_by("-claimed_at", "-created_at")

        completed_requests = Request.objects.filter(
            requester=profile,
            status=Request.STATUS_FULFILLED
        ).order_by("-created_at")

        return render(request, "unhoused_dash.html", {
            "open_requests": open_requests,
            "processing_requests": processing_requests,
            "completed_requests": completed_requests,
        })

    return redirect("home")


# Returns correct dashboard route based on user role.
# Used for centralized redirection logic.

def get_dashboard_url(user):
    try:
        profile = user.profile
    except Profile.DoesNotExist:
        return "home"

    role = user.profile.role.name.lower() if user.profile.role else None

    if role == "admin":
        return "admin_dashboard"
    if role == "volunteer":
        return "volunteer"
    elif role == "unhoused":
        return "unhoused"

    return "home"


@login_required
def dashboard_redirect(request):
    if not request.user.is_authenticated:
        return redirect("login")

    role = request.user.profile.role.name

    if role == "admin":
        return redirect("admin_dashboard")
    elif role == "volunteer":
        return redirect("volunteer")
    elif role == "unhoused":
        return redirect("unhoused")

    return redirect("home")

@login_required
def history_view(request):
    profile = request.user.profile

    # Completed Requests (both roles)
    completed_requests = Request.objects.filter(
        status=Request.STATUS_FULFILLED
    ).filter(
        Q(requester=profile) | Q(claimed_by=profile)
    ).order_by("-updated_at")

    # Completed Offers (both roles)
    completed_offers = Offer.objects.filter(
        status=Offer.STATUS_FULFILLED
    ).filter(
        Q(offered_by=profile) | Q(claimed_by=profile)
    ).prefetch_related("images").order_by("-updated_at")

    return render(request, "history.html", {
        "completed_requests": completed_requests,
        "completed_offers": completed_offers,
    })


@login_required
def delete_account(request):
    if request.method != "POST":
        return redirect("settings")

    form = DeleteAccountForm(request.POST, user=request.user)

    if not form.is_valid():
        context = build_settings_context(
            request,
            delete_form=form,
            active_tab="delete-tab",
        )
        return render(request, "settings.html", context)

    request.user.delete()
    messages.success(request, "Your account has been deleted.")
    return redirect("home")


@login_required
def update_email(request):
    if request.method != "POST":
        return redirect("settings")

    form = EmailChangeForm(request.POST, user=request.user)

    if not form.is_valid():
        context = build_settings_context(
            request,
            email_form=form,
            active_tab="security-tab",
        )
        return render(request, "settings.html", context)

    new_email = form.cleaned_data["email"].strip().lower()

    # Prevent same email
    if new_email == request.user.email.lower():
        messages.error(request, "That is already your current email.")
        return redirect(f"{reverse('settings')}?tab=security-tab")

    # Prevent duplicate email
    if User.objects.filter(email__iexact=new_email).exclude(pk=request.user.pk).exists():
        messages.error(request, "That email is already in use.")
        return redirect(f"{reverse('settings')}?tab=security-tab")

    # Generate verification code
    code = generate_verification_code()

    EmailVerificationCode.objects.create(
        user=request.user,
        code=code,
        expires_at=timezone.now() + timedelta(minutes=10)
    )

    send_verification_email(request.user, code, override_email=new_email)

    # Store pending email in session
    request.session["pending_new_email"] = new_email

    messages.info(request, f"A verification code was sent to {new_email}.")
    return redirect("verify_email_change")


@login_required
def resend_email_change_code(request):
    pending_email = request.session.get("pending_new_email")

    if not pending_email:
        messages.error(request, "No email change request found.")
        return redirect("settings")

    # 30-second cooldown
    last_sent = request.session.get("last_email_change_verification_sent")

    if last_sent:
        last_sent_time = timezone.datetime.fromisoformat(last_sent)

        if timezone.now() < last_sent_time + timedelta(seconds=30):
            remaining = int(
                (last_sent_time + timedelta(seconds=30) - timezone.now()).total_seconds()
            )
            messages.error(request, f"Please wait {remaining}s before requesting another code.")
            return redirect("verify_email_change")

    # mark previous unverified codes for this user as used
    EmailVerificationCode.objects.filter(
        user=request.user,
        verified=False
    ).update(verified=True)

    code = generate_verification_code()

    EmailVerificationCode.objects.create(
        user=request.user,
        code=code,
        expires_at=timezone.now() + timedelta(minutes=10)
    )

    send_verification_email(request.user, code, override_email=pending_email)

    request.session["last_email_change_verification_sent"] = timezone.now().isoformat()

    messages.success(request, "A new verification code was sent to your new email.")
    return redirect("verify_email_change")

# Handles role switching between "volunteer" and "unhoused".
#
# IMPORTANT:
# - Prevents switching if user has active items:
#   - Volunteers → cannot switch if they have active offers
#   - Unhoused → cannot switch if they have active requests
#

@login_required
def update_role(request):
    if request.method != "POST":
        return redirect("settings")

    form = RoleChangeForm(
        request.POST,
        allowed_roles=["unhoused", "volunteer"]
    )

    if not form.is_valid():
        context = build_settings_context(
            request,
            role_form=form,
            active_tab="security-tab",
        )
        return render(request, "settings.html", context)

    profile = Profile.objects.get(user=request.user)
    current_role = profile.role.name.lower() if profile.role else None
    selected_role = form.cleaned_data["role"]

    if current_role == selected_role:
        messages.info(request, "You are already using that role.")
        return redirect(f"{reverse('settings')}?tab=security-tab")

    # Block volunteer -> unhoused only if volunteer still has active offers
    if current_role == "volunteer" and selected_role == "unhoused":
        active_offers = Offer.objects.filter(
            offered_by=profile,
            status__in=[Offer.STATUS_OPEN, Offer.STATUS_CLAIMED]
        )

        if active_offers.exists():
            messages.error(
                request,
                "You cannot switch to Unhoused while you still have active offers. "
                "Please remove, cancel, or complete them first."
            )
            return redirect(f"{reverse('settings')}?tab=security-tab")

    # Block unhoused -> volunteer only if unhoused still has active requests
    if current_role == "unhoused" and selected_role == "volunteer":
        active_requests = Request.objects.filter(
            requester=profile,
            status__in=[Request.STATUS_OPEN, Request.STATUS_CLAIMED]
        )

        if active_requests.exists():
            messages.error(
                request,
                "You cannot switch to Volunteer while you still have active requests. "
                "Please remove, cancel, or complete them first."
            )
            return redirect(f"{reverse('settings')}?tab=security-tab")

    profile.role = Role.objects.get(name=selected_role)
    profile.save()

    messages.success(request, "Role updated.")
    return redirect(f"{reverse('settings')}?tab=security-tab")

@login_required
@require_POST
def admin_update_account(request, profile_id):
    if not is_admin(request.user):
        messages.error(request, "Only admins can update accounts.")
        return redirect("home")

    profile = get_object_or_404(Profile.objects.select_related("user", "role"), id=profile_id)
    form = AdminAccountEditForm(request.POST, profile=profile)

    if not form.is_valid():
        for field, errors in form.errors.items():
            for error in errors:
                if field == "__all__":
                    messages.error(request, error)
                else:
                    label = form.fields[field].label or field.replace("_", " ").title()
                    messages.error(request, f"{label}: {error}")
        return redirect("admin_dashboard")

    selected_role = form.cleaned_data["role"]

    if profile.user == request.user and selected_role != "admin":
        messages.error(request, "You cannot remove your own admin role.")
        return redirect("admin_dashboard")

    profile.user.first_name = form.cleaned_data.get("first_name", "").strip()
    profile.user.last_name = form.cleaned_data.get("last_name", "").strip()
    profile.user.email = form.cleaned_data["email"]
    profile.user.username = form.cleaned_data["email"]
    profile.user.save()

    profile.display_username = form.cleaned_data["display_username"].strip()
    profile.phone_number = form.cleaned_data.get("phone_number", "")
    profile.city = form.cleaned_data.get("city", "").strip()
    profile.state = form.cleaned_data.get("state", "").strip()
    profile.role = Role.objects.get(name=selected_role)
    profile.save()

    messages.success(request, "Account updated successfully.")
    return redirect("admin_dashboard")


@login_required
@require_POST
def admin_delete_account(request, profile_id):
    if not is_admin(request.user):
        messages.error(request, "Only admins can delete accounts.")
        return redirect("home")

    profile = get_object_or_404(Profile.objects.select_related("user", "role"), id=profile_id)

    if profile.user == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect("admin_dashboard")

    if profile.role and profile.role.name.lower() == "admin":
        messages.error(request, "You cannot delete another admin account.")
        return redirect("admin_dashboard")

    profile.user.delete()
    messages.success(request, "Account deleted successfully.")
    return redirect("admin_dashboard")

# Allows unhoused users to create new requests.
# Sets request status to OPEN by default.

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
            return redirect("unhoused")
    else:
        form = RequestForm()

    return render(request, "create_request.html", {
        "form": form,
    })

# Updates an existing request.
#
# Special behavior:
# - If request was already claimed → resets it back to OPEN
# - Clears claimed_by and claimed_at
# - Notifies user that volunteer will be affected

@login_required
@require_POST
def update_request(request, request_id):
    profile = request.user.profile

    if profile.role is None or profile.role.name.lower() != "unhoused":
        messages.error(request, "Only unhoused users can update requests.")
        return redirect("home")

    req = get_object_or_404(Request, id=request_id, requester=profile)
    form = RequestForm(request.POST, instance=req)

    if not form.is_valid():
        messages.error(request, "Please check your request form and try again.")
        return redirect("unhoused")

    updated_request = form.save(commit=False)

    previous_claimer = req.claimed_by
    was_claimed = req.status == Request.STATUS_CLAIMED

    if was_claimed:
        updated_request.status = Request.STATUS_OPEN
        updated_request.claimed_by = None
        updated_request.claimed_at = None

    updated_request.requester = profile
    updated_request.save()

    if was_claimed and previous_claimer and previous_claimer.user != request.user:
        requester_name = (
                profile.display_username
                or request.user.get_full_name().strip()
                or request.user.username
        )

        send_system_dm(
            sender=request.user,
            recipient=previous_claimer.user,
            body=(
                f'{requester_name} updated the request "{updated_request.title}". '
                f'The request has been reopened, so you are no longer assigned to it.'
            ),
        )

        messages.success(
            request,
            "Your request was updated. The volunteer was notified, and your request is open again."
        )
    else:
        messages.success(request, "Your request was updated successfully.")

    updated_request.requester = profile
    updated_request.save()

    return redirect("unhoused")

# Deletes a request.
#
# If request was already claimed:
# - Notifies that volunteer will be affected not yet completely implemented

@login_required
@require_POST
def delete_request(request, request_id):
    profile = request.user.profile

    if profile.role is None or profile.role.name.lower() != "unhoused":
        messages.error(request, "Only unhoused users can delete requests.")
        return redirect("home")

    req = get_object_or_404(Request, id=request_id, requester=profile)
    was_processing = req.status == Request.STATUS_CLAIMED
    previous_claimer = req.claimed_by
    request_title = req.title

    req.delete()

    if was_processing and previous_claimer and previous_claimer.user != request.user:
        requester_name = (
                profile.display_username
                or request.user.get_full_name().strip()
                or request.user.username
        )

        send_system_dm(
            sender=request.user,
            recipient=previous_claimer.user,
            body=(
                f'{requester_name} deleted the request "{request_title}". '
                f'It is no longer needed.'
            ),
        )

        messages.success(
            request,
            "Your request was deleted. The volunteer was notified that it is no longer needed."
        )
    else:
        messages.success(request, "Your request was deleted successfully.")

    return redirect("unhoused")


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

    category = request.GET.get("category", "").strip()
    city = request.GET.get("city", "").strip()

    requests_qs = Request.objects.filter(status=Request.STATUS_OPEN)

    if category:
        requests_qs = requests_qs.filter(category=category)
    if city:
        requests_qs = requests_qs.filter(city__icontains=city)

    paginator = Paginator(requests_qs, 9)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "volunteer_requests.html", {
        "requests": page_obj,
        "categories": Request.CATEGORY_CHOICES,
        "selected_category": category,
        "selected_city": city,
    })

# Allows volunteers to claim a request.
# Updates status and tracks claimer + timestamp.

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
    req.claimed_at = timezone.now()
    req.save()

    messages.success(request, "You have claimed this request.")
    return redirect("volunteer_requests")

@login_required
@require_POST
def withdraw_claimed_request(request, request_id):
    profile = request.user.profile

    if profile.role is None or profile.role.name.lower() != "volunteer":
        messages.error(request, "Only volunteers can remove themselves from accepted requests.")
        return redirect("home")

    req = get_object_or_404(Request, id=request_id, claimed_by=profile)

    if req.status != Request.STATUS_CLAIMED:
        messages.error(request, "Only accepted requests can be removed from your dashboard.")
        return redirect("volunteer")

    requester_profile = req.requester
    request_title = req.title

    req.status = Request.STATUS_OPEN
    req.claimed_by = None
    req.claimed_at = None
    req.save()

    if requester_profile and requester_profile.user != request.user:
        volunteer_name = (
                profile.display_username
                or request.user.get_full_name().strip()
                or request.user.username
        )

        send_system_dm(
            sender=request.user,
            recipient=requester_profile.user,
            body=(
                f'{volunteer_name} removed themselves from the request "{request_title}". '
                f'The request has reopened so another volunteer can respond.'
            ),
        )

    messages.success(
        request,
        "You removed yourself from the request. The unhoused user was notified and the request is open again."
    )
    return redirect("volunteer")

# Allows volunteers to create offers.
#
# Supports:
# - Multiple image uploads
# - Assigning images via OfferImage model

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
        form = OfferForm(request.POST, request.FILES)
        files = request.FILES.getlist("offer_images")

        if form.is_valid():
            offer = form.save(commit=False)
            offer.offered_by = profile
            offer.status = Offer.STATUS_OPEN
            offer.save()

            for file in files:
                OfferImage.objects.create(
                    offer=offer,
                    image=file
                )

            messages.success(request, "Your offer was submitted successfully.")
            return redirect("create_offer")

        for field, errors in form.errors.items():
            for error in errors:
                if field == "__all__":
                    messages.error(request, error)
                else:
                    label = form.fields[field].label or field.replace("_", " ").title()
                    messages.error(request, f"{label}: {error}")

    else:
        form = OfferForm()

    return render(request, "create_offer.html", {"form": form})

# Displays all OPEN offers for unhoused users.
# Uses pagination (18 per page).

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

    offers_list = Offer.objects.filter(
        status=Offer.STATUS_OPEN
    ).prefetch_related("images")

    paginator = Paginator(offers_list, 18)   # show 6 offers per page
    page_number = request.GET.get("page")
    offers = paginator.get_page(page_number)

    return render(request, "available_offers.html", {
        "offers": offers
    })

# Allows unhoused users to claim an offer.
# Changes status to CLAIMED and stores who claimed it.

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
    offer.claimed_at = timezone.now()
    offer.save()

    messages.success(request, "You have claimed this offer.")
    return redirect("available_offers")

# Displays all offers created by the logged-in volunteer.
# Includes pagination and image prefetching.

@login_required
def my_offers(request):
    profile = request.user.profile

    if profile.role is None or profile.role.name.lower() != "volunteer":
        messages.error(request, "Only volunteers can view their offers.")
        return redirect("home")

    offers_list = Offer.objects.filter(
        offered_by=profile
    ).prefetch_related("images")

    paginator = Paginator(offers_list, 18)   # show 18 offers per page
    page_number = request.GET.get("page")
    offers = paginator.get_page(page_number)

    return render(request, "my_offers.html", {
        "offers": offers
    })

# Allows users to report an offer.
# Prevents self-reporting.
# Stores reason and optional details.

@login_required
@require_POST
def create_offer_report(request):
    try:
        reporter_profile = request.user.profile
    except Profile.DoesNotExist:
        messages.error(request, "You must have a profile to submit a report.")
        return redirect("home")

    offer_id = request.POST.get("offer_id")
    reported_user_id = request.POST.get("reported_user_id")
    reason = (request.POST.get("reason") or "").strip()
    details = (request.POST.get("details") or "").strip()
    return_to = (request.POST.get("return_to") or "").strip()

    if not offer_id or not reported_user_id or not reason:
        messages.error(request, "Please complete the report form.")
        return redirect(return_to or "available_offers")

    offer = get_object_or_404(Offer, pk=offer_id)
    reported_user = get_object_or_404(Profile, user__id=reported_user_id)

    if reported_user.user == request.user:
        messages.error(request, "You cannot report yourself.")
        return redirect(return_to or "available_offers")

    OfferReport.objects.create(
        reporter=reporter_profile,
        reported_user=reported_user,
        offer=offer,
        reason=reason,
        details=details,
    )

    messages.success(request, "Your report was submitted successfully.")
    return redirect(return_to or "available_offers")

# Allows users to report a request.
# Validates reason against predefined choices.
# Prevents self-reporting.

@login_required
@require_POST
def create_request_report(request):
    try:
        reporter_profile = request.user.profile
    except Profile.DoesNotExist:
        messages.error(request, "You must have a profile to submit a report.")
        return redirect("home")

    request_id = request.POST.get("request_id")
    reported_user_id = request.POST.get("reported_user_id")
    reason = (request.POST.get("reason") or "").strip()
    details = (request.POST.get("details") or "").strip()
    return_to = (request.POST.get("return_to") or "").strip()

    valid_reasons = {choice[0] for choice in RequestReport.REASON_CHOICES}

    if not request_id or not reported_user_id or not reason:
        messages.error(request, "Please complete the report form.")
        return redirect(return_to or "volunteer_requests")

    if reason not in valid_reasons:
        messages.error(request, "Please choose a valid report reason.")
        return redirect(return_to or "volunteer_requests")

    request_item = get_object_or_404(Request, pk=request_id)
    reported_user = get_object_or_404(Profile, user__id=reported_user_id)

    if reported_user.user == request.user:
        messages.error(request, "You cannot report yourself.")
        return redirect(return_to or "volunteer_requests")

    RequestReport.objects.create(
        reporter=reporter_profile,
        reported_user=reported_user,
        request_item=request_item,
        reason=reason,
        details=details,
    )

    messages.success(request, "Your report was submitted successfully.")
    return redirect(return_to or "volunteer_requests")


@login_required
@require_POST
def update_offer(request, offer_id):
    profile = request.user.profile
    page_number = request.POST.get("return_page_number", "1")

    if profile.role is None or profile.role.name.lower() != "volunteer":
        messages.error(request, "Unauthorized.")
        return redirect("my_offers")

    offer = get_object_or_404(Offer, id=offer_id, offered_by=profile)

    # BLOCK EDIT IF CLAIMED
    if offer.status == Offer.STATUS_CLAIMED:
        messages.error(request, "This offer has already been claimed and cannot be edited.")
        return redirect(f"{reverse('my_offers')}?page={page_number}")

    form = OfferForm(request.POST, instance=offer)

    if form.is_valid():
        updated_offer = form.save(commit=False)
        updated_offer.offered_by = profile
        updated_offer.save()

        messages.success(request, "Offer updated successfully.")

    else:
        messages.error(request, "Failed to update offer. Please check your form.")

    # always redirect back to my_offers
    return redirect(f"{reverse('my_offers')}?page={page_number}")


@login_required
@require_POST
def delete_offer(request, offer_id):
    profile = request.user.profile
    page_number = request.POST.get("return_page_number", "1")

    if profile.role is None or profile.role.name.lower() != "volunteer":
        messages.error(request, "Only volunteers can delete offers.")
        return redirect("home")

    offer = get_object_or_404(Offer, id=offer_id, offered_by=profile)
    was_claimed = offer.status == Offer.STATUS_CLAIMED
    previous_claimer = offer.claimed_by
    offer_title = offer.title

    offer.delete()

    if was_claimed and previous_claimer and previous_claimer.user != request.user:
        volunteer_name = (
                profile.display_username
                or request.user.get_full_name().strip()
                or request.user.username
        )

        send_system_dm(
            sender=request.user,
            recipient=previous_claimer.user,
            body=(
                f'{volunteer_name} deleted the offer "{offer_title}". '
                f'It is no longer available.'
            ),
        )

        messages.success(
            request,
            "Your offer was deleted. The unhoused user was notified that it is no longer available."
        )
    else:
        messages.success(request, "Offer deleted successfully.")

    return redirect(f"{reverse('my_offers')}?page={page_number}")


@login_required
@require_POST
def verify_request(request, request_id):
    profile = request.user.profile

    if profile.role is None or profile.role.name.lower() != "unhoused":
        messages.error(request, "Only unhoused users can verify requests.")
        return redirect("home")

    req = get_object_or_404(Request, id=request_id, requester=profile)

    if req.status != Request.STATUS_CLAIMED:
        messages.error(request, "Only processing requests can be marked as fulfilled.")
        return redirect("unhoused")

    previous_claimer = req.claimed_by
    request_title = req.title

    req.status = Request.STATUS_FULFILLED
    req.save()

    if previous_claimer and previous_claimer.user != request.user:
        requester_name = (
                profile.display_username
                or request.user.get_full_name().strip()
                or request.user.username
        )

        send_system_dm(
            sender=request.user,
            recipient=previous_claimer.user,
            body=(
                f'{requester_name} marked the request "{request_title}" as fulfilled. '
                f'Thank you for helping {requester_name}!'
            ),
        )

        messages.success(request, "Request marked as fulfilled. The volunteer was notified.")
    else:
        messages.success(request, "Request marked as fulfilled.")

    return redirect("unhoused")



@login_required
@require_POST
def verify_offer(request, offer_id):
    profile = request.user.profile

    if profile.role is None or profile.role.name.lower() != "volunteer":
        messages.error(request, "Only volunteers can mark offers as fulfilled.")
        return redirect("home")

    offer = get_object_or_404(Offer, id=offer_id, offered_by=profile)

    if offer.status != Offer.STATUS_CLAIMED:
        messages.error(request, "Only claimed offers can be marked as fulfilled.")
        return redirect("volunteer")

    previous_claimer = offer.claimed_by
    offer_title = offer.title

    offer.status = Offer.STATUS_FULFILLED
    offer.save()

    if previous_claimer and previous_claimer.user != request.user:
        volunteer_name = (
                profile.display_username
                or request.user.get_full_name().strip()
                or request.user.username
        )

        send_system_dm(
            sender=request.user,
            recipient=previous_claimer.user,
            body=(
                f'{volunteer_name} marked the offer "{offer_title}" as fulfilled. '
                f'Thank you for confirming receipt.'
            ),
        )

        messages.success(request, "Offer marked as fulfilled. The unhoused user was notified.")
    else:
        messages.success(request, "Offer marked as fulfilled.")

    return redirect("volunteer")


def is_admin(user):
    try:
        return bool(user.profile.role and user.profile.role.name.lower() == "admin")
    except Profile.DoesNotExist:
        return False


@login_required
def admin_dashboard(request):
    if not is_admin(request.user):
        messages.error(request, "Only admins can view that page.")
        return redirect("home")

    query = request.GET.get("q", "").strip()

    profiles = Profile.objects.select_related("user", "role").order_by("user__email")

    if query:
        profiles = profiles.filter(
            Q(user__username__icontains=query) |
            Q(user__email__icontains=query) |
            Q(display_username__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query)
        )

    suggestions = (
        Profile.objects.select_related("user")
        .exclude(user__email__isnull=True)
        .exclude(user__email__exact="")
        .order_by("user__email")
        .values_list("user__email", flat=True)
        .distinct()
    )

    return render(request, "admin_dash.html", {
        "profiles": profiles,
        "query": query,
        "suggestions": suggestions,
    })
